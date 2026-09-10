package com.planirovanie.repo;

import com.planirovanie.entity.TechDebt;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface TechDebtRepo extends JpaRepository<TechDebt, Long> {
    List<TechDebt> findAllByOrderByOrdAsc();
}
