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
 * Outbound integrations, configured via environment variables. Nothing is called unless the
 * corresponding integration is configured.
 *  - Slack: Incoming Webhook URL or bot token + channel.
 *  - Atlassian suite (Cloud REST): Jira, Jira Service Management, Jira Product Discovery,
 *    Confluence, Compass (status), Bitbucket, Trello, Opsgenie, Statuspage and Bamboo.
 *    Jira/JSM/JPD/Confluence/Compass share one Atlassian account (email + API token, Basic auth);
 *    Bitbucket uses an app password, Trello an API key+token, Opsgenie a GenieKey, Statuspage an
 *    API key, Bamboo a token. {@link #status()} reports which products are configured.
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
    // ---- Atlassian product suite (all Cloud REST; configured via env, off until set) ----
    @Value("${app.integrations.jsm.serviceDeskId:${JSM_SERVICE_DESK_ID:}}") private String jsmServiceDeskId;
    @Value("${app.integrations.jsm.requestTypeId:${JSM_REQUEST_TYPE_ID:}}") private String jsmRequestTypeId;
    @Value("${app.integrations.jpd.project:${JPD_PROJECT_KEY:}}")           private String jpdProject;
    @Value("${app.integrations.confluence.base:${CONFLUENCE_BASE_URL:${JIRA_BASE_URL:}}}") private String confluenceBase;
    @Value("${app.integrations.confluence.space:${CONFLUENCE_SPACE_KEY:}}") private String confluenceSpace;
    @Value("${app.integrations.compass.cloudId:${COMPASS_CLOUD_ID:}}")      private String compassCloudId;
    @Value("${app.integrations.bitbucket.workspace:${BITBUCKET_WORKSPACE:}}") private String bitbucketWorkspace;
    @Value("${app.integrations.bitbucket.user:${BITBUCKET_USER:}}")         private String bitbucketUser;
    @Value("${app.integrations.bitbucket.appPassword:${BITBUCKET_APP_PASSWORD:}}") private String bitbucketAppPassword;
    @Value("${app.integrations.bitbucket.repo:${BITBUCKET_REPO:}}")         private String bitbucketRepo;
    @Value("${app.integrations.trello.key:${TRELLO_API_KEY:}}")             private String trelloKey;
    @Value("${app.integrations.trello.token:${TRELLO_TOKEN:}}")             private String trelloToken;
    @Value("${app.integrations.trello.list:${TRELLO_LIST_ID:}}")           private String trelloList;
    @Value("${app.integrations.opsgenie.apiKey:${OPSGENIE_API_KEY:}}")      private String opsgenieKey;
    @Value("${app.integrations.statuspage.apiKey:${STATUSPAGE_API_KEY:}}")  private String statuspageKey;
    @Value("${app.integrations.statuspage.pageId:${STATUSPAGE_PAGE_ID:}}")  private String statuspagePage;
    @Value("${app.integrations.bamboo.base:${BAMBOO_BASE_URL:}}")           private String bambooBase;
    @Value("${app.integrations.bamboo.token:${BAMBOO_TOKEN:}}")             private String bambooToken;
    @Value("${app.integrations.bamboo.plan:${BAMBOO_PLAN_KEY:}}")           private String bambooPlan;

    private final ObjectMapper M = new ObjectMapper();
    private volatile HttpClient http;   // built lazily on first real request (avoids network setup at startup)

    private HttpClient client() {
        if (http == null) http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(6)).build();
        return http;
    }

    private static boolean has(String s) { return s != null && !s.isBlank(); }

    private boolean atlassianAuth() { return has(jiraEmail) && has(jiraToken); }   // shared Atlassian API token

    public boolean slackConfigured() { return has(slackWebhook) || (has(slackToken) && has(slackChannel)); }
    public boolean jiraConfigured()  { return has(jiraBase) && atlassianAuth() && has(jiraProject); }
    public boolean jsmConfigured()   { return has(jiraBase) && atlassianAuth() && has(jsmServiceDeskId) && has(jsmRequestTypeId); }
    public boolean jpdConfigured()   { return has(jiraBase) && atlassianAuth() && has(jpdProject); }
    public boolean confluenceConfigured() { return has(confluenceBase) && atlassianAuth() && has(confluenceSpace); }
    public boolean compassConfigured()    { return has(jiraBase) && atlassianAuth() && has(compassCloudId); }
    public boolean bitbucketConfigured()  { return has(bitbucketWorkspace) && has(bitbucketUser) && has(bitbucketAppPassword); }
    public boolean trelloConfigured()     { return has(trelloKey) && has(trelloToken) && has(trelloList); }
    public boolean opsgenieConfigured()   { return has(opsgenieKey); }
    public boolean statuspageConfigured() { return has(statuspageKey) && has(statuspagePage); }
    public boolean bambooConfigured()     { return has(bambooBase) && has(bambooToken) && has(bambooPlan); }

    public Map<String, Object> status() {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("slack", slackConfigured());
        m.put("jira", jiraConfigured());
        if (jiraConfigured()) { m.put("jiraProject", jiraProject); }
        // Atlassian product suite — configured flags for each product.
        Map<String, Object> a = new LinkedHashMap<>();
        a.put("jira", jiraConfigured());
        a.put("jsm", jsmConfigured());                 // Jira Service Management
        a.put("jpd", jpdConfigured());                 // Jira Product Discovery
        a.put("confluence", confluenceConfigured());
        a.put("compass", compassConfigured());
        a.put("bitbucket", bitbucketConfigured());
        a.put("trello", trelloConfigured());
        a.put("opsgenie", opsgenieConfigured());
        a.put("statuspage", statuspageConfigured());
        a.put("bamboo", bambooConfigured());
        m.put("atlassian", a);
        return m;
    }

    /** Dispatch a "create/notify" action to any supported Atlassian product by key. */
    public Map<String, Object> atlassian(String product, String title, String body) {
        if (product == null) return err("Не указан продукт Atlassian");
        switch (product.toLowerCase()) {
            case "jira":       return createJira(title, body);
            case "jsm":        return createJsmRequest(title, body);
            case "confluence": return createConfluencePage(title, body);
            case "bitbucket":  return createBitbucketIssue(title, body);
            case "trello":     return createTrelloCard(title, body);
            case "opsgenie":   return createOpsgenieAlert(title, body);
            case "statuspage": return createStatuspageIncident(title, body);
            case "bamboo":     return triggerBambooBuild();
            default:           return err("Действие для продукта «" + product + "» не поддерживается (доступно как статус-интеграция)");
        }
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

    private String atlassianBasic() {
        return Base64.getEncoder().encodeToString((jiraEmail + ":" + jiraToken).getBytes(StandardCharsets.UTF_8));
    }
    private static String trim(String base) { return base == null ? "" : base.replaceAll("/+$", ""); }

    /** Jira Service Management: raise a customer request. */
    public Map<String, Object> createJsmRequest(String summary, String description) {
        if (!jsmConfigured()) return err("Jira Service Management не настроена (JSM_SERVICE_DESK_ID, JSM_REQUEST_TYPE_ID + Jira base/email/token)");
        try {
            ObjectNode body = M.createObjectNode();
            body.put("serviceDeskId", jsmServiceDeskId);
            body.put("requestTypeId", jsmRequestTypeId);
            ObjectNode fv = body.putObject("requestFieldValues");
            fv.put("summary", summary == null ? "(без названия)" : summary);
            fv.put("description", description == null ? "" : description);
            HttpResponse<String> r = send(HttpRequest.newBuilder(URI.create(trim(jiraBase) + "/rest/servicedeskapi/request"))
                    .header("Content-Type", "application/json").header("Accept", "application/json")
                    .header("Authorization", "Basic " + atlassianBasic())
                    .POST(HttpRequest.BodyPublishers.ofString(body.toString(), StandardCharsets.UTF_8)).build());
            if (r.statusCode() / 100 == 2) { Map<String, Object> m = ok(null); m.put("key", M.readTree(r.body()).path("issueKey").asText("")); return m; }
            return err("JSM: HTTP " + r.statusCode() + " " + r.body());
        } catch (Exception e) { return err("JSM: " + e.getMessage()); }
    }

    /** Confluence Cloud: publish a page (storage-format HTML) in the configured space. */
    public Map<String, Object> createConfluencePage(String title, String html) {
        if (!confluenceConfigured()) return err("Confluence не настроен (CONFLUENCE_BASE_URL, CONFLUENCE_SPACE_KEY + Atlassian email/token)");
        try {
            ObjectNode body = M.createObjectNode();
            body.put("type", "page"); body.put("title", title == null ? "Untitled" : title);
            body.putObject("space").put("key", confluenceSpace);   // space {key}
            ObjectNode storage = body.putObject("body").putObject("storage");
            storage.put("value", html == null ? "" : html); storage.put("representation", "storage");
            HttpResponse<String> r = send(HttpRequest.newBuilder(URI.create(trim(confluenceBase) + "/wiki/rest/api/content"))
                    .header("Content-Type", "application/json").header("Accept", "application/json")
                    .header("Authorization", "Basic " + atlassianBasic())
                    .POST(HttpRequest.BodyPublishers.ofString(body.toString(), StandardCharsets.UTF_8)).build());
            if (r.statusCode() / 100 == 2) { Map<String, Object> m = ok(null); m.put("id", M.readTree(r.body()).path("id").asText("")); return m; }
            return err("Confluence: HTTP " + r.statusCode() + " " + r.body());
        } catch (Exception e) { return err("Confluence: " + e.getMessage()); }
    }

    /** Bitbucket Cloud: create an issue in the configured repository. */
    public Map<String, Object> createBitbucketIssue(String title, String content) {
        if (!bitbucketConfigured()) return err("Bitbucket не настроен (BITBUCKET_WORKSPACE, BITBUCKET_USER, BITBUCKET_APP_PASSWORD, BITBUCKET_REPO)");
        if (!has(bitbucketRepo)) return err("Не задан BITBUCKET_REPO");
        try {
            ObjectNode body = M.createObjectNode();
            body.put("title", title == null ? "(no title)" : title);
            body.putObject("content").put("raw", content == null ? "" : content);
            String basic = Base64.getEncoder().encodeToString((bitbucketUser + ":" + bitbucketAppPassword).getBytes(StandardCharsets.UTF_8));
            String url = "https://api.bitbucket.org/2.0/repositories/" + bitbucketWorkspace + "/" + bitbucketRepo + "/issues";
            HttpResponse<String> r = send(HttpRequest.newBuilder(URI.create(url))
                    .header("Content-Type", "application/json").header("Authorization", "Basic " + basic)
                    .POST(HttpRequest.BodyPublishers.ofString(body.toString(), StandardCharsets.UTF_8)).build());
            if (r.statusCode() / 100 == 2) { Map<String, Object> m = ok(null); m.put("id", M.readTree(r.body()).path("id").asText("")); return m; }
            return err("Bitbucket: HTTP " + r.statusCode() + " " + r.body());
        } catch (Exception e) { return err("Bitbucket: " + e.getMessage()); }
    }

    /** Trello: create a card on the configured list. */
    public Map<String, Object> createTrelloCard(String name, String desc) {
        if (!trelloConfigured()) return err("Trello не настроен (TRELLO_API_KEY, TRELLO_TOKEN, TRELLO_LIST_ID)");
        try {
            String q = "?idList=" + enc(trelloList) + "&key=" + enc(trelloKey) + "&token=" + enc(trelloToken)
                    + "&name=" + enc(name == null ? "" : name) + "&desc=" + enc(desc == null ? "" : desc);
            HttpResponse<String> r = send(HttpRequest.newBuilder(URI.create("https://api.trello.com/1/cards" + q))
                    .POST(HttpRequest.BodyPublishers.noBody()).build());
            if (r.statusCode() / 100 == 2) { Map<String, Object> m = ok(null); m.put("id", M.readTree(r.body()).path("id").asText("")); m.put("url", M.readTree(r.body()).path("url").asText("")); return m; }
            return err("Trello: HTTP " + r.statusCode() + " " + r.body());
        } catch (Exception e) { return err("Trello: " + e.getMessage()); }
    }

    /** Opsgenie: create an alert. */
    public Map<String, Object> createOpsgenieAlert(String message, String description) {
        if (!opsgenieConfigured()) return err("Opsgenie не настроен (OPSGENIE_API_KEY)");
        try {
            ObjectNode body = M.createObjectNode();
            body.put("message", message == null ? "(no message)" : message);
            body.put("description", description == null ? "" : description);
            HttpResponse<String> r = send(HttpRequest.newBuilder(URI.create("https://api.opsgenie.com/v2/alerts"))
                    .header("Content-Type", "application/json").header("Authorization", "GenieKey " + opsgenieKey)
                    .POST(HttpRequest.BodyPublishers.ofString(body.toString(), StandardCharsets.UTF_8)).build());
            return r.statusCode() / 100 == 2 ? ok(null) : err("Opsgenie: HTTP " + r.statusCode() + " " + r.body());
        } catch (Exception e) { return err("Opsgenie: " + e.getMessage()); }
    }

    /** Statuspage: create an incident on the configured page. */
    public Map<String, Object> createStatuspageIncident(String name, String bodyText) {
        if (!statuspageConfigured()) return err("Statuspage не настроен (STATUSPAGE_API_KEY, STATUSPAGE_PAGE_ID)");
        try {
            ObjectNode inc = M.createObjectNode();
            ObjectNode i = inc.putObject("incident");
            i.put("name", name == null ? "(no name)" : name); i.put("status", "investigating"); i.put("body", bodyText == null ? "" : bodyText);
            HttpResponse<String> r = send(HttpRequest.newBuilder(URI.create("https://api.statuspage.io/v1/pages/" + statuspagePage + "/incidents"))
                    .header("Content-Type", "application/json").header("Authorization", "OAuth " + statuspageKey)
                    .POST(HttpRequest.BodyPublishers.ofString(inc.toString(), StandardCharsets.UTF_8)).build());
            return r.statusCode() / 100 == 2 ? ok(null) : err("Statuspage: HTTP " + r.statusCode() + " " + r.body());
        } catch (Exception e) { return err("Statuspage: " + e.getMessage()); }
    }

    /** Bamboo: trigger a build of the configured plan. */
    public Map<String, Object> triggerBambooBuild() {
        if (!bambooConfigured()) return err("Bamboo не настроен (BAMBOO_BASE_URL, BAMBOO_TOKEN, BAMBOO_PLAN_KEY)");
        try {
            HttpResponse<String> r = send(HttpRequest.newBuilder(URI.create(trim(bambooBase) + "/rest/api/latest/queue/" + bambooPlan + "?os_authType=basic"))
                    .header("Accept", "application/json").header("Authorization", "Bearer " + bambooToken)
                    .POST(HttpRequest.BodyPublishers.noBody()).build());
            return r.statusCode() / 100 == 2 ? ok(null) : err("Bamboo: HTTP " + r.statusCode() + " " + r.body());
        } catch (Exception e) { return err("Bamboo: " + e.getMessage()); }
    }

    private static String enc(String s) {
        return java.net.URLEncoder.encode(s == null ? "" : s, StandardCharsets.UTF_8);
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
