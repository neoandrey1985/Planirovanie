package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

/** Deployment event — feeds DORA (deployment frequency, lead time, change failure rate). */
@Entity
@Table(name = "deployments")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Deployment {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "dp_id") @JsonProperty("id") public String dpId;
    public String date;
    @Column(name = "release_id") @JsonProperty("release") public String release;
    public String env;         // Prod / Stage / Test
    public String status;      // Успех / Ошибка / Откат
    @Column(name = "lead_days") @JsonProperty("leadDays") public Double leadDays; // lead time for changes, дни
    public String note;
    @JsonIgnore public Integer ord;
}
