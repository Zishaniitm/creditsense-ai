package com.creditsense.repository;

import com.creditsense.entity.CreditAssessment;
import com.creditsense.entity.LoanApplication;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface CreditAssessmentRepository extends JpaRepository<CreditAssessment, UUID> {
    Optional<CreditAssessment> findByApplication(LoanApplication application);
}