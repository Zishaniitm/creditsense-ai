package com.creditsense.entity;

import jakarta.persistence.*;
import org.hibernate.annotations.CreationTimestamp;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "loan_applications")
public class LoanApplication {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "application_id", updatable = false)
    private UUID applicationId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(name = "loan_amount", nullable = false, precision = 15, scale = 2)
    private BigDecimal loanAmount;

    @Column(name = "loan_purpose", nullable = false, length = 100)
    private String loanPurpose;

    @Column(name = "loan_term_months", nullable = false)
    private Integer loanTermMonths;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private Status status = Status.SUBMITTED;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "reviewed_by")
    private User reviewedBy;

    @Column(name = "decision_notes", columnDefinition = "TEXT")
    private String decisionNotes;

    @CreationTimestamp
    @Column(name = "submitted_at", updatable = false)
    private LocalDateTime submittedAt;

    @Column(name = "reviewed_at")
    private LocalDateTime reviewedAt;

    @Column(name = "decision_at")
    private LocalDateTime decisionAt;

    @OneToOne(mappedBy = "application", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private ApplicantFinancials financials;

    @OneToOne(mappedBy = "application", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private CreditAssessment assessment;

    public enum Status {
        SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED
    }

    public LoanApplication() {}

    // Getters
    public UUID getApplicationId()          { return applicationId; }
    public User getUser()                   { return user; }
    public BigDecimal getLoanAmount()       { return loanAmount; }
    public String getLoanPurpose()          { return loanPurpose; }
    public Integer getLoanTermMonths()      { return loanTermMonths; }
    public Status getStatus()              { return status; }
    public User getReviewedBy()            { return reviewedBy; }
    public String getDecisionNotes()       { return decisionNotes; }
    public LocalDateTime getSubmittedAt()  { return submittedAt; }
    public LocalDateTime getReviewedAt()   { return reviewedAt; }
    public LocalDateTime getDecisionAt()   { return decisionAt; }
    public ApplicantFinancials getFinancials() { return financials; }
    public CreditAssessment getAssessment()    { return assessment; }

    // Setters
    public void setApplicationId(UUID v)        { this.applicationId = v; }
    public void setUser(User v)                 { this.user = v; }
    public void setLoanAmount(BigDecimal v)     { this.loanAmount = v; }
    public void setLoanPurpose(String v)        { this.loanPurpose = v; }
    public void setLoanTermMonths(Integer v)    { this.loanTermMonths = v; }
    public void setStatus(Status v)             { this.status = v; }
    public void setReviewedBy(User v)           { this.reviewedBy = v; }
    public void setDecisionNotes(String v)      { this.decisionNotes = v; }
    public void setSubmittedAt(LocalDateTime v) { this.submittedAt = v; }
    public void setReviewedAt(LocalDateTime v)  { this.reviewedAt = v; }
    public void setDecisionAt(LocalDateTime v)  { this.decisionAt = v; }
    public void setFinancials(ApplicantFinancials v) { this.financials = v; }
    public void setAssessment(CreditAssessment v)    { this.assessment = v; }

    // Builder
    public static Builder builder() { return new Builder(); }

    public static class Builder {
        private final LoanApplication obj = new LoanApplication();
        public Builder user(User v)              { obj.user = v; return this; }
        public Builder loanAmount(BigDecimal v)  { obj.loanAmount = v; return this; }
        public Builder loanPurpose(String v)     { obj.loanPurpose = v; return this; }
        public Builder loanTermMonths(Integer v) { obj.loanTermMonths = v; return this; }
        public Builder status(Status v)          { obj.status = v; return this; }
        public LoanApplication build()           { return obj; }
    }
}