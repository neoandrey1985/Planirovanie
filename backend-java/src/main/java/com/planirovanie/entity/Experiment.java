package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

@Entity
@Table(name = "experiments")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Experiment {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "exp_id") @JsonProperty("id") public String expId;
    public Integer sprint;
    public String hypothesis;
    public String action;
    public String metric;
    public String result;
    public String status;
    @JsonIgnore public Integer ord;
}
