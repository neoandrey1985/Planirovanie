package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

/** Stakeholder register entry with power/interest and engagement levels. */
@Entity
@Table(name = "stakeholders")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Stakeholder {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "sk_id") @JsonProperty("id") public String skId;
    public String name;
    public String role;
    public Integer power;        // 1..5 влияние
    public Integer interest;     // 1..5 интерес
    @Column(name = "engage_cur") @JsonProperty("engageCur") public String engageCur;       // текущая вовлечённость
    @Column(name = "engage_target") @JsonProperty("engageTarget") public String engageTarget; // целевая
    public String strategy;
    @JsonIgnore public Integer ord;
}
