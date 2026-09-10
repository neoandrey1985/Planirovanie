package com.planirovanie.repo;

import com.planirovanie.entity.Release;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface ReleaseRepo extends JpaRepository<Release, Long> {
    List<Release> findAllByOrderByOrdAsc();
}
