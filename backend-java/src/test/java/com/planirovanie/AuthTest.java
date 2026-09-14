package com.planirovanie;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@TestPropertySource(properties = {
        "app.auth.enabled=true",
        "spring.datasource.url=jdbc:h2:mem:planirovanie_auth;MODE=PostgreSQL;DB_CLOSE_DELAY=-1"
})
class AuthTest {

    @Autowired MockMvc mvc;
    @Autowired ObjectMapper om;

    private static final String STATE = """
        {"state":{"params":{"name":"P","start":"2026-08-03","sprintDays":10,"focus":0.8,"today":"2026-09-10","goal":"G","sprints":11},
        "team":[{"name":"A","role":"Backend","avail":1,"absent":0}],
        "tasks":[{"id":"T-01","title":"X","role":"Backend","type":"Задача","est":5,"status":"Готово","sprint":1}]}}""";

    private String login(String user, String pass) throws Exception {
        MvcResult r = mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON)
                .content("{\"username\":\"" + user + "\",\"password\":\"" + pass + "\"}"))
                .andExpect(status().isOk()).andReturn();
        JsonNode n = om.readTree(r.getResponse().getContentAsString());
        return n.get("token").asText();
    }

    @Test
    void enforcesAuthAndRoles() throws Exception {
        // no token -> reads and writes are rejected
        mvc.perform(get("/api/state")).andExpect(status().isUnauthorized());
        mvc.perform(put("/api/state").contentType(MediaType.APPLICATION_JSON).content(STATE))
           .andExpect(status().isUnauthorized());

        // bad credentials
        mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON)
                .content("{\"username\":\"admin\",\"password\":\"wrong\"}"))
           .andExpect(status().isUnauthorized());

        // VIEWER can read but not write
        String viewer = login("viewer", "viewer123");
        mvc.perform(get("/api/state").header("Authorization", "Bearer " + viewer))
           .andExpect(status().isOk());
        mvc.perform(put("/api/state").header("Authorization", "Bearer " + viewer)
                .contentType(MediaType.APPLICATION_JSON).content(STATE))
           .andExpect(status().isForbidden());

        // EDITOR can write, but cannot manage users
        String editor = login("editor", "editor123");
        mvc.perform(put("/api/state").header("Authorization", "Bearer " + editor)
                .contentType(MediaType.APPLICATION_JSON).content(STATE))
           .andExpect(status().isOk());
        mvc.perform(get("/api/auth/users").header("Authorization", "Bearer " + editor))
           .andExpect(status().isForbidden());

        // ADMIN can manage users
        String admin = login("admin", "admin123");
        mvc.perform(get("/api/auth/users").header("Authorization", "Bearer " + admin))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$[?(@.username=='admin')].role").value(org.hamcrest.Matchers.hasItem("ADMIN")));
        mvc.perform(get("/api/auth/me").header("Authorization", "Bearer " + admin))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$.role").value("ADMIN"));

        // create a user, then it can log in
        mvc.perform(post("/api/auth/users").header("Authorization", "Bearer " + admin)
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"username\":\"kate\",\"password\":\"kate123\",\"role\":\"EDITOR\",\"displayName\":\"Kate\"}"))
           .andExpect(status().isOk());
        String kate = login("kate", "kate123");
        mvc.perform(put("/api/state").header("Authorization", "Bearer " + kate)
                .contentType(MediaType.APPLICATION_JSON).content(STATE))
           .andExpect(status().isOk());

        // logout invalidates the token
        mvc.perform(post("/api/auth/logout").header("Authorization", "Bearer " + kate))
           .andExpect(status().isNoContent());
        mvc.perform(get("/api/state").header("Authorization", "Bearer " + kate))
           .andExpect(status().isUnauthorized());
    }
}
