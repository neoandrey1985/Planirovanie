package com.planirovanie;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class StateRoundTripTest {

    @Autowired
    MockMvc mvc;

    private static final String STATE = """
        {"state":{
          "params":{"name":"P","start":"2026-08-03","sprintDays":10,"focus":0.8,"today":"2026-09-10","goal":"G","sprints":11},
          "budget":{"rate":8000,"total":8000000},
          "ttmTarget":15,
          "team":[{"name":"A","role":"Backend","avail":1,"absent":0}],
          "tasks":[{"id":"T-01","title":"X","role":"Backend","type":"Задача","est":5,"status":"Готово","sprint":1}],
          "deps":[{"id":"D-01","item":"I","stream":"S","dir":"Мы зависим","status":"Заблокировано","task":"T-01"}],
          "rice":[{"id":"F-01","name":"R","reach":5000,"impact":3,"conf":"100%","effort":40}],
          "calendar":[{"date":"2026-11-04","name":"Праздник"}]
        }}""";

    @Test
    void stateRoundTripAndVersioning() throws Exception {
        mvc.perform(get("/api/health"))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$.status").value("ok"));

        mvc.perform(put("/api/state").contentType(MediaType.APPLICATION_JSON).content(STATE))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$.version").value(1));

        mvc.perform(get("/api/state"))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$.version").value(1))
           .andExpect(jsonPath("$.state.params.start").value("2026-08-03"))
           .andExpect(jsonPath("$.state.budget.rate").value(8000.0))
           .andExpect(jsonPath("$.state.ttmTarget").value(15))
           .andExpect(jsonPath("$.state.tasks[0].id").value("T-01"))
           .andExpect(jsonPath("$.state.deps[0].id").value("D-01"))
           .andExpect(jsonPath("$.state.deps[0].desc").doesNotExist())
           .andExpect(jsonPath("$.state.rice[0].id").value("F-01"))
           .andExpect(jsonPath("$.state.calendar[0].date").value("2026-11-04"));

        // second PUT bumps the version
        mvc.perform(put("/api/state").contentType(MediaType.APPLICATION_JSON).content(STATE))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$.version").value(2));

        // per-entity REST resource
        mvc.perform(get("/api/tasks"))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$[0].id").value("T-01"))
           .andExpect(jsonPath("$[0].title").value("X"));
    }
}
