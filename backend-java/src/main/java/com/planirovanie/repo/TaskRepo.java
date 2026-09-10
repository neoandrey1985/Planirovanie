package com.planirovanie.repo;

import com.planirovanie.entity.Task;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface TaskRepo extends JpaRepository<Task, Long> {
    List<Task> findAllByOrderByOrdAsc();
    Optional<Task> findByTaskId(String taskId);
}
