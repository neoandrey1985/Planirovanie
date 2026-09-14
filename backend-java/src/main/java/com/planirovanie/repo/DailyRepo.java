package com.planirovanie.repo;

import com.planirovanie.entity.Daily;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface DailyRepo extends JpaRepository<Daily, Long> {
    List<Daily> findAllByOrderByOrdAsc();
}
