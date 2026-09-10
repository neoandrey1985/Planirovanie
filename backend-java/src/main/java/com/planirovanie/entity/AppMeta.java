package com.planirovanie.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "app_meta")
public class AppMeta {
    @Id public Integer id;
    public Long version;
}
