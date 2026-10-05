package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

/** Impediment log entry: an obstacle blocking the team, with aging and owner. */
@Entity
@Table(name = "impediments")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Impediment {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "im_id") @JsonProperty("id") public String imId;
    public String date;        // когда возник (ISO)
    public String title;
    public String owner;
    public String severity;    // High / Medium / Low
    public String status;      // Открыт / В работе / Снят
    public Integer sprint;
    public String resolved;    // когда снят (ISO)
    @JsonIgnore public Integer ord;
}
