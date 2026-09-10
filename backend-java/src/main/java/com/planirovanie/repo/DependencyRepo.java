package com.planirovanie.repo;

import com.planirovanie.entity.Dependency;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface DependencyRepo extends JpaRepository<Dependency, Long> {
    List<Dependency> findAllByOrderByOrdAsc();
}
