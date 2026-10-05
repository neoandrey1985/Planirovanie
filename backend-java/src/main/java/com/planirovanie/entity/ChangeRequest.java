package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

/** Change request (CCB): a formal request to change scope / schedule / cost / quality. */
@Entity
@Table(name = "change_requests")
@JsonIgnoreProperties(ignoreUnknown = true)
public class ChangeRequest {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) @JsonIgnore public Long pk;
    @Column(name = "cr_id") @JsonProperty("id") public String crId;
    public String date;
    public String title;
    public String type;        // Scope / Срок / Стоимость / Качество
    public String impact;      // оценка влияния
    public String requester;
    public String status;      // Предложен / Одобрен / Отклонён / Отложен / Внедрён
    public String note;
    @JsonIgnore public Integer ord;
}
