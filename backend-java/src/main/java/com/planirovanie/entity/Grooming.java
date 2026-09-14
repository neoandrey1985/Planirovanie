package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

@Entity
@Table(name = "grooming")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Grooming {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "grm_id") @JsonProperty("id") public String grmId;
    @Column(name = "gdate") @JsonProperty("date") public String date;
    public String item;
    public String action;
    public Double est;
    public String ready;
    public String owner;
    public String notes;
    @JsonIgnore public Integer ord;
}
