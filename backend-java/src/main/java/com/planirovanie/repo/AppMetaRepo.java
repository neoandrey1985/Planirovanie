package com.planirovanie.repo;

import com.planirovanie.entity.AppMeta;
import jakarta.persistence.LockModeType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;

import java.util.Optional;

public interface AppMetaRepo extends JpaRepository<AppMeta, Integer> {

    /** Row-locks the single version record so concurrent PUTs serialize on it. */
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select m from AppMeta m where m.id = 1")
    Optional<AppMeta> findForUpdate();
}
