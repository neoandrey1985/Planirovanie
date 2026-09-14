package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

@Entity
@Table(name = "kudos")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Kudos {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "kudos_id") @JsonProperty("id") public String kudosId;
    public Integer sprint;
    @Column(name = "from_who") @JsonProperty("from") public String from;
    @Column(name = "to_who") @JsonProperty("to") public String to;
    public String reason;
    @JsonIgnore public Integer ord;
}
