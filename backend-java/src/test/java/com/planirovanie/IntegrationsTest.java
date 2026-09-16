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
    void notConfiguredByDefault() {
        IntegrationService s = new IntegrationService();
        assertFalse(s.slackConfigured());
        assertFalse(s.jiraConfigured());
        Map<String, Object> st = s.status();
        assertEquals(Boolean.FALSE, st.get("slack"));
        assertEquals(Boolean.FALSE, st.get("jira"));
        // Actions must fail gracefully (no exception) when unconfigured.
        assertEquals(Boolean.FALSE, s.postSlack("hi").get("ok"));
        assertEquals(Boolean.FALSE, s.createJira("S", "D").get("ok"));
    }

    @Test
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
    }
}
