package com.creditsense.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "applicant_financials")
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class ApplicantFinancials {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "financial_id", updatable = false)
    private UUID financialId;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "application_id", nullable = false, unique = true)
    private LoanApplication application;

    @Column(nullable = false)
    private Integer age;

    @Column(name = "monthly_income", nullable = false, precision = 12, scale = 2)
    private BigDecimal monthlyIncome;

    @Column(name = "debt_ratio", precision = 8, scale = 4)
    private BigDecimal debtRatio;

    @Column(name = "revolving_utilization", precision = 8, scale = 4)
    private BigDecimal revolvingUtilization;

    @Column(name = "open_credit_lines")
    private Integer openCreditLines;

    @Column(name = "real_estate_loans")
    private Integer realEstateLoans;

    @Column(name = "num_dependents")
    private Integer numDependents;

    @Column(name = "late_30_59_days")
    private Integer late3059Days;

    @Column(name = "late_60_89_days")
    private Integer late6089Days;

    @Column(name = "late_90_days")
    private Integer late90Days;

    // Engineered features
    @Column(name = "debt_to_income_ratio", precision = 8, scale = 4)
    private BigDecimal debtToIncomeRatio;

    @Column(name = "payment_consistency_score", precision = 6, scale = 2)
    private BigDecimal paymentConsistencyScore;

    @Column(name = "revolving_utilization_cat")
    private Integer revolvingUtilizationCat;

    @Column(name = "late_payment_frequency", precision = 8, scale = 4)
    private BigDecimal latePaymentFrequency;

    @Column(name = "income_stability_flag")
    private Integer incomeStabilityFlag;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;
}