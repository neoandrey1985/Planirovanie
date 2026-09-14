package com.planirovanie.repo;

import com.planirovanie.entity.Mood;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface MoodRepo extends JpaRepository<Mood, Long> {
    List<Mood> findAllByOrderByOrdAsc();
}
