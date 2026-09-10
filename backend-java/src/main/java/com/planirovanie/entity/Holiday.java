package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

@Entity
@Table(name = "calendar")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Holiday {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long id;
    @Column(name = "cdate") @JsonProperty("date") public String day;
    public String name;
    @JsonIgnore public Integer ord;
}
