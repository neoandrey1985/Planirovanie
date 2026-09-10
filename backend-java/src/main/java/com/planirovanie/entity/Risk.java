package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;

@Entity
@Table(name = "risks")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Risk {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    public String name;
    public Integer p;
    public Integer i;
    public String mit;
    public String owner;
    public String status;
    @JsonIgnore public Integer ord;
}
