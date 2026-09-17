package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

/** Agile maturity self-assessment: a level (1–5) for one dimension of a framework (Scrum/Kanban/SAFe). */
@Entity
@Table(name = "agile_maturity")
@JsonIgnoreProperties(ignoreUnknown = true)
public class AgileMaturity {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "am_id") @JsonProperty("id") public String amId;
    public String framework;
    public String dimension;
    public Integer level;
    public String note;
    @JsonIgnore public Integer ord;
}
