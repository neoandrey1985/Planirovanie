package com.planirovanie.repo;

import com.planirovanie.entity.BoardDoc;
import org.springframework.data.jpa.repository.JpaRepository;

public interface BoardDocRepo extends JpaRepository<BoardDoc, Integer> {
}
