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

    /** Generic Atlassian action: /api/integrations/atlassian/{product} with {title, body}.
     *  product ∈ jira | jsm | confluence | bitbucket | trello | opsgenie | statuspage | bamboo. */
    @PostMapping("/atlassian/{product}")
    public Map<String, Object> atlassian(@PathVariable String product, @RequestBody(required = false) Map<String, String> body) {
        Map<String, String> b = body == null ? Map.of() : body;
        String title = b.getOrDefault("title", b.get("summary"));
        String text = b.getOrDefault("body", b.getOrDefault("description", ""));
        return svc.atlassian(product, title, text);
    }
}
