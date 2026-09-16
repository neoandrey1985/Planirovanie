package com.planirovanie.web;

import com.planirovanie.service.IntegrationService;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * Integration endpoints. Reads (GET status) require any signed-in user; the POST actions
 * require EDITOR/ADMIN (enforced by AuthInterceptor on /api/**).
 */
@RestController
@RequestMapping("/api/integrations")
public class IntegrationsController {

    private final IntegrationService svc;

    public IntegrationsController(IntegrationService svc) { this.svc = svc; }

    @GetMapping("/status")
    public Map<String, Object> status() { return svc.status(); }

    @PostMapping("/slack")
    public Map<String, Object> slack(@RequestBody Map<String, String> body) {
        return svc.postSlack(body.getOrDefault("text", ""));
    }

    @PostMapping("/jira")
    public Map<String, Object> jira(@RequestBody Map<String, String> body) {
        return svc.createJira(body.get("summary"), body.getOrDefault("description", ""));
    }
}
