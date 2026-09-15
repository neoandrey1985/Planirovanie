package com.planirovanie.repo;

import com.planirovanie.entity.Board;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface BoardRepo extends JpaRepository<Board, Long> {
    List<Board> findAllByOrderByOrdAsc();
}
