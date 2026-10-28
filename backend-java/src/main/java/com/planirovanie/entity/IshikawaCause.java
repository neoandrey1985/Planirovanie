package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

/** Ishikawa (fishbone) cause: a cause of sprint schedule slippage, grouped under a category. */
@Entity
@Table(name = "ishikawa")
@JsonIgnoreProperties(ignoreUnknown = true)
public class IshikawaCause {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "ca_id") @JsonProperty("id") public String caId;
    public String cat;                 // category name (matches IshikawaCat.name)
    @Column(name = "cause_text") @JsonProperty("cause") public String cause;
    public Integer weight;             // 1..10 — relative contribution (Pareto)
    public String risk;                // optional: linked risk name (risks register)
    @JsonIgnore public Integer ord;
}
