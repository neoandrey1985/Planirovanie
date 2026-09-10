package com.planirovanie.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.planirovanie.entity.*;
import java.util.List;

/** JSON transfer objects matching the front-end ST shape exactly. */
public final class Dtos {
    private Dtos() {}

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ParamsDto {
        public String name;
        public String start;
        public Integer sprintDays;
        public Double focus;
        public String today;
        public String goal;
        public Integer sprints;
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class BudgetDto {
        public Double rate;
        public Double total;
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class StateDto {
        public ParamsDto params;
        public List<Dod> dod;
        public List<TeamMember> team;
        public List<Task> tasks;
        public List<Release> releases;
        public List<Milestone> milestones;
        @JsonProperty("techDebt") public List<TechDebt> techDebt;
        public List<Risk> risks;
        public List<Bug> bugs;
        public List<Holiday> calendar;
        public List<Retro> retro;
        public List<Rice> rice;
        public List<Dependency> deps;
        public List<Okr> okr;
        public BudgetDto budget;
        public Integer ttmTarget;
    }

    /** PUT body is {"state": {...}, "baseVersion": N} — baseVersion enables optimistic concurrency. */
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class StateEnvelope {
        public StateDto state;
        public Long baseVersion;
    }

    public static class StateResponse {
        public long version;
        public StateDto state;
        public String updatedAt;
        public StateResponse(long version, StateDto state, String updatedAt) {
            this.version = version; this.state = state; this.updatedAt = updatedAt;
        }
    }

    public static class PutResponse {
        public long version;
        public String updatedAt;
        public PutResponse(long version, String updatedAt) {
            this.version = version; this.updatedAt = updatedAt;
        }
    }
}
