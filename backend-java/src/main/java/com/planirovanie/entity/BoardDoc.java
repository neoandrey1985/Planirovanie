package com.planirovanie.entity;

import jakarta.persistence.*;

/** Whole whiteboard document (camera + items) stored as a JSON string in a single row. */
@Entity
@Table(name = "board_doc")
public class BoardDoc {
    @Id public Integer id;
    @Column(columnDefinition = "text") public String data;
}
