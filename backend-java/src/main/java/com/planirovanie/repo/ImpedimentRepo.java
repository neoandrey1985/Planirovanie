package com.planirovanie.repo;

import com.planirovanie.entity.Impediment;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ImpedimentRepo extends JpaRepository<Impediment, Long> {
    List<Impediment> findAllByOrderByOrdAsc();
}
