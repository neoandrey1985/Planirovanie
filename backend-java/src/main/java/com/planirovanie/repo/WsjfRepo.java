package com.planirovanie.repo;

import com.planirovanie.entity.Wsjf;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface WsjfRepo extends JpaRepository<Wsjf, Long> {
    List<Wsjf> findAllByOrderByOrdAsc();
}
