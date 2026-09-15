package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

@Entity
@Table(name = "tasks")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Task {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "task_id") @JsonProperty("id") public String taskId;
    public String title;
    public String assignee;
    public String role;
    public String type;
    public Double est;
    public String status;
    public Integer sprint;
    public String dep;
    public String started;
    public String done;
    public Boolean added;
    @Column(name = "release_id") @JsonProperty("release") public String release;
    public String priority;
    public String dor;
    @JsonIgnore public Integer ord;
}
