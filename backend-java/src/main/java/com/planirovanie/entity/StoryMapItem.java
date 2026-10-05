package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

/** Story-map cell: a story under a backbone activity, placed into a release band. */
@Entity
@Table(name = "story_map")
@JsonIgnoreProperties(ignoreUnknown = true)
public class StoryMapItem {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "sm_id") @JsonProperty("id") public String smId;
    public String activity;    // колонка (шаг пользовательского пути)
    @Column(name = "release_id") @JsonProperty("release") public String release; // полоса релиза
    public String story;
    public String task;        // необязательная связь с задачей
    @JsonIgnore public Integer ord;
}
