package com.planirovanie.repo;

import com.planirovanie.entity.Skill;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface SkillRepo extends JpaRepository<Skill, Long> {
    List<Skill> findAllByOrderByOrdAsc();
}
