package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

@Entity
@Table(name = "releases")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Release {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "rel_id") @JsonProperty("id") public String relId;
    public String name;
    public Integer sfrom;
    public Integer sto;
    public String status;
    @JsonIgnore public Integer ord;
}
