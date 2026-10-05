package com.planirovanie.repo;

import com.planirovanie.entity.PokerRound;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface PokerRoundRepo extends JpaRepository<PokerRound, Long> {
    List<PokerRound> findAllByOrderByOrdAsc();
}
