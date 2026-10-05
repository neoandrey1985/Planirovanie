package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

/** Issue log entry: a problem that has already occurred (vs a risk, which is potential). */
@Entity
@Table(name = "issues")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Issue {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "is_id") @JsonProperty("id") public String isId;
    public String date;
    public String title;
    public String priority;    // Critical / High / Medium / Low
    public String owner;
    public String status;      // Открыта / В работе / Решена / Закрыта
    public String due;
    public String resolution;
    @JsonIgnore public Integer ord;
}
