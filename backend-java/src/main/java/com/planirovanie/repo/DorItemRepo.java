package com.planirovanie.repo;

import com.planirovanie.entity.DorItem;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface DorItemRepo extends JpaRepository<DorItem, Long> {
    List<DorItem> findAllByOrderByOrdAsc();
}
