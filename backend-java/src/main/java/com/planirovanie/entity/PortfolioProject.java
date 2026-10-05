package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

/** Portfolio entry: a summary snapshot of one project/initiative for the portfolio view. */
@Entity
@Table(name = "portfolio")
@JsonIgnoreProperties(ignoreUnknown = true)
public class PortfolioProject {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "po_id") @JsonProperty("id") public String poId;
    public String name;
    public String status;      // RAG: Зелёный / Жёлтый / Красный
    public Double health;      // 0..1
    public Double velocity;
    public Double budget;
    public Double spent;
    public Double progress;    // 0..1
    public String owner;
    public String note;
    @JsonIgnore public Integer ord;
}
