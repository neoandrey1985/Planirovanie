package com.planirovanie.web;

import com.planirovanie.dto.Dtos.*;
import com.planirovanie.entity.UserSession;
import com.planirovanie.service.AuditService;
import com.planirovanie.service.StateService;
import com.planirovanie.service.VersionConflictException;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.util.Map;

/**
 * Document-oriented state endpoint, compatible with the existing sync client.
 * Authentication and role checks are enforced centrally by {@link AuthInterceptor}
 * (reads need any authenticated user; writes need EDITOR or ADMIN).
 */
@RestController
@RequestMapping("/api")
public class StateController {

    private final StateService service;
    private final AuditService audit;

    public StateController(StateService service, AuditService audit) {
        this.service = service;
        this.audit = audit;
    }

    @GetMapping("/state")
    public ResponseEntity<?> get() {
        return ResponseEntity.ok(new StateResponse(service.version(), service.get(), Instant.now().toString()));
    }

    @RequestMapping(value = "/state", method = RequestMethod.HEAD)
    public ResponseEntity<Void> head() {
        return ResponseEntity.ok().build();
    }

    @PutMapping("/state")
    public ResponseEntity<?> put(@RequestBody StateEnvelope env, HttpServletRequest http) {
        try {
            long v = service.replace(env == null ? null : env.state, env == null ? null : env.baseVersion);
            Object s = http.getAttribute("session");
            String user = s instanceof UserSession us ? us.username : null;
            String role = s instanceof UserSession us ? us.role : null;
            audit.log("DATA", "state_saved", user, role, "PUT", "/api/state", 200, null,
                    http.getRemoteAddr(), http.getHeader("User-Agent"), "Сохранение данных, версия " + v);
            return ResponseEntity.ok(new PutResponse(v, Instant.now().toString()));
        } catch (VersionConflictException ex) {
            // Someone else saved first: return current version and fresh state so the client can reconcile.
            return ResponseEntity.status(409).body(Map.of(
                    "error", "version_conflict",
                    "version", ex.currentVersion,
                    "state", service.get()));
        }
    }
}
