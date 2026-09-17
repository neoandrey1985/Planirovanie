package com.planirovanie.service;

import com.planirovanie.entity.AppUser;
import com.planirovanie.entity.UserSession;
import com.planirovanie.repo.AppUserRepo;
import com.planirovanie.repo.UserSessionRepo;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.security.SecureRandom;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Base64;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Server-side authentication and role management.
 * Roles live in {@code app_users.role}; opaque bearer tokens live in {@code app_sessions}.
 */
@Service
public class AuthService {

    public static final Set<String> ROLES = Set.of("VIEWER", "EDITOR", "ADMIN");
    private static final Logger log = LoggerFactory.getLogger(AuthService.class);

    private final AppUserRepo users;
    private final UserSessionRepo sessions;
    private final PasswordHasher hasher;
    private final SecureRandom rng = new SecureRandom();
    /** In-memory login throttle: key (user|ip) -> [failCount, windowStartMs, lockUntilMs]. */
    private final Map<String, long[]> attempts = new ConcurrentHashMap<>();

    @Value("${app.auth.session-hours:12}")
    private long sessionHours;

    /** Seed the three weak demo accounts (admin/editor/viewer). Opt-in — off by default;
     *  intended only for local demos. Real installs get a single admin (see {@link #seed()}). */
    @Value("${app.auth.seed-defaults:false}")
    private boolean seedDefaults;

    /** Password for the bootstrap admin created on a fresh DB when demo seeding is off.
     *  If blank, a strong random password is generated and logged once. */
    @Value("${app.auth.admin-password:${APP_ADMIN_PASSWORD:}}")
    private String adminPassword;

    /** Login brute-force protection: lock a (user|ip) after N failures for M seconds. */
    @Value("${app.auth.max-attempts:8}")
    private int maxAttempts;
    @Value("${app.auth.lockout-seconds:300}")
    private long lockoutSeconds;

    public AuthService(AppUserRepo users, UserSessionRepo sessions, PasswordHasher hasher) {
        this.users = users; this.sessions = sessions; this.hasher = hasher;
    }

    /** Bootstrap accounts on a fresh database.
     *  - {@code seed-defaults=true}: create the three demo users with weak passwords (LOCAL DEMO ONLY);
     *  - otherwise: create a single {@code admin} whose password comes from {@code APP_ADMIN_PASSWORD},
     *    or a strong random password logged once when that is unset.
     *  Never runs if any user already exists. */
    @PostConstruct
    @Transactional
    public void seed() {
        if (users.count() > 0) return;
        if (seedDefaults) {
            create("admin", "admin123", "ADMIN", "Администратор");
            create("editor", "editor123", "EDITOR", "Редактор");
            create("viewer", "viewer123", "VIEWER", "Наблюдатель");
            log.warn("app.auth.seed-defaults=true — созданы демо-пользователи со СЛАБЫМИ паролями " +
                    "(admin/editor/viewer). Отключите (AUTH_SEED_DEFAULTS=false) для реальных развёртываний.");
            return;
        }
        boolean provided = adminPassword != null && !adminPassword.isBlank();
        String pw = provided ? adminPassword.trim() : randomPassword();
        create("admin", pw, "ADMIN", "Администратор");
        if (provided) {
            log.info("Создан первичный администратор «admin» (пароль из APP_ADMIN_PASSWORD).");
        } else {
            log.warn("Создан первичный администратор «admin» со СГЕНЕРИРОВАННЫМ паролем: {}\n" +
                    "Задайте APP_ADMIN_PASSWORD и смените пароль после первого входа.", pw);
        }
    }

    private String randomPassword() {
        byte[] b = new byte[12];
        rng.nextBytes(b);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(b);
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

    // ---- login brute-force throttle (in-memory) ----

    /** @return true if this key is currently locked out (too many recent failures). */
    public boolean isLocked(String key) {
        long[] a = attempts.get(key);
        return a != null && a[2] > System.currentTimeMillis();
    }

    /** Record a login outcome for throttling: clears the counter on success, locks after N failures. */
    public void noteLogin(String key, boolean success) {
        if (key == null) return;
        if (success) { attempts.remove(key); return; }
        long now = System.currentTimeMillis();
        attempts.compute(key, (k, a) -> {
            if (a == null || now - a[1] > lockoutSeconds * 1000L) a = new long[]{0, now, 0};
            a[0]++;
            if (a[0] >= maxAttempts) a[2] = now + lockoutSeconds * 1000L;
            return a;
        });
    }

    public long lockoutSeconds() { return lockoutSeconds; }

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
