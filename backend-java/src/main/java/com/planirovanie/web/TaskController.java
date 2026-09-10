package com.planirovanie.web;

import com.planirovanie.entity.Task;
import com.planirovanie.repo.TaskRepo;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * Example of a proper per-entity REST resource on top of JPA.
 * The other collections follow the same pattern; the front-end itself uses /api/state.
 */
@RestController
@RequestMapping("/api/tasks")
public class TaskController {

    private final TaskRepo repo;

    public TaskController(TaskRepo repo) {
        this.repo = repo;
    }

    @GetMapping
    public List<Task> all() {
        return repo.findAllByOrderByOrdAsc();
    }

    @GetMapping("/{id}")
    public ResponseEntity<Task> one(@PathVariable String id) {
        return repo.findByTaskId(id).map(ResponseEntity::ok).orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    public Task create(@RequestBody Task t) {
        t.pk = null;
        t.ord = (int) repo.count();
        return repo.save(t);
    }

    @PutMapping("/{id}")
    public ResponseEntity<Task> update(@PathVariable String id, @RequestBody Task t) {
        return repo.findByTaskId(id).map(existing -> {
            t.pk = existing.pk;
            t.taskId = id;
            t.ord = existing.ord;
            return ResponseEntity.ok(repo.save(t));
        }).orElse(ResponseEntity.notFound().build());
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable String id) {
        return repo.findByTaskId(id).map(existing -> {
            repo.deleteById(existing.pk);
            return ResponseEntity.noContent().<Void>build();
        }).orElse(ResponseEntity.notFound().build());
    }
}
