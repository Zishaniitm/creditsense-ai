package com.creditsense.entity;

import jakarta.persistence.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "credit_assessments")
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

    public CreditAssessment() {}

    // Getters
    public UUID getAssessmentId()        { return assessmentId; }
    public LoanApplication getApplication() { return application; }
    public BigDecimal getRiskScore()     { return riskScore; }
    public String getRiskCategory()      { return riskCategory; }
    public BigDecimal getConfidence()    { return confidence; }
    public String getModelVersion()      { return modelVersion; }
    public String getShapExplanation()   { return shapExplanation; }
    public LocalDateTime getAssessedAt() { return assessedAt; }

    // Setters
    public void setAssessmentId(UUID v)           { this.assessmentId = v; }
    public void setApplication(LoanApplication v) { this.application = v; }
    public void setRiskScore(BigDecimal v)        { this.riskScore = v; }
    public void setRiskCategory(String v)         { this.riskCategory = v; }
    public void setConfidence(BigDecimal v)       { this.confidence = v; }
    public void setModelVersion(String v)         { this.modelVersion = v; }
    public void setShapExplanation(String v)      { this.shapExplanation = v; }
    public void setAssessedAt(LocalDateTime v)    { this.assessedAt = v; }

    // Builder
    public static Builder builder() { return new Builder(); }

    public static class Builder {
        private final CreditAssessment obj = new CreditAssessment();
        public Builder application(LoanApplication v) { obj.application = v; return this; }
        public Builder riskScore(BigDecimal v)        { obj.riskScore = v; return this; }
        public Builder riskCategory(String v)         { obj.riskCategory = v; return this; }
        public Builder confidence(BigDecimal v)       { obj.confidence = v; return this; }
        public Builder modelVersion(String v)         { obj.modelVersion = v; return this; }
        public Builder shapExplanation(String v)      { obj.shapExplanation = v; return this; }
        public CreditAssessment build()               { return obj; }
    }
}