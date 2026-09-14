package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

@Entity
@Table(name = "vacation")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Vacation {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "vac_id") @JsonProperty("id") public String vacId;
    public String member;
    @Column(name = "vtype") @JsonProperty("type") public String type;
    @Column(name = "dfrom") @JsonProperty("from") public String from;
    @Column(name = "dto") @JsonProperty("to") public String to;
    public Double days;
    public String status;
    public String notes;
    @JsonIgnore public Integer ord;
}
