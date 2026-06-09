package com.creditsense.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "credit_assessments")
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class CreditAssessment {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "assessment_id", updatable = false)
    private UUID assessmentId;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "application_id", nullable = false, unique = true)
    private LoanApplication application;

    @Column(name = "risk_score", nullable = false, precision = 5, scale = 2)
    private BigDecimal riskScore;

    @Column(name = "risk_category", nullable = false, length = 10)
    private String riskCategory;

    @Column(nullable = false, precision = 5, scale = 4)
    private BigDecimal confidence;

    @Column(name = "model_version", nullable = false, length = 20)
    private String modelVersion;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "shap_explanation", columnDefinition = "jsonb")
    private String shapExplanation;

    @CreationTimestamp
    @Column(name = "assessed_at", updatable = false)
    private LocalDateTime assessedAt;
}