package com.planirovanie.repo;

import com.planirovanie.entity.Issue;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface IssueRepo extends JpaRepository<Issue, Long> {
    List<Issue> findAllByOrderByOrdAsc();
}
