package com.planirovanie.repo;

import com.planirovanie.entity.Stakeholder;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface StakeholderRepo extends JpaRepository<Stakeholder, Long> {
    List<Stakeholder> findAllByOrderByOrdAsc();
}
