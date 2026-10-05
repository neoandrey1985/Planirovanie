package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

/** Planning-poker round: votes for a backlog item and the agreed estimate. */
@Entity
@Table(name = "poker")
@JsonIgnoreProperties(ignoreUnknown = true)
public class PokerRound {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "pk_id") @JsonProperty("id") public String pkId;
    public String task;
    public String title;
    @Column(columnDefinition = "text") public String votes;  // "Имя:значение, ..."
    public String result;      // согласованная оценка (SP)
    public String status;      // Открыт / Завершён
    @JsonIgnore public Integer ord;
}
