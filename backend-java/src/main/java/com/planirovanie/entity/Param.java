package com.planirovanie.entity;

import jakarta.persistence.*;

/** Single-row configuration table. Mapped to params{}, budget{} and ttmTarget in the state DTO. */
@Entity
@Table(name = "params")
public class Param {
    @Id public Integer id;
    public String name;
    @Column(name = "start_date")  public String startDate;
    @Column(name = "sprint_days") public Integer sprintDays;
    public Double focus;
    @Column(name = "today_date")  public String todayDate;
    public String goal;
    public Integer sprints;
    @Column(name = "budget_rate")  public Double budgetRate;
    @Column(name = "budget_total") public Double budgetTotal;
    @Column(name = "ttm_target")   public Integer ttmTarget;
}
