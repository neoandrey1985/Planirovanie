package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

/** Star Map competency: a team member's skill level (1–5) for one competency of their role. */
@Entity
@Table(name = "skills")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Skill {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "sk_id") @JsonProperty("id") public String skillId;
    public String member;
    public String role;
    public String skill;
    public Integer level;
    @JsonIgnore public Integer ord;
}
