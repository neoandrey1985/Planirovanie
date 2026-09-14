package com.planirovanie.repo;

import com.planirovanie.entity.Kudos;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface KudosRepo extends JpaRepository<Kudos, Long> {
    List<Kudos> findAllByOrderByOrdAsc();
}
