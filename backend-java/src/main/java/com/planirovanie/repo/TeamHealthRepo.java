package com.planirovanie.repo;

import com.planirovanie.entity.TeamHealth;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface TeamHealthRepo extends JpaRepository<TeamHealth, Long> {
    List<TeamHealth> findAllByOrderByOrdAsc();
}
