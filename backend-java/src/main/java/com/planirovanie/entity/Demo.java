package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

@Entity
@Table(name = "demo")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Demo {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "demo_id") @JsonProperty("id") public String demoId;
    public Integer sprint;
    @Column(name = "ddate") @JsonProperty("date") public String date;
    public String item;
    public String presenter;
    public String stakeholders;
    public String feedback;
    public String status;
    @JsonIgnore public Integer ord;
}
