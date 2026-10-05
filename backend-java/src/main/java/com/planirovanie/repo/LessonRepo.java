package com.planirovanie.repo;

import com.planirovanie.entity.Lesson;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface LessonRepo extends JpaRepository<Lesson, Long> {
    List<Lesson> findAllByOrderByOrdAsc();
}
