package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

@Entity
@Table(name = "rice")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Rice {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "rice_id") @JsonProperty("id") public String riceId;
    public String name;
    public Double reach;
    public Double impact;
    public String conf;
    public Double effort;
    @JsonIgnore public Integer ord;
}
