package com.planirovanie.repo;

import com.planirovanie.entity.Birthday;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface BirthdayRepo extends JpaRepository<Birthday, Long> {
    List<Birthday> findAllByOrderByOrdAsc();
}
