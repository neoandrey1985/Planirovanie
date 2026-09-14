package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;

import java.time.Instant;

@Entity
@Table(name = "app_sessions")
@JsonIgnoreProperties(ignoreUnknown = true)
public class UserSession {
    @Id public String token;
    @Column(nullable = false) public String username;
    @Column(nullable = false) public String role;
    @Column(name = "created_at") public Instant createdAt;
    @Column(name = "expires_at") public Instant expiresAt;
}
