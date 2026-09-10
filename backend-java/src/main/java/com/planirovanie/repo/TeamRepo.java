package com.planirovanie.repo;

import com.planirovanie.entity.TeamMember;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface TeamRepo extends JpaRepository<TeamMember, Long> {
    List<TeamMember> findAllByOrderByOrdAsc();
}
