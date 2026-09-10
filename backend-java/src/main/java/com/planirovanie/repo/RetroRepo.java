package com.planirovanie.repo;

import com.planirovanie.entity.Retro;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface RetroRepo extends JpaRepository<Retro, Long> {
    List<Retro> findAllByOrderByOrdAsc();
}
