package com.planirovanie.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.persistence.Column;
import jakarta.persistence.Embeddable;

/**
 * A Kanban board filter, matching the front-end shape {@code {type, value}}.
 * {@code type} is one of: all, role, release, release-compose; {@code value} is the role name
 * for role boards (absent otherwise).
 */
@Embeddable
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public class BoardFilter {
    @Column(name = "filter_type") public String type;
    @Column(name = "filter_value") public String value;
}
