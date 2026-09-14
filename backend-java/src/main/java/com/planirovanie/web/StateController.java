package com.planirovanie.web;

import com.planirovanie.dto.Dtos.*;
import com.planirovanie.service.StateService;
import com.planirovanie.service.VersionConflictException;
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

    public StateController(StateService service) {
        this.service = service;
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
    public ResponseEntity<?> put(@RequestBody StateEnvelope env) {
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
