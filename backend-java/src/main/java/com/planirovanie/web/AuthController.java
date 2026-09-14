package com.planirovanie.web;

import com.planirovanie.entity.AppUser;
import com.planirovanie.entity.UserSession;
import com.planirovanie.service.AuthService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.Optional;

/** Login / logout / current user, plus ADMIN-only user & role management. */
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService auth;

    public AuthController(AuthService auth) {
        this.auth = auth;
    }

    public record LoginReq(String username, String password) {}
    public record UserReq(String username, String password, String role, String displayName, Boolean active) {}

    private Map<String, Object> userView(AppUser u) {
        return Map.of("username", u.username, "role", u.role,
                "name", u.displayName == null ? u.username : u.displayName, "active", u.active);
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginReq req) {
        Optional<UserSession> s = auth.login(req == null ? null : req.username(), req == null ? null : req.password());
        if (s.isEmpty()) return ResponseEntity.status(401).body(Map.of("error", "invalid_credentials"));
        UserSession sess = s.get();
        String name = auth.findUser(sess.username).map(u -> u.displayName == null ? u.username : u.displayName)
                .orElse(sess.username);
        return ResponseEntity.ok(Map.of("token", sess.token, "username", sess.username, "role", sess.role, "name", name));
    }

    @PostMapping("/logout")
    public ResponseEntity<Void> logout(HttpServletRequest req) {
        Object s = req.getAttribute("session");
        if (s instanceof UserSession us) auth.logout(us.token);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/me")
    public ResponseEntity<?> me(HttpServletRequest req) {
        Object s = req.getAttribute("session");
        if (!(s instanceof UserSession us)) return ResponseEntity.status(401).body(Map.of("error", "unauthorized"));
        String name = auth.findUser(us.username).map(u -> u.displayName == null ? u.username : u.displayName)
                .orElse(us.username);
        return ResponseEntity.ok(Map.of("username", us.username, "role", us.role, "name", name));
    }

    // ---- ADMIN user management (interceptor enforces ADMIN on /api/auth/users**) ----

    @GetMapping("/users")
    public List<Map<String, Object>> list() {
        return auth.listUsers().stream().map(this::userView).toList();
    }

    @PostMapping("/users")
    public ResponseEntity<?> create(@RequestBody UserReq req) {
        if (req == null || req.username() == null || req.username().isBlank()
                || req.password() == null || req.password().isBlank())
            return ResponseEntity.badRequest().body(Map.of("error", "username_and_password_required"));
        if (auth.findUser(req.username().trim()).isPresent())
            return ResponseEntity.status(409).body(Map.of("error", "user_exists"));
        AppUser u = auth.create(req.username(), req.password(), req.role(), req.displayName());
        return ResponseEntity.ok(userView(u));
    }

    @PutMapping("/users/{username}")
    public ResponseEntity<?> update(@PathVariable String username, @RequestBody UserReq req) {
        boolean demoting = req != null && ((req.role() != null && !"ADMIN".equalsIgnoreCase(req.role()))
                || Boolean.FALSE.equals(req.active()));
        if (demoting && auth.isLastAdmin(username))
            return ResponseEntity.status(409).body(Map.of("error", "last_admin"));
        boolean ok = auth.updateUser(username,
                req == null ? null : req.role(),
                req == null ? null : req.password(),
                req == null ? null : req.active(),
                req == null ? null : req.displayName());
        return ok ? ResponseEntity.ok(Map.of("ok", true))
                : ResponseEntity.status(404).body(Map.of("error", "not_found"));
    }

    @DeleteMapping("/users/{username}")
    public ResponseEntity<?> delete(@PathVariable String username) {
        if (auth.isLastAdmin(username))
            return ResponseEntity.status(409).body(Map.of("error", "last_admin"));
        boolean ok = auth.deleteUser(username);
        return ok ? ResponseEntity.noContent().build()
                : ResponseEntity.status(404).body(Map.of("error", "not_found"));
    }
}
