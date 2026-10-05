package com.planirovanie.repo;

import com.planirovanie.entity.Decision;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface DecisionRepo extends JpaRepository<Decision, Long> {
    List<Decision> findAllByOrderByOrdAsc();
}
