package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

/** Per-sprint goal and its achievement status (best practice: a commitment per sprint). */
@Entity
@Table(name = "sprint_goals")
@JsonIgnoreProperties(ignoreUnknown = true)
public class SprintGoal {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "sg_id") @JsonProperty("id") public String sgId;
    public Integer sprint;
    public String goal;
    public String status;
    @JsonIgnore public Integer ord;
}
