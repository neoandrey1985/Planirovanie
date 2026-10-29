package com.planirovanie;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.planirovanie.service.AuthService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/** «Мой профиль»: любой пользователь (в т.ч. VIEWER) привязывает себя к участнику команды и меняет свой пароль. */
@SpringBootTest
@AutoConfigureMockMvc
@TestPropertySource(properties = {
        "app.auth.enabled=true",
        "app.auth.seed-defaults=true",
        "app.auth.max-attempts=3",
        "spring.datasource.url=jdbc:h2:mem:planirovanie_profile;MODE=PostgreSQL;DB_CLOSE_DELAY=-1"
})
class ProfileTest {

    @Autowired MockMvc mvc;
    @Autowired ObjectMapper om;
    @Autowired AuthService auth;

    private JsonNode json(MvcResult r) throws Exception { return om.readTree(r.getResponse().getContentAsString(StandardCharsets.UTF_8)); }

    private MvcResult loginRaw(String user, String pass) throws Exception {
        return mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON)
                .content("{\"username\":\"" + user + "\",\"password\":\"" + pass + "\"}")).andReturn();
    }

    private String login(String user, String pass) throws Exception {
        MvcResult r = loginRaw(user, pass);
        assertEquals(200, r.getResponse().getStatus());
        return json(r).get("token").asText();
    }

    private int password(String token, String oldP, String newP) throws Exception {
        return mvc.perform(put("/api/auth/me/password").header("Authorization", "Bearer " + token).contentType(MediaType.APPLICATION_JSON)
                .content("{\"oldPassword\":\"" + oldP + "\",\"newPassword\":\"" + newP + "\"}")).andReturn().getResponse().getStatus();
    }

    @Test
    void memberBindingForAnyRole() throws Exception {
        auth.create("anna", "Anna-pass-1", "VIEWER", "Анна");
        String tk = login("anna", "Anna-pass-1");
        JsonNode me = json(mvc.perform(get("/api/auth/me").header("Authorization", "Bearer " + tk)).andExpect(status().isOk()).andReturn());
        assertTrue(me.get("member").isNull());
        // VIEWER может менять свой профиль, хотя данные приложения ему только на чтение
        JsonNode upd = json(mvc.perform(put("/api/auth/me").header("Authorization", "Bearer " + tk).contentType(MediaType.APPLICATION_JSON)
                .content("{\"member\":\"  Иванов А. \"}")).andExpect(status().isOk()).andReturn());
        assertEquals("Иванов А.", upd.get("member").asText());
        assertEquals("Иванов А.", json(loginRaw("anna", "Anna-pass-1")).get("member").asText());   // и при входе
        mvc.perform(put("/api/auth/me").header("Authorization", "Bearer " + tk).contentType(MediaType.APPLICATION_JSON)
                .content("{\"member\":\"\"}")).andExpect(status().isOk());
        assertTrue(json(mvc.perform(get("/api/auth/me").header("Authorization", "Bearer " + tk)).andReturn()).get("member").isNull());
        mvc.perform(put("/api/state").header("Authorization", "Bearer " + tk).contentType(MediaType.APPLICATION_JSON)
                .content("{\"state\":{}}")).andExpect(status().isForbidden());                  // права на данные не расширились
        mvc.perform(put("/api/auth/me").contentType(MediaType.APPLICATION_JSON).content("{\"member\":\"X\"}"))
           .andExpect(status().isUnauthorized());
    }

    @Test
    void ownPasswordChange() throws Exception {
        auth.create("boris", "Boris-pass-1", "EDITOR", "Борис");
        String tk = login("boris", "Boris-pass-1"), other = login("boris", "Boris-pass-1");
        assertEquals(403, password(tk, "wrong-pass", "Boris-new-2"));      // неверный текущий
        assertEquals(400, password(tk, "Boris-pass-1", "short"));          // короче 8 символов
        assertEquals(400, password(tk, "Boris-pass-1", "Boris-pass-1"));   // тот же пароль
        assertEquals(204, password(tk, "Boris-pass-1", "Boris-new-2"));
        assertEquals(401, loginRaw("boris", "Boris-pass-1").getResponse().getStatus());
        login("boris", "Boris-new-2");
        // текущая сессия жива, остальные закрыты
        mvc.perform(get("/api/auth/me").header("Authorization", "Bearer " + tk)).andExpect(status().isOk());
        mvc.perform(get("/api/auth/me").header("Authorization", "Bearer " + other)).andExpect(status().isUnauthorized());
        // подбор текущего пароля ограничен
        String t2 = login("boris", "Boris-new-2");
        for (int i = 0; i < 3; i++) assertEquals(403, password(t2, "guess-" + i, "Boris-new-3"));
        assertEquals(429, password(t2, "Boris-new-2", "Boris-new-3"));
    }
}
