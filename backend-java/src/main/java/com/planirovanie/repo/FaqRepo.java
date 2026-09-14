package com.planirovanie.repo;

import com.planirovanie.entity.Faq;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface FaqRepo extends JpaRepository<Faq, Long> {
    List<Faq> findAllByOrderByOrdAsc();
}
