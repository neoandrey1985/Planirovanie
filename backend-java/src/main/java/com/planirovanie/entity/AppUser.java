package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;

import java.time.Instant;

@Entity
@Table(name = "app_users")
@JsonIgnoreProperties(ignoreUnknown = true)
public class AppUser {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(nullable = false, unique = true) public String username;
    @Column(name = "pass_hash", nullable = false) @JsonIgnore public String passHash;
    @Column(nullable = false) public String role;              // VIEWER | EDITOR | ADMIN
    @Column(name = "display_name") public String displayName;
    @Column(nullable = false) public boolean active = true;
    @Column(name = "created_at") public Instant createdAt;
}
