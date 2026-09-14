package com.planirovanie.web;

import com.planirovanie.entity.UserSession;
import com.planirovanie.service.AuditService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * Audit log endpoints.
 *  - POST /api/audit/client : any signed-in user records a client-side UI event.
 *  - GET  /api/audit        : ADMIN reads recent events (interceptor enforces the roles).
 */
@RestController
@RequestMapping("/api/audit")
public class AuditController {

    private final AuditService audit;

    public AuditController(AuditService audit) {
        this.audit = audit;
    }

    public record ClientEvent(String action, String detail) {}

    @PostMapping("/client")
    public Map<String, Object> client(@RequestBody(required = false) ClientEvent ev, HttpServletRequest req) {
        String user = null, role = null;
        Object s = req.getAttribute("session");
        if (s instanceof UserSession us) { user = us.username; role = us.role; }
        String action = ev == null || ev.action() == null ? "event" : ev.action();
        String detail = ev == null ? null : ev.detail();
        audit.log("CLIENT", action, user, role, "UI", null, null, null,
                req.getRemoteAddr(), req.getHeader("User-Agent"), detail);
        return Map.of("ok", audit.isEnabled());
    }

    @GetMapping
    public Map<String, Object> list(@RequestParam(defaultValue = "200") int limit,
                                    @RequestParam(required = false) String category,
                                    @RequestParam(required = false) String user) {
        List<Map<String, Object>> events = audit.recent(limit, category, user);
        return Map.of("enabled", audit.isEnabled(), "total", audit.count(), "events", events);
    }
}
