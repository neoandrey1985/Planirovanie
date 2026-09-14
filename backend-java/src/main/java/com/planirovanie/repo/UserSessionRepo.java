package com.planirovanie.repo;

import com.planirovanie.entity.UserSession;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.Instant;

public interface UserSessionRepo extends JpaRepository<UserSession, String> {
    @Modifying
    @Query("delete from UserSession s where s.expiresAt < :now")
    int deleteExpired(@Param("now") Instant now);

    @Modifying
    @Query("delete from UserSession s where s.username = :username")
    int deleteByUsername(@Param("username") String username);
}
