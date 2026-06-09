package com.creditsense.repository;

import com.creditsense.entity.LoanApplication;
import com.creditsense.entity.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface LoanApplicationRepository extends JpaRepository<LoanApplication, UUID> {
    List<LoanApplication> findByUser(User user);
    Page<LoanApplication> findAll(Pageable pageable);

    @Query("SELECT COUNT(a) FROM LoanApplication a WHERE a.status = 'APPROVED'")
    long countApproved();

    @Query("SELECT COUNT(a) FROM LoanApplication a WHERE a.status = 'REJECTED'")
    long countRejected();

    @Query("SELECT AVG(CAST(ca.riskScore AS double)) FROM CreditAssessment ca")
    Double avgRiskScore();
}