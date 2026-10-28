package com.planirovanie.repo;

import com.planirovanie.entity.IshikawaCause;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface IshikawaCauseRepo extends JpaRepository<IshikawaCause, Long> {
    List<IshikawaCause> findAllByOrderByOrdAsc();
}
