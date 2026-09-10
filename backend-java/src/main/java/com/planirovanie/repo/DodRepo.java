package com.planirovanie.repo;

import com.planirovanie.entity.Dod;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface DodRepo extends JpaRepository<Dod, Long> {
    List<Dod> findAllByOrderByOrdAsc();
}
