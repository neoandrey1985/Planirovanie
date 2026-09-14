package com.planirovanie.repo;

import com.planirovanie.entity.Demo;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface DemoRepo extends JpaRepository<Demo, Long> {
    List<Demo> findAllByOrderByOrdAsc();
}
