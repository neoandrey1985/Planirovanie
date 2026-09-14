package com.planirovanie.repo;

import com.planirovanie.entity.Experiment;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface ExperimentRepo extends JpaRepository<Experiment, Long> {
    List<Experiment> findAllByOrderByOrdAsc();
}
