package com.planirovanie.repo;

import com.planirovanie.entity.SprintGoal;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface SprintGoalRepo extends JpaRepository<SprintGoal, Long> {
    List<SprintGoal> findAllByOrderByOrdAsc();
}
