package com.planirovanie.repo;

import com.planirovanie.entity.AgileMaturity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface AgileMaturityRepo extends JpaRepository<AgileMaturity, Long> {
    List<AgileMaturity> findAllByOrderByOrdAsc();
}
