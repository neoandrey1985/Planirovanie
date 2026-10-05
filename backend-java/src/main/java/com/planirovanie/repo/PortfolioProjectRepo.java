package com.planirovanie.repo;

import com.planirovanie.entity.PortfolioProject;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface PortfolioProjectRepo extends JpaRepository<PortfolioProject, Long> {
    List<PortfolioProject> findAllByOrderByOrdAsc();
}
