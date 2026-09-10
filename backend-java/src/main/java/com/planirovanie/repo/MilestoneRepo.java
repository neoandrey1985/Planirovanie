package com.planirovanie.repo;

import com.planirovanie.entity.Milestone;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface MilestoneRepo extends JpaRepository<Milestone, Long> {
    List<Milestone> findAllByOrderByOrdAsc();
}
