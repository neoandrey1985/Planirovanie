package com.planirovanie.repo;

import com.planirovanie.entity.ChangeRequest;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ChangeRequestRepo extends JpaRepository<ChangeRequest, Long> {
    List<ChangeRequest> findAllByOrderByOrdAsc();
}
