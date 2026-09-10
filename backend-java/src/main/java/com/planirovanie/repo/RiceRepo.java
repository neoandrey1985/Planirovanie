package com.planirovanie.repo;

import com.planirovanie.entity.Rice;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface RiceRepo extends JpaRepository<Rice, Long> {
    List<Rice> findAllByOrderByOrdAsc();
}
