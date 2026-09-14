package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

@Entity
@Table(name = "daily")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Daily {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "daily_id") @JsonProperty("id") public String dailyId;
    @Column(name = "ddate") @JsonProperty("date") public String date;
    public Integer sprint;
    public String participant;
    public String yesterday;
    public String today;
    public String blocker;
    @JsonIgnore public Integer ord;
}
