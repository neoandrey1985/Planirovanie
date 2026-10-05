package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

/** Scope-creep log entry: a recorded change to the composition of a sprint or release. */
@Entity
@Table(name = "scope_log")
@JsonIgnoreProperties(ignoreUnknown = true)
public class ScopeLog {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "sc_id") @JsonProperty("id") public String scId;
    public String date;
    public Integer sprint;
    @Column(name = "release_id") @JsonProperty("release") public String release;
    public String kind;      // Добавлено / Убрано / Перенесено
    public String item;      // task id or name
    public String detail;
    @JsonIgnore public Integer ord;
}
