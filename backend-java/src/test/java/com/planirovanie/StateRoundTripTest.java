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
          "skills":[{"id":"SK-01","member":"A","role":"Backend","skill":"API","level":4}],
          "agile":[{"id":"AM-01","framework":"Scrum","dimension":"Definition of Done","level":3,"note":"n"}],
          "tasks":[{"id":"T-01","title":"X","role":"Backend","type":"Задача","est":5,"status":"Готово","sprint":1,"release":"R-1","priority":"Must","dor":"Готова"}],
          "deps":[{"id":"D-01","item":"I","stream":"S","dir":"Мы зависим","status":"Заблокировано","task":"T-01"}],
          "rice":[{"id":"F-01","name":"R","reach":5000,"impact":3,"conf":"100%","effort":40}],
          "calendar":[{"date":"2026-11-04","name":"Праздник"}],
          "boards":[{"id":"b-all","name":"Все задачи","filter":{"type":"all"},"cols":["To Do","В работе","Готово"]},
                    {"id":"b-backend","name":"Backend","filter":{"type":"role","value":"Backend"},"cols":["To Do","В работе","Готово"]}],
          "board":{"cam":{"x":80,"y":80,"z":1.5},"items":[
             {"id":"bi1","t":"sticky","x":10,"y":20,"w":160,"h":140,"fill":"#FFE066","text":"Идея","author":"A","votes":2},
             {"id":"bi2","t":"conn","x1":0,"y1":0,"x2":90,"y2":0}]}
        }}""";

    /** Same state envelope with an explicit baseVersion for concurrency checks. */
    private static String withBase(long base) {
        return STATE.substring(0, STATE.length() - 1) + ",\"baseVersion\":" + base + "}";
    }

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
           .andExpect(jsonPath("$.state.skills[0].member").value("A"))
           .andExpect(jsonPath("$.state.skills[0].skill").value("API"))
           .andExpect(jsonPath("$.state.skills[0].level").value(4))
           .andExpect(jsonPath("$.state.agile[0].framework").value("Scrum"))
           .andExpect(jsonPath("$.state.agile[0].dimension").value("Definition of Done"))
           .andExpect(jsonPath("$.state.agile[0].level").value(3))
           .andExpect(jsonPath("$.state.tasks[0].id").value("T-01"))
           .andExpect(jsonPath("$.state.tasks[0].release").value("R-1"))
           .andExpect(jsonPath("$.state.tasks[0].priority").value("Must"))
           .andExpect(jsonPath("$.state.tasks[0].dor").value("Готова"))
           .andExpect(jsonPath("$.state.deps[0].id").value("D-01"))
           .andExpect(jsonPath("$.state.deps[0].desc").doesNotExist())
           .andExpect(jsonPath("$.state.rice[0].id").value("F-01"))
           .andExpect(jsonPath("$.state.calendar[0].date").value("2026-11-04"))
           .andExpect(jsonPath("$.state.boards[0].id").value("b-all"))
           .andExpect(jsonPath("$.state.boards[0].filter.type").value("all"))
           .andExpect(jsonPath("$.state.boards[1].filter.type").value("role"))
           .andExpect(jsonPath("$.state.boards[1].filter.value").value("Backend"))
           .andExpect(jsonPath("$.state.boards[1].cols[2]").value("Готово"))
           .andExpect(jsonPath("$.state.board.cam.z").value(1.5))
           .andExpect(jsonPath("$.state.board.items[0].t").value("sticky"))
           .andExpect(jsonPath("$.state.board.items[0].votes").value(2))
           .andExpect(jsonPath("$.state.board.items[1].t").value("conn"));

        // second PUT bumps the version (no baseVersion => backward-compatible, always accepted)
        mvc.perform(put("/api/state").contentType(MediaType.APPLICATION_JSON).content(STATE))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$.version").value(2));

        // optimistic concurrency: a stale baseVersion is rejected with 409 + current version and state
        mvc.perform(put("/api/state").contentType(MediaType.APPLICATION_JSON).content(withBase(1)))
           .andExpect(status().isConflict())
           .andExpect(jsonPath("$.error").value("version_conflict"))
           .andExpect(jsonPath("$.version").value(2))
           .andExpect(jsonPath("$.state.tasks[0].id").value("T-01"));

        // the correct baseVersion succeeds and bumps to 3
        mvc.perform(put("/api/state").contentType(MediaType.APPLICATION_JSON).content(withBase(2)))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$.version").value(3));

        // per-entity REST resource
        mvc.perform(get("/api/tasks"))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$[0].id").value("T-01"))
           .andExpect(jsonPath("$[0].title").value("X"));
    }
}
