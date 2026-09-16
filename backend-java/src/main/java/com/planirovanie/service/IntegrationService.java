package com.planirovanie.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Outbound integrations with Slack and Jira, configured via environment variables.
 * Slack: an Incoming Webhook URL (simplest) or a bot token + channel (chat.postMessage).
 * Jira Cloud: base URL + account e-mail + API token (Basic auth) + project key.
 * Nothing is called unless the corresponding integration is configured.
 */
@Service
public class IntegrationService {

    @Value("${app.integrations.slack.webhook:${SLACK_WEBHOOK_URL:}}")   private String slackWebhook;
    @Value("${app.integrations.slack.token:${SLACK_BOT_TOKEN:}}")       private String slackToken;
    @Value("${app.integrations.slack.channel:${SLACK_CHANNEL:}}")       private String slackChannel;
    @Value("${app.integrations.jira.base:${JIRA_BASE_URL:}}")           private String jiraBase;
    @Value("${app.integrations.jira.email:${JIRA_EMAIL:}}")             private String jiraEmail;
    @Value("${app.integrations.jira.token:${JIRA_API_TOKEN:}}")         private String jiraToken;
    @Value("${app.integrations.jira.project:${JIRA_PROJECT_KEY:}}")     private String jiraProject;
    @Value("${app.integrations.jira.issueType:${JIRA_ISSUE_TYPE:Task}}")private String jiraIssueType;

    private final ObjectMapper M = new ObjectMapper();
    private volatile HttpClient http;   // built lazily on first real request (avoids network setup at startup)

    private HttpClient client() {
        if (http == null) http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(6)).build();
        return http;
    }

    private static boolean has(String s) { return s != null && !s.isBlank(); }

    public boolean slackConfigured() { return has(slackWebhook) || (has(slackToken) && has(slackChannel)); }
    public boolean jiraConfigured()  { return has(jiraBase) && has(jiraEmail) && has(jiraToken) && has(jiraProject); }

    public Map<String, Object> status() {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("slack", slackConfigured());
        m.put("jira", jiraConfigured());
        if (jiraConfigured()) { m.put("jiraProject", jiraProject); }
        return m;
    }

    /** Post a message to Slack. Returns {ok, ...} or {ok:false, error}. */
    public Map<String, Object> postSlack(String text) {
        if (!slackConfigured()) return err("Slack не настроен (SLACK_WEBHOOK_URL или SLACK_BOT_TOKEN+SLACK_CHANNEL)");
        try {
            if (has(slackWebhook)) {
                ObjectNode body = M.createObjectNode(); body.put("text", text);
                HttpResponse<String> r = send(HttpRequest.newBuilder(URI.create(slackWebhook))
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(body.toString(), StandardCharsets.UTF_8)).build());
                return r.statusCode() / 100 == 2 ? ok(null) : err("Slack webhook: HTTP " + r.statusCode());
            }
            ObjectNode body = M.createObjectNode(); body.put("channel", slackChannel); body.put("text", text);
            HttpResponse<String> r = send(HttpRequest.newBuilder(URI.create("https://slack.com/api/chat.postMessage"))
                    .header("Content-Type", "application/json; charset=utf-8")
                    .header("Authorization", "Bearer " + slackToken)
                    .POST(HttpRequest.BodyPublishers.ofString(body.toString(), StandardCharsets.UTF_8)).build());
            var json = M.readTree(r.body());
            return json.path("ok").asBoolean(false) ? ok(null) : err("Slack: " + json.path("error").asText("ошибка"));
        } catch (Exception e) { return err("Slack: " + e.getMessage()); }
    }

    /** Create a Jira issue. Returns {ok, key, url} or {ok:false, error}. */
    public Map<String, Object> createJira(String summary, String description) {
        if (!jiraConfigured()) return err("Jira не настроена (JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY)");
        try {
            ObjectNode fields = M.createObjectNode();
            fields.putObject("project").put("key", jiraProject);
            fields.put("summary", summary == null ? "(без названия)" : summary);
            fields.putObject("issuetype").put("name", jiraIssueType);
            // Jira Cloud v3 expects an ADF document for description.
            ObjectNode doc = fields.putObject("description");
            doc.put("type", "doc"); doc.put("version", 1);
            var content = doc.putArray("content").addObject();
            content.put("type", "paragraph");
            content.putArray("content").addObject().put("type", "text").put("text", description == null ? "" : description);
            ObjectNode body = M.createObjectNode(); body.set("fields", fields);
            String basic = Base64.getEncoder().encodeToString((jiraEmail + ":" + jiraToken).getBytes(StandardCharsets.UTF_8));
            String url = jiraBase.replaceAll("/+$", "") + "/rest/api/3/issue";
            HttpResponse<String> r = send(HttpRequest.newBuilder(URI.create(url))
                    .header("Content-Type", "application/json")
                    .header("Accept", "application/json")
                    .header("Authorization", "Basic " + basic)
                    .POST(HttpRequest.BodyPublishers.ofString(body.toString(), StandardCharsets.UTF_8)).build());
            if (r.statusCode() / 100 == 2) {
                String key = M.readTree(r.body()).path("key").asText("");
                Map<String, Object> m = ok(null); m.put("key", key);
                m.put("url", jiraBase.replaceAll("/+$", "") + "/browse/" + key);
                return m;
            }
            return err("Jira: HTTP " + r.statusCode() + " " + r.body());
        } catch (Exception e) { return err("Jira: " + e.getMessage()); }
    }

    private HttpResponse<String> send(HttpRequest req) throws Exception {
        return client().send(req, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
    }
    private static Map<String, Object> ok(String note) {
        Map<String, Object> m = new LinkedHashMap<>(); m.put("ok", true); if (note != null) m.put("note", note); return m;
    }
    private static Map<String, Object> err(String msg) {
        Map<String, Object> m = new LinkedHashMap<>(); m.put("ok", false); m.put("error", msg); return m;
    }
}
