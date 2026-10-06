package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

/** Production incident with recovery time and postmortem — feeds DORA (MTTR). */
@Entity
@Table(name = "incidents")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Incident {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "in_id") @JsonProperty("id") public String inId;
    public String date;
    public String title;
    public String severity;    // Critical / High / Medium / Low
    @Column(name = "down_hours") @JsonProperty("downHours") public Double downHours; // время восстановления, часы
    public String cause;
    public String status;      // Открыт / Восстановлен / Закрыт
    public String postmortem;
    @JsonIgnore public Integer ord;
}
