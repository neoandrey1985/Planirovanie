package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

/** Decision log / ADR entry: a recorded project or architecture decision with its rationale. */
@Entity
@Table(name = "decisions")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Decision {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "dc_id") @JsonProperty("id") public String dcId;
    public String date;
    public String title;
    public String context;
    public String options;
    @Column(name = "dec_text") @JsonProperty("decision") public String decision;
    public String rationale;
    public String owner;
    public String status;      // Предложено / Принято / Пересмотрено / Отменено
    @JsonIgnore public Integer ord;
}
