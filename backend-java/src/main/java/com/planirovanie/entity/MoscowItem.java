package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

@Entity
@Table(name = "moscow")
@JsonIgnoreProperties(ignoreUnknown = true)
public class MoscowItem {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "ms_id") @JsonProperty("id") public String msId;
    public String name;
    public String category;
    public String note;
    @JsonIgnore public Integer ord;
}
