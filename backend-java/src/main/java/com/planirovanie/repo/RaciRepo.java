package com.planirovanie.repo;

import com.planirovanie.entity.Raci;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface RaciRepo extends JpaRepository<Raci, Long> {
    List<Raci> findAllByOrderByOrdAsc();
}
