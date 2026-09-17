package com.planirovanie;

import com.planirovanie.service.IntegrationService;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Verifies integration config detection and the safe "not configured" behaviour without any
 * network calls (Slack/Jira endpoints cannot be reached from the sandbox).
 */
class IntegrationsTest {

    @Test
    @SuppressWarnings("unchecked")
    void notConfiguredByDefault() {
        IntegrationService s = new IntegrationService();
        assertFalse(s.slackConfigured());
        assertFalse(s.jiraConfigured());
        Map<String, Object> st = s.status();
        assertEquals(Boolean.FALSE, st.get("slack"));
        assertEquals(Boolean.FALSE, st.get("jira"));
        // Every Atlassian product is reported and off by default.
        Map<String, Object> a = (Map<String, Object>) st.get("atlassian");
        assertNotNull(a);
        for (String p : new String[]{"jira", "jsm", "jpd", "confluence", "compass", "bitbucket",
                "trello", "opsgenie", "statuspage", "bamboo"}) {
            assertEquals(Boolean.FALSE, a.get(p), p + " should be off by default");
        }
        // Actions must fail gracefully (no exception, ok:false) when unconfigured.
        assertEquals(Boolean.FALSE, s.postSlack("hi").get("ok"));
        assertEquals(Boolean.FALSE, s.createJira("S", "D").get("ok"));
        assertEquals(Boolean.FALSE, s.createConfluencePage("t", "b").get("ok"));
        assertEquals(Boolean.FALSE, s.createTrelloCard("n", "d").get("ok"));
        assertEquals(Boolean.FALSE, s.createOpsgenieAlert("m", "d").get("ok"));
        assertEquals(Boolean.FALSE, s.atlassian("bitbucket", "t", "b").get("ok"));
        assertEquals(Boolean.FALSE, s.atlassian("unknown", "t", "b").get("ok"));
    }

    @Test
    @SuppressWarnings("unchecked")
    void detectsConfiguration() {
        IntegrationService s = new IntegrationService();
        ReflectionTestUtils.setField(s, "slackWebhook", "https://hooks.slack.com/services/XXX");
        ReflectionTestUtils.setField(s, "jiraBase", "https://x.atlassian.net");
        ReflectionTestUtils.setField(s, "jiraEmail", "a@b.c");
        ReflectionTestUtils.setField(s, "jiraToken", "tok");
        ReflectionTestUtils.setField(s, "jiraProject", "PLAN");
        assertTrue(s.slackConfigured());
        assertTrue(s.jiraConfigured());
        assertEquals("PLAN", s.status().get("jiraProject"));
        // Confluence reuses the Atlassian email/token; adding a space enables it.
        ReflectionTestUtils.setField(s, "confluenceBase", "https://x.atlassian.net");
        ReflectionTestUtils.setField(s, "confluenceSpace", "TEAM");
        assertTrue(s.confluenceConfigured());
        // Trello uses its own key/token/list.
        ReflectionTestUtils.setField(s, "trelloKey", "k");
        ReflectionTestUtils.setField(s, "trelloToken", "t");
        ReflectionTestUtils.setField(s, "trelloList", "l");
        assertTrue(s.trelloConfigured());
        Map<String, Object> a = (Map<String, Object>) s.status().get("atlassian");
        assertEquals(Boolean.TRUE, a.get("jira"));
        assertEquals(Boolean.TRUE, a.get("confluence"));
        assertEquals(Boolean.TRUE, a.get("trello"));
        assertEquals(Boolean.FALSE, a.get("bitbucket"));
    }
}
