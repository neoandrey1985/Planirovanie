package com.planirovanie.repo;

import com.planirovanie.entity.Param;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ParamRepo extends JpaRepository<Param, Integer> {
}
