package com.planirovanie.web;

import com.planirovanie.dto.Dtos.*;
import com.planirovanie.service.StateService;
import com.planirovanie.service.VersionConflictException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.util.Map;

/** Document-oriented state endpoint, compatible with the existing sync client. */
@RestController
@RequestMapping("/api")
public class StateController {

    private final StateService service;

    @Value("${app.team-token:}")
    private String token;

    public StateController(StateService service) {
        this.service = service;
    }

    private boolean authorized(String provided) {
        return token == null || token.isBlank() || token.equals(provided);
    }

    @GetMapping("/state")
    public ResponseEntity<?> get(@RequestHeader(value = "X-Team-Token", required = false) String t) {
        if (!authorized(t)) return ResponseEntity.status(401).body(Map.of("error", "unauthorized"));
        return ResponseEntity.ok(new StateResponse(service.version(), service.get(), Instant.now().toString()));
    }

    @RequestMapping(value = "/state", method = RequestMethod.HEAD)
    public ResponseEntity<Void> head(@RequestHeader(value = "X-Team-Token", required = false) String t) {
        return authorized(t) ? ResponseEntity.ok().build() : ResponseEntity.status(401).build();
    }

    @PutMapping("/state")
    public ResponseEntity<?> put(@RequestHeader(value = "X-Team-Token", required = false) String t,
                                 @RequestBody StateEnvelope env) {
        if (!authorized(t)) return ResponseEntity.status(401).body(Map.of("error", "unauthorized"));
        try {
            long v = service.replace(env == null ? null : env.state, env == null ? null : env.baseVersion);
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
