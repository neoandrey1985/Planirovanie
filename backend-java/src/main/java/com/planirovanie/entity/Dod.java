package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;

@Entity
@Table(name = "dod")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Dod {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long id;
    public String crit;
    public Boolean done;
    @JsonIgnore public Integer ord;
}
