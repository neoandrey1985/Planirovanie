package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

/** Lessons-learned register entry: what happened, the lesson, and the recommendation. */
@Entity
@Table(name = "lessons")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Lesson {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "le_id") @JsonProperty("id") public String leId;
    public String date;
    public Integer sprint;
    public String category;    // Процесс / Технологии / Люди / Коммуникации / Качество
    public String context;
    @Column(name = "lesson_text") @JsonProperty("lesson") public String lesson;
    public String recommendation;
    @JsonIgnore public Integer ord;
}
