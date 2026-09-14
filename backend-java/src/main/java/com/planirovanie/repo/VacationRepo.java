package com.planirovanie.repo;

import com.planirovanie.entity.Vacation;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface VacationRepo extends JpaRepository<Vacation, Long> {
    List<Vacation> findAllByOrderByOrdAsc();
}
