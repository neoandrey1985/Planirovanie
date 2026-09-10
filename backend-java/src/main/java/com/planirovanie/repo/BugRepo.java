package com.planirovanie.repo;

import com.planirovanie.entity.Bug;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface BugRepo extends JpaRepository<Bug, Long> {
    List<Bug> findAllByOrderByOrdAsc();
}
