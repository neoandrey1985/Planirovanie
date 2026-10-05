package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

import java.util.List;
import java.util.Map;

/**
 * A Kanban board definition, matching the front-end shape
 * {@code {id, name, filter:{type,value}, cols:[...]}}.
 */
@Entity
@Table(name = "boards")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Board {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "board_id") @JsonProperty("id") public String boardId;
    public String name;
    @Embedded public BoardFilter filter;
    @Convert(converter = ColsConverter.class)
    @Column(columnDefinition = "text")
    public List<String> cols;
    @Convert(converter = WipConverter.class)
    @Column(columnDefinition = "text")
    public Map<String, Integer> wip;   // per-column WIP limits
    @JsonIgnore public Integer ord;
}
