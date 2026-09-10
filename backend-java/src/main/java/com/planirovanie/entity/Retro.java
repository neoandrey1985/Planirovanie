package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;

@Entity
@Table(name = "retro")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Retro {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long id;
    public Integer sprint;
    public String well;
    public String improve;
    public String action;
    public String owner;
    public String due;
    public String status;
    @JsonIgnore public Integer ord;
}
