package com.planirovanie.repo;

import com.planirovanie.entity.Deployment;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface DeploymentRepo extends JpaRepository<Deployment, Long> {
    List<Deployment> findAllByOrderByOrdAsc();
}
