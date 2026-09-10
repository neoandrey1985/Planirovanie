package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

@Entity
@Table(name = "tech_debt")
@JsonIgnoreProperties(ignoreUnknown = true)
public class TechDebt {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "td_id") @JsonProperty("id") public String tdId;
    @Column(name = "descr") @JsonProperty("desc") public String descr;
    public String area;
    public String type;
    public String impact;
    public Double est;
    public String status;
    public Integer created;
    public Integer paid;
    @JsonIgnore public Integer ord;
}
