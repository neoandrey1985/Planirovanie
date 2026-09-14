package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

@Entity
@Table(name = "radar")
@JsonIgnoreProperties(ignoreUnknown = true)
public class RadarAxis {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "radar_id") @JsonProperty("id") public String radarId;
    public String axis;
    public Double score;
    public Double prev;
    @JsonIgnore public Integer ord;
}
