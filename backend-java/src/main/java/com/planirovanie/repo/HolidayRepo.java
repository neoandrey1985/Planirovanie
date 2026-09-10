package com.planirovanie.repo;

import com.planirovanie.entity.Holiday;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface HolidayRepo extends JpaRepository<Holiday, Long> {
    List<Holiday> findAllByOrderByOrdAsc();
}
