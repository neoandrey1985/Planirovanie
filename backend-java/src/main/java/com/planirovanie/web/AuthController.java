package com.planirovanie.web;

import com.planirovanie.entity.AppUser;
import com.planirovanie.entity.UserSession;
import com.planirovanie.service.AuditService;
import com.planirovanie.service.AuthService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/** Login / logout / current user, plus ADMIN-only user & role management. */
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService auth;
    private final AuditService audit;

    public AuthController(AuthService auth, AuditService audit) {
        this.auth = auth;
        this.audit = audit;
    }

    private void audit(String action, String user, String role, HttpServletRequest req, String detail) {
        audit.log("AUTH", action, user, role, req.getMethod(), req.getRequestURI(), null, null,
                req.getRemoteAddr(), req.getHeader("User-Agent"), detail);
    }

    public record LoginReq(String username, String password) {}
    public record UserReq(String username, String password, String role, String displayName, Boolean active) {}
    public record MeReq(String member) {}
    public record PasswordReq(String oldPassword, String newPassword) {}

    private Map<String, Object> userView(AppUser u) {
        return Map.of("username", u.username, "role", u.role,
                "name", u.displayName == null ? u.username : u.displayName, "active", u.active);
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginReq req, HttpServletRequest http) {
        String attempted = req == null ? null : req.username();
        String key = (attempted == null ? "?" : attempted.trim().toLowerCase()) + "|" + http.getRemoteAddr();
        // Brute-force lockout: reject early after too many recent failures.
        if (auth.isLocked(key)) {
            audit("login_locked", attempted, null, http, "Вход временно заблокирован (много неудачных попыток)");
            return ResponseEntity.status(429)
                    .header("Retry-After", String.valueOf(auth.lockoutSeconds()))
                    .body(Map.of("error", "too_many_attempts"));
        }
        Optional<UserSession> s = auth.login(attempted, req == null ? null : req.password());
        auth.noteLogin(key, s.isPresent());
        if (s.isEmpty()) {
            audit("login_failed", attempted, null, http, "Неудачная попытка входа");
            return ResponseEntity.status(401).body(Map.of("error", "invalid_credentials"));
        }
        UserSession sess = s.get();
        String name = auth.findUser(sess.username).map(u -> u.displayName == null ? u.username : u.displayName)
                .orElse(sess.username);
        audit("login", sess.username, sess.role, http, "Вход выполнен");
        Map<String, Object> body = new LinkedHashMap<>(Map.of("token", sess.token, "username", sess.username, "role", sess.role, "name", name));
        body.put("member", auth.findUser(sess.username).map(u -> u.memberName).orElse(null));
        return ResponseEntity.ok(body);
    }

    @PostMapping("/logout")
    public ResponseEntity<Void> logout(HttpServletRequest req) {
        Object s = req.getAttribute("session");
        if (s instanceof UserSession us) { auth.logout(us.token); audit("logout", us.username, us.role, req, null); }
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/me")
    public ResponseEntity<?> me(HttpServletRequest req) {
        Object s = req.getAttribute("session");
        if (!(s instanceof UserSession us)) return ResponseEntity.status(401).body(Map.of("error", "unauthorized"));
        return ResponseEntity.ok(meView(us));
    }

    private Map<String, Object> meView(UserSession us) {
        Optional<AppUser> u = auth.findUser(us.username);
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("username", us.username);
        m.put("role", us.role);
        m.put("name", u.map(x -> x.displayName == null ? x.username : x.displayName).orElse(us.username));
        m.put("member", u.map(x -> x.memberName).orElse(null));
        return m;
    }

    // ---- «Мой профиль»: любой вошедший пользователь (в т.ч. VIEWER) меняет только свою учётную запись ----

    @PutMapping("/me")
    public ResponseEntity<?> updateMe(@RequestBody MeReq body, HttpServletRequest req) {
        Object s = req.getAttribute("session");
        if (!(s instanceof UserSession us)) return ResponseEntity.status(401).body(Map.of("error", "unauthorized"));
        if (!auth.setMember(us.username, body == null ? null : body.member()))
            return ResponseEntity.status(404).body(Map.of("error", "not_found"));
        audit("profile_updated", us.username, us.role, req, "Участник команды: " + (body == null || body.member() == null ? "—" : body.member()));
        return ResponseEntity.ok(meView(us));
    }

    @PutMapping("/me/password")
    public ResponseEntity<?> changePassword(@RequestBody PasswordReq body, HttpServletRequest req) {
        Object s = req.getAttribute("session");
        if (!(s instanceof UserSession us)) return ResponseEntity.status(401).body(Map.of("error", "unauthorized"));
        String key = us.username.toLowerCase() + "|pw|" + req.getRemoteAddr();
        if (auth.isLocked(key)) return ResponseEntity.status(429)
                .header("Retry-After", String.valueOf(auth.lockoutSeconds())).body(Map.of("error", "too_many_attempts"));
        String err = auth.changeOwnPassword(us.username, us.token,
                body == null ? null : body.oldPassword(), body == null ? null : body.newPassword());
        if ("wrong_password".equals(err)) auth.noteLogin(key, false);
        if (err == null) {
            auth.noteLogin(key, true);
            audit("password_changed", us.username, us.role, req, "Пользователь сменил свой пароль");
            return ResponseEntity.noContent().build();
        }
        int code = "wrong_password".equals(err) ? 403 : "not_found".equals(err) ? 404 : 400;
        Map<String, Object> out = new LinkedHashMap<>(Map.of("error", err));
        if ("weak_password".equals(err)) out.put("minLength", AuthService.MIN_PASSWORD);
        return ResponseEntity.status(code).body(out);
    }

    // ---- ADMIN user management (interceptor enforces ADMIN on /api/auth/users**) ----

    @GetMapping("/users")
    public List<Map<String, Object>> list() {
        return auth.listUsers().stream().map(this::userView).toList();
    }

    @PostMapping("/users")
    public ResponseEntity<?> create(@RequestBody UserReq req, HttpServletRequest http) {
        if (req == null || req.username() == null || req.username().isBlank()
                || req.password() == null || req.password().isBlank())
            return ResponseEntity.badRequest().body(Map.of("error", "username_and_password_required"));
        if (auth.findUser(req.username().trim()).isPresent())
            return ResponseEntity.status(409).body(Map.of("error", "user_exists"));
        AppUser u = auth.create(req.username(), req.password(), req.role(), req.displayName());
        audit("user_created", actor(http), actorRole(http), http, "Создан пользователь " + u.username + " (" + u.role + ")");
        return ResponseEntity.ok(userView(u));
    }

    @PutMapping("/users/{username}")
    public ResponseEntity<?> update(@PathVariable String username, @RequestBody UserReq req, HttpServletRequest http) {
        boolean demoting = req != null && ((req.role() != null && !"ADMIN".equalsIgnoreCase(req.role()))
                || Boolean.FALSE.equals(req.active()));
        if (demoting && auth.isLastAdmin(username))
            return ResponseEntity.status(409).body(Map.of("error", "last_admin"));
        boolean ok = auth.updateUser(username,
                req == null ? null : req.role(),
                req == null ? null : req.password(),
                req == null ? null : req.active(),
                req == null ? null : req.displayName());
        if (ok) audit("user_updated", actor(http), actorRole(http), http,
                "Изменён пользователь " + username + (req != null && req.role() != null ? ", роль=" + req.role() : "")
                        + (req != null && req.password() != null && !req.password().isBlank() ? ", смена пароля" : "")
                        + (req != null && req.active() != null ? ", активен=" + req.active() : ""));
        return ok ? ResponseEntity.ok(Map.of("ok", true))
                : ResponseEntity.status(404).body(Map.of("error", "not_found"));
    }

    @DeleteMapping("/users/{username}")
    public ResponseEntity<?> delete(@PathVariable String username, HttpServletRequest http) {
        if (auth.isLastAdmin(username))
            return ResponseEntity.status(409).body(Map.of("error", "last_admin"));
        boolean ok = auth.deleteUser(username);
        if (ok) audit("user_deleted", actor(http), actorRole(http), http, "Удалён пользователь " + username);
        return ok ? ResponseEntity.noContent().build()
                : ResponseEntity.status(404).body(Map.of("error", "not_found"));
    }

    private String actor(HttpServletRequest req) {
        Object s = req.getAttribute("session");
        return s instanceof UserSession us ? us.username : null;
    }
    private String actorRole(HttpServletRequest req) {
        Object s = req.getAttribute("session");
        return s instanceof UserSession us ? us.role : null;
    }
}
