package com.planirovanie;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.planirovanie.service.AuditService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@TestPropertySource(properties = {
        "app.auth.enabled=true",
        "app.auth.seed-defaults=true",   // logs in as the demo admin/editor/viewer accounts
        "app.audit.enabled=true",
        "app.audit.url=jdbc:h2:mem:auditlog;MODE=PostgreSQL;DB_CLOSE_DELAY=-1",
        "app.audit.username=sa",
        "app.audit.password=",
        "app.audit.driver-class-name=org.h2.Driver",
        "spring.datasource.url=jdbc:h2:mem:planirovanie_audit_primary;MODE=PostgreSQL;DB_CLOSE_DELAY=-1"
})
class AuditTest {

    @Autowired MockMvc mvc;
    @Autowired ObjectMapper om;
    @Autowired AuditService audit;

    private static final String STATE = """
        {"state":{"params":{"name":"P","start":"2026-08-03","sprintDays":10,"focus":0.8,"today":"2026-09-10","goal":"G","sprints":11},
        "team":[{"name":"A","role":"Backend","avail":1,"absent":0}],
        "tasks":[{"id":"T-01","title":"X","role":"Backend","type":"Задача","est":5,"status":"Готово","sprint":1}]}}""";

    private String login(String user, String pass) throws Exception {
        MvcResult r = mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON)
                .content("{\"username\":\"" + user + "\",\"password\":\"" + pass + "\"}"))
                .andExpect(status().isOk()).andReturn();
        return om.readTree(r.getResponse().getContentAsString()).get("token").asText();
    }

    private void awaitAtLeast(long n) throws Exception {
        for (int i = 0; i < 40 && audit.count() < n; i++) Thread.sleep(50);
    }

    @Test
    void logsEventsToSeparateDatabase() throws Exception {
        assertTrue(audit.isEnabled(), "audit should be enabled against H2");

        String admin = login("admin", "admin123");
        mvc.perform(get("/api/state").header("Authorization", "Bearer " + admin)).andExpect(status().isOk());
        mvc.perform(put("/api/state").header("Authorization", "Bearer " + admin)
                .contentType(MediaType.APPLICATION_JSON).content(STATE)).andExpect(status().isOk());

        // failed login + a forbidden write (viewer) → AUTH login_failed + DENY
        mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON)
                .content("{\"username\":\"admin\",\"password\":\"nope\"}")).andExpect(status().isUnauthorized());
        String viewer = login("viewer", "viewer123");
        mvc.perform(put("/api/state").header("Authorization", "Bearer " + viewer)
                .contentType(MediaType.APPLICATION_JSON).content(STATE)).andExpect(status().isForbidden());

        // client-side event ingest (viewer allowed)
        mvc.perform(post("/api/audit/client").header("Authorization", "Bearer " + viewer)
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"action\":\"open_section\",\"detail\":\"risks\"}")).andExpect(status().isOk());

        awaitAtLeast(6);

        // admin reads the log; editor is forbidden
        MvcResult r = mvc.perform(get("/api/audit?limit=200").header("Authorization", "Bearer " + admin))
                .andExpect(status().isOk()).andReturn();
        JsonNode body = om.readTree(r.getResponse().getContentAsString());
        assertTrue(body.get("enabled").asBoolean());
        JsonNode events = body.get("events");
        assertTrue(events.size() >= 5, "expected several events, got " + events.size());

        String all = events.toString();
        assertTrue(all.contains("\"AUTH\""), "AUTH events present");
        assertTrue(all.contains("login_failed"), "failed login recorded");
        assertTrue(all.contains("\"DATA\""), "data save recorded");
        assertTrue(all.contains("\"DENY\""), "forbidden write recorded");
        assertTrue(all.contains("\"CLIENT\""), "client event recorded");

        String editor = login("editor", "editor123");
        mvc.perform(get("/api/audit").header("Authorization", "Bearer " + editor)).andExpect(status().isForbidden());
    }
}
