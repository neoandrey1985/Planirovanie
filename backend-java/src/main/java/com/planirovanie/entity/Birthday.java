package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

@Entity
@Table(name = "birthdays")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Birthday {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "bd_id") @JsonProperty("id") public String bdId;
    public String member;
    @Column(name = "bdate") @JsonProperty("date") public String date;
    public String role;
    public String notes;
    @JsonIgnore public Integer ord;
}
