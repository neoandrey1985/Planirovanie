package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

@Entity
@Table(name = "mood")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Mood {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "mood_id") @JsonProperty("id") public String moodId;
    public Integer sprint;
    public Double mood;
    public String note;
    @JsonIgnore public Integer ord;
}
