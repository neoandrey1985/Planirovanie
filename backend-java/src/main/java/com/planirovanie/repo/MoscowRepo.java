package com.planirovanie.repo;

import com.planirovanie.entity.MoscowItem;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface MoscowRepo extends JpaRepository<MoscowItem, Long> {
    List<MoscowItem> findAllByOrderByOrdAsc();
}
