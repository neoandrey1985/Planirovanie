package com.planirovanie.repo;

import com.planirovanie.entity.StoryMapItem;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface StoryMapItemRepo extends JpaRepository<StoryMapItem, Long> {
    List<StoryMapItem> findAllByOrderByOrdAsc();
}
