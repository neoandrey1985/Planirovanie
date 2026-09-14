package com.planirovanie.repo;

import com.planirovanie.entity.Grooming;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface GroomingRepo extends JpaRepository<Grooming, Long> {
    List<Grooming> findAllByOrderByOrdAsc();
}
