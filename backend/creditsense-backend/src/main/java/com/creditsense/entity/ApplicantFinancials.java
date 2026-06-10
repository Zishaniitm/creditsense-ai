package com.creditsense.entity;

import jakarta.persistence.*;
import org.hibernate.annotations.CreationTimestamp;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "applicant_financials")
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

    public ApplicantFinancials() {}

    // Getters
    public UUID getFinancialId()                    { return financialId; }
    public LoanApplication getApplication()         { return application; }
    public Integer getAge()                         { return age; }
    public BigDecimal getMonthlyIncome()            { return monthlyIncome; }
    public BigDecimal getDebtRatio()                { return debtRatio; }
    public BigDecimal getRevolvingUtilization()     { return revolvingUtilization; }
    public Integer getOpenCreditLines()             { return openCreditLines; }
    public Integer getRealEstateLoans()             { return realEstateLoans; }
    public Integer getNumDependents()               { return numDependents; }
    public Integer getLate3059Days()                { return late3059Days; }
    public Integer getLate6089Days()                { return late6089Days; }
    public Integer getLate90Days()                  { return late90Days; }
    public BigDecimal getDebtToIncomeRatio()        { return debtToIncomeRatio; }
    public BigDecimal getPaymentConsistencyScore()  { return paymentConsistencyScore; }
    public Integer getRevolvingUtilizationCat()     { return revolvingUtilizationCat; }
    public BigDecimal getLatePaymentFrequency()     { return latePaymentFrequency; }
    public Integer getIncomeStabilityFlag()         { return incomeStabilityFlag; }
    public LocalDateTime getCreatedAt()             { return createdAt; }

    // Setters
    public void setFinancialId(UUID v)                   { this.financialId = v; }
    public void setApplication(LoanApplication v)        { this.application = v; }
    public void setAge(Integer v)                        { this.age = v; }
    public void setMonthlyIncome(BigDecimal v)           { this.monthlyIncome = v; }
    public void setDebtRatio(BigDecimal v)               { this.debtRatio = v; }
    public void setRevolvingUtilization(BigDecimal v)    { this.revolvingUtilization = v; }
    public void setOpenCreditLines(Integer v)            { this.openCreditLines = v; }
    public void setRealEstateLoans(Integer v)            { this.realEstateLoans = v; }
    public void setNumDependents(Integer v)              { this.numDependents = v; }
    public void setLate3059Days(Integer v)               { this.late3059Days = v; }
    public void setLate6089Days(Integer v)               { this.late6089Days = v; }
    public void setLate90Days(Integer v)                 { this.late90Days = v; }
    public void setDebtToIncomeRatio(BigDecimal v)       { this.debtToIncomeRatio = v; }
    public void setPaymentConsistencyScore(BigDecimal v) { this.paymentConsistencyScore = v; }
    public void setRevolvingUtilizationCat(Integer v)    { this.revolvingUtilizationCat = v; }
    public void setLatePaymentFrequency(BigDecimal v)    { this.latePaymentFrequency = v; }
    public void setIncomeStabilityFlag(Integer v)        { this.incomeStabilityFlag = v; }

    // Builder
    public static Builder builder() { return new Builder(); }

    public static class Builder {
        private final ApplicantFinancials obj = new ApplicantFinancials();
        public Builder application(LoanApplication v)       { obj.application = v; return this; }
        public Builder age(Integer v)                       { obj.age = v; return this; }
        public Builder monthlyIncome(BigDecimal v)          { obj.monthlyIncome = v; return this; }
        public Builder debtRatio(BigDecimal v)              { obj.debtRatio = v; return this; }
        public Builder revolvingUtilization(BigDecimal v)   { obj.revolvingUtilization = v; return this; }
        public Builder openCreditLines(Integer v)           { obj.openCreditLines = v; return this; }
        public Builder realEstateLoans(Integer v)           { obj.realEstateLoans = v; return this; }
        public Builder numDependents(Integer v)             { obj.numDependents = v; return this; }
        public Builder late3059Days(Integer v)              { obj.late3059Days = v; return this; }
        public Builder late6089Days(Integer v)              { obj.late6089Days = v; return this; }
        public Builder late90Days(Integer v)                { obj.late90Days = v; return this; }
        public Builder debtToIncomeRatio(BigDecimal v)      { obj.debtToIncomeRatio = v; return this; }
        public Builder paymentConsistencyScore(BigDecimal v){ obj.paymentConsistencyScore = v; return this; }
        public Builder revolvingUtilizationCat(Integer v)   { obj.revolvingUtilizationCat = v; return this; }
        public Builder latePaymentFrequency(BigDecimal v)   { obj.latePaymentFrequency = v; return this; }
        public Builder incomeStabilityFlag(Integer v)       { obj.incomeStabilityFlag = v; return this; }
        public ApplicantFinancials build()                  { return obj; }
    }
}