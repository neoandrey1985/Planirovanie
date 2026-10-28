package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;

/** Ishikawa (fishbone) category: a "bone" of the diagram (name, colour, which side of the spine). */
@Entity
@Table(name = "ishikawa_cats")
@JsonIgnoreProperties(ignoreUnknown = true)
public class IshikawaCat {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    public String name;
    public String color;               // hex colour of the bone
    public String side;                // "Сверху" / "Снизу" relative to the spine
    @JsonIgnore public Integer ord;
}
