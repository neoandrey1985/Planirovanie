package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

@Entity
@Table(name = "faq")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Faq {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "faq_id") @JsonProperty("id") public String faqId;
    public String category;
    @Column(name = "question") @JsonProperty("q") public String q;
    @Column(name = "answer") @JsonProperty("a") public String a;
    @JsonIgnore public Integer ord;
}
