package com.planirovanie.repo;

import com.planirovanie.entity.Okr;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface OkrRepo extends JpaRepository<Okr, Long> {
    List<Okr> findAllByOrderByOrdAsc();
}
