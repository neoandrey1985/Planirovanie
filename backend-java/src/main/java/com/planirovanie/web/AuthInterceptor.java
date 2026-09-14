package com.planirovanie.web;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.planirovanie.entity.UserSession;
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
    private final ObjectMapper json = new ObjectMapper();

    @Value("${app.auth.enabled:true}")
    private boolean enabled;

    public AuthInterceptor(AuthService auth) {
        this.auth = auth;
    }

    @Override
    public boolean preHandle(HttpServletRequest req, HttpServletResponse res, Object handler) throws Exception {
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
        // Any mutation of application data requires EDITOR or ADMIN.
        if (writing && !("EDITOR".equals(role) || "ADMIN".equals(role))) {
            return deny(res, 403, "forbidden");
        }
        return true;
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
