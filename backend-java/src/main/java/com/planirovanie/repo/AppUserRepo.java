package com.planirovanie.repo;

import com.planirovanie.entity.AppUser;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface AppUserRepo extends JpaRepository<AppUser, Long> {
    Optional<AppUser> findByUsername(String username);
    List<AppUser> findAllByOrderByUsernameAsc();
}
