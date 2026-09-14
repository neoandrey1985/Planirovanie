package com.planirovanie.service;

import com.planirovanie.entity.AppUser;
import com.planirovanie.entity.UserSession;
import com.planirovanie.repo.AppUserRepo;
import com.planirovanie.repo.UserSessionRepo;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.security.SecureRandom;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Base64;
import java.util.List;
import java.util.Optional;
import java.util.Set;

/**
 * Server-side authentication and role management.
 * Roles live in {@code app_users.role}; opaque bearer tokens live in {@code app_sessions}.
 */
@Service
public class AuthService {

    public static final Set<String> ROLES = Set.of("VIEWER", "EDITOR", "ADMIN");

    private final AppUserRepo users;
    private final UserSessionRepo sessions;
    private final PasswordHasher hasher;
    private final SecureRandom rng = new SecureRandom();

    @Value("${app.auth.session-hours:12}")
    private long sessionHours;

    /** Whether to create default demo users on first startup (disable in real deployments). */
    @Value("${app.auth.seed-defaults:true}")
    private boolean seedDefaults;

    public AuthService(AppUserRepo users, UserSessionRepo sessions, PasswordHasher hasher) {
        this.users = users; this.sessions = sessions; this.hasher = hasher;
    }

    /** Seed three demo accounts (admin/editor/viewer) once, so a fresh install is usable. */
    @PostConstruct
    @Transactional
    public void seed() {
        if (!seedDefaults || users.count() > 0) return;
        create("admin", "admin123", "ADMIN", "Администратор");
        create("editor", "editor123", "EDITOR", "Редактор");
        create("viewer", "viewer123", "VIEWER", "Наблюдатель");
    }

    // ---- user management (ADMIN) ----

    @Transactional
    public AppUser create(String username, String password, String role, String displayName) {
        String r = normalizeRole(role);
        AppUser u = new AppUser();
        u.username = username.trim();
        u.passHash = hasher.hash(password);
        u.role = r;
        u.displayName = (displayName == null || displayName.isBlank()) ? username : displayName;
        u.active = true;
        u.createdAt = Instant.now();
        return users.save(u);
    }

    public List<AppUser> listUsers() {
        return users.findAllByOrderByUsernameAsc();
    }

    @Transactional
    public boolean updateUser(String username, String role, String password, Boolean active, String displayName) {
        Optional<AppUser> o = users.findByUsername(username);
        if (o.isEmpty()) return false;
        AppUser u = o.get();
        if (role != null && !role.isBlank()) u.role = normalizeRole(role);
        if (password != null && !password.isBlank()) {
            u.passHash = hasher.hash(password);
            sessions.deleteByUsername(username);   // force re-login after a password change
        }
        if (active != null) {
            u.active = active;
            if (!active) sessions.deleteByUsername(username);
        }
        if (displayName != null && !displayName.isBlank()) u.displayName = displayName;
        users.save(u);
        return true;
    }

    @Transactional
    public boolean deleteUser(String username) {
        Optional<AppUser> o = users.findByUsername(username);
        if (o.isEmpty()) return false;
        sessions.deleteByUsername(username);
        users.delete(o.get());
        return true;
    }

    public boolean isLastAdmin(String username) {
        Optional<AppUser> o = users.findByUsername(username);
        if (o.isEmpty() || !"ADMIN".equals(o.get().role)) return false;
        long admins = users.findAll().stream().filter(u -> "ADMIN".equals(u.role) && u.active).count();
        return admins <= 1;
    }

    // ---- authentication ----

    @Transactional
    public Optional<UserSession> login(String username, String password) {
        if (username == null || password == null) return Optional.empty();
        Optional<AppUser> o = users.findByUsername(username.trim());
        if (o.isEmpty()) return Optional.empty();
        AppUser u = o.get();
        if (!u.active || !hasher.verify(password, u.passHash)) return Optional.empty();
        UserSession s = new UserSession();
        s.token = newToken();
        s.username = u.username;
        s.role = u.role;
        s.createdAt = Instant.now();
        s.expiresAt = s.createdAt.plus(sessionHours, ChronoUnit.HOURS);
        return Optional.of(sessions.save(s));
    }

    /** Resolve a bearer token to a live session, or empty if missing/expired. */
    @Transactional
    public Optional<UserSession> resolve(String token) {
        if (token == null || token.isBlank()) return Optional.empty();
        Optional<UserSession> o = sessions.findById(token.trim());
        if (o.isEmpty()) return Optional.empty();
        UserSession s = o.get();
        if (s.expiresAt != null && s.expiresAt.isBefore(Instant.now())) {
            sessions.deleteById(token);
            return Optional.empty();
        }
        return o;
    }

    @Transactional
    public void logout(String token) {
        if (token != null && !token.isBlank()) sessions.deleteById(token.trim());
    }

    @Transactional
    public int purgeExpired() {
        return sessions.deleteExpired(Instant.now());
    }

    public Optional<AppUser> findUser(String username) {
        return users.findByUsername(username);
    }

    private String newToken() {
        byte[] b = new byte[32];
        rng.nextBytes(b);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(b);
    }

    private static String normalizeRole(String role) {
        String r = role == null ? "VIEWER" : role.trim().toUpperCase();
        return ROLES.contains(r) ? r : "VIEWER";
    }
}
