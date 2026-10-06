package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

/** Team Health Check (Spotify Squad model) rating for one dimension in one period. */
@Entity
@Table(name = "team_health")
@JsonIgnoreProperties(ignoreUnknown = true)
public class TeamHealth {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "hc_id") @JsonProperty("id") public String hcId;
    public String date;
    public Integer sprint;
    public String dimension;   // измерение здоровья команды
    public String rating;      // Зелёный / Жёлтый / Красный
    public String trend;       // Растёт / Стабильно / Падает
    public String note;
    @JsonIgnore public Integer ord;
}
