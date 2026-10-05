package com.planirovanie.repo;

import com.planirovanie.entity.ScopeLog;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ScopeLogRepo extends JpaRepository<ScopeLog, Long> {
    List<ScopeLog> findAllByOrderByOrdAsc();
}
