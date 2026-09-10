package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

@Entity
@Table(name = "bugs")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Bug {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "bug_id") @JsonProperty("id") public String bugId;
    @Column(name = "descr") @JsonProperty("desc") public String descr;
    public String task;
    public Integer sprint;
    public String sev;
    public String status;
    @Column(name = "time_h") @JsonProperty("time") public Double timeH;
    public Boolean reopened;
    public String cause;
    @JsonIgnore public Integer ord;
}
