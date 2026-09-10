package com.planirovanie.repo;

import com.planirovanie.entity.Risk;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface RiskRepo extends JpaRepository<Risk, Long> {
    List<Risk> findAllByOrderByOrdAsc();
}
