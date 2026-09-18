package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;

@Entity
@Table(name = "team")
@JsonIgnoreProperties(ignoreUnknown = true)
public class TeamMember {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long id;
    public String name;
    public String role;
    public String scrum;      // additional "Scrum Master" role: "Да" when assigned, else empty
    public Double avail;
    public Double absent;
    @JsonIgnore public Integer ord;
}
