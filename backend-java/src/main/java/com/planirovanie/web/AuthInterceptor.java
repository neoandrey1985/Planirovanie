package com.planirovanie.web;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.planirovanie.entity.UserSession;
import com.planirovanie.service.AuditService;
import com.planirovanie.service.AuthService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import java.util.Map;
import java.util.Optional;

/**
 * Enforces authentication and role-based authorization on every /api request:
 *   - public: login, health, CORS preflight, and the HEAD probe on /api/state;
 *   - reads (GET): any authenticated user (VIEWER+);
 *   - writes (POST/PUT/DELETE/PATCH): EDITOR or ADMIN;
 *   - /api/auth/users**: ADMIN only.
 * The resolved {@link UserSession} is exposed to controllers as request attribute "session".
 */
@Component
public class AuthInterceptor implements HandlerInterceptor {

    private final AuthService auth;
    private final AuditService audit;
    private final ObjectMapper json = new ObjectMapper();

    @Value("${app.auth.enabled:true}")
    private boolean enabled;

    public AuthInterceptor(AuthService auth, AuditService audit) {
        this.auth = auth;
        this.audit = audit;
    }

    @Override
    public boolean preHandle(HttpServletRequest req, HttpServletResponse res, Object handler) throws Exception {
        req.setAttribute("t0", System.currentTimeMillis());
        String method = req.getMethod();
        if ("OPTIONS".equals(method)) return true;                       // CORS preflight

        String path = req.getRequestURI();
        // Always-public endpoints.
        if (path.endsWith("/api/health")) return true;
        if (path.endsWith("/api/auth/login")) return true;
        if (path.endsWith("/api/state") && "HEAD".equals(method)) return true;   // backend-presence probe

        // Resolve the bearer token (if any) so controllers can read the current user.
        Optional<UserSession> session = auth.resolve(bearer(req));
        session.ifPresent(s -> req.setAttribute("session", s));

        if (!enabled) return true;                                       // auth disabled (e.g. tests/dev)

        if (session.isEmpty()) return deny(res, 401, "unauthorized");

        String role = session.get().role;
        boolean writing = method.equals("POST") || method.equals("PUT")
                || method.equals("DELETE") || method.equals("PATCH");

        // ADMIN-only surface: user & role management.
        if (path.contains("/api/auth/users")) {
            return "ADMIN".equals(role) ? true : deny(res, 403, "forbidden");
        }
        // Client-side event ingest: any signed-in user (incl. VIEWER) may record UI events.
        if (path.contains("/api/audit/client")) return true;
        // Reading the audit log is ADMIN-only.
        if (path.contains("/api/audit")) {
            return "ADMIN".equals(role) ? true : deny(res, 403, "forbidden");
        }
        // Any mutation of application data requires EDITOR or ADMIN.
        if (writing && !("EDITOR".equals(role) || "ADMIN".equals(role))) {
            return deny(res, 403, "forbidden");
        }
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest req, HttpServletResponse res, Object handler, Exception ex) {
        try {
            if (audit == null || !audit.isEnabled()) return;
            String path = req.getRequestURI();
            String method = req.getMethod();
            if ("OPTIONS".equals(method)) return;
            if (path.contains("/api/audit")) return;                     // don't log the audit endpoints themselves
            Object s = req.getAttribute("session");
            String user = null, role = null;
            if (s instanceof UserSession us) { user = us.username; role = us.role; }
            int status = res.getStatus();
            Object t0 = req.getAttribute("t0");
            Integer dur = (t0 instanceof Long l) ? (int) (System.currentTimeMillis() - l) : null;
            String category = status == 401 || status == 403 ? "DENY" : (status >= 500 ? "ERROR" : "ACCESS");
            audit.log(category, method, user, role, method, path, status, dur,
                    req.getRemoteAddr(), req.getHeader("User-Agent"), null);
        } catch (Exception ignore) { /* logging must never break the response */ }
    }

    private static String bearer(HttpServletRequest req) {
        String h = req.getHeader("Authorization");
        if (h != null && h.regionMatches(true, 0, "Bearer ", 0, 7)) return h.substring(7).trim();
        return req.getHeader("X-Auth-Token");                           // convenience fallback
    }

    private boolean deny(HttpServletResponse res, int status, String error) throws Exception {
        res.setStatus(status);
        res.setContentType("application/json");
        res.getWriter().write(json.writeValueAsString(Map.of("error", error)));
        return false;
    }
}
