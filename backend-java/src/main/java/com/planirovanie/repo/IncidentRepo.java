package com.planirovanie.repo;

import com.planirovanie.entity.Incident;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface IncidentRepo extends JpaRepository<Incident, Long> {
    List<Incident> findAllByOrderByOrdAsc();
}
