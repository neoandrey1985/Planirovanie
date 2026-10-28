package com.planirovanie.repo;

import com.planirovanie.entity.IshikawaCat;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface IshikawaCatRepo extends JpaRepository<IshikawaCat, Long> {
    List<IshikawaCat> findAllByOrderByOrdAsc();
}
