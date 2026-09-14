package com.planirovanie.repo;

import com.planirovanie.entity.RadarAxis;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface RadarRepo extends JpaRepository<RadarAxis, Long> {
    List<RadarAxis> findAllByOrderByOrdAsc();
}
