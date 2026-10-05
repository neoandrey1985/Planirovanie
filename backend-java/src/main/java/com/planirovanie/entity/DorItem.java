package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;

/** Definition of Ready checklist item (template), analogous to {@link Dod}. */
@Entity
@Table(name = "dor_items")
@JsonIgnoreProperties(ignoreUnknown = true)
public class DorItem {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long id;
    public String crit;
    public Boolean done;
    @JsonIgnore public Integer ord;
}
