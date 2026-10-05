package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

/** RACI matrix row: responsibility assignment for an activity (R/A/C/I hold role or person names). */
@Entity
@Table(name = "raci")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Raci {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "ra_id") @JsonProperty("id") public String raId;
    public String activity;
    @Column(name = "resp") @JsonProperty("r") public String r;   // Responsible
    @Column(name = "acc")  @JsonProperty("a") public String a;   // Accountable
    @Column(name = "cons") @JsonProperty("c") public String c;   // Consulted
    @Column(name = "inf")  @JsonProperty("i") public String i;   // Informed
    @JsonIgnore public Integer ord;
}
