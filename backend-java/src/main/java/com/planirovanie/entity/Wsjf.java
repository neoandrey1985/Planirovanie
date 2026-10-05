package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

/** WSJF prioritization (SAFe): score = Cost of Delay (bv + tc + rr) / Job Size. */
@Entity
@Table(name = "wsjf")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Wsjf {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "w_id") @JsonProperty("id") public String wId;
    public String task;
    public String name;
    public Integer bv;        // user-business value
    public Integer tc;        // time criticality
    public Integer rr;        // risk reduction / opportunity enablement
    @Column(name = "job_size") public Double jobSize;
    @JsonIgnore public Integer ord;
}
