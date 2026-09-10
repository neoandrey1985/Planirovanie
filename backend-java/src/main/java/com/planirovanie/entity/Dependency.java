package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

@Entity
@Table(name = "deps")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Dependency {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "dep_id") @JsonProperty("id") public String depId;
    public String item;
    public String type;
    public String task;
    public String stream;
    public String dir;
    @Column(name = "descr") @JsonProperty("desc") public String descr;
    public Integer sprint;
    public String status;
    public String owner;
    public String risk;
    @JsonIgnore public Integer ord;
}
