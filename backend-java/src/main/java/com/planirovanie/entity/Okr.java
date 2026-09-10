package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;

@Entity
@Table(name = "okr")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Okr {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long id;
    public String q;
    public String obj;
    public String kr;
    public Double target;
    public Double cur;
    @JsonIgnore public Integer ord;
}
