package com.creditsense.dto.request;

import jakarta.validation.constraints.*;
import java.math.BigDecimal;

public class LoanApplicationRequest {

    @NotNull
    @Positive(message = "Loan amount must be positive")
    private BigDecimal loanAmount;

    @NotBlank(message = "Loan purpose is required")
    private String loanPurpose;

    @NotNull @Min(1) @Max(360)
    private Integer loanTermMonths;

    @NotNull @Min(18) @Max(100)
    private Integer age;

    @NotNull @PositiveOrZero
    private BigDecimal monthlyIncome;

    @NotNull @DecimalMin("0.0") @DecimalMax("100.0")
    private BigDecimal debtRatio;

    @NotNull @DecimalMin("0.0")
    private BigDecimal revolvingUtilization;

    @NotNull @PositiveOrZero
    private Integer openCreditLines;

    @NotNull @PositiveOrZero
    private Integer realEstateLoans;

    @NotNull @PositiveOrZero
    private Integer numDependents;

    @NotNull @PositiveOrZero
    private Integer late3059Days;

    @NotNull @PositiveOrZero
    private Integer late6089Days;

    @NotNull @PositiveOrZero
    private Integer late90Days;

    // Getters
    public BigDecimal getLoanAmount()        { return loanAmount; }
    public String getLoanPurpose()           { return loanPurpose; }
    public Integer getLoanTermMonths()       { return loanTermMonths; }
    public Integer getAge()                  { return age; }
    public BigDecimal getMonthlyIncome()     { return monthlyIncome; }
    public BigDecimal getDebtRatio()         { return debtRatio; }
    public BigDecimal getRevolvingUtilization() { return revolvingUtilization; }
    public Integer getOpenCreditLines()      { return openCreditLines; }
    public Integer getRealEstateLoans()      { return realEstateLoans; }
    public Integer getNumDependents()        { return numDependents; }
    public Integer getLate3059Days()         { return late3059Days; }
    public Integer getLate6089Days()         { return late6089Days; }
    public Integer getLate90Days()           { return late90Days; }

    // Setters
    public void setLoanAmount(BigDecimal v)        { this.loanAmount = v; }
    public void setLoanPurpose(String v)           { this.loanPurpose = v; }
    public void setLoanTermMonths(Integer v)       { this.loanTermMonths = v; }
    public void setAge(Integer v)                  { this.age = v; }
    public void setMonthlyIncome(BigDecimal v)     { this.monthlyIncome = v; }
    public void setDebtRatio(BigDecimal v)         { this.debtRatio = v; }
    public void setRevolvingUtilization(BigDecimal v) { this.revolvingUtilization = v; }
    public void setOpenCreditLines(Integer v)      { this.openCreditLines = v; }
    public void setRealEstateLoans(Integer v)      { this.realEstateLoans = v; }
    public void setNumDependents(Integer v)        { this.numDependents = v; }
    public void setLate3059Days(Integer v)         { this.late3059Days = v; }
    public void setLate6089Days(Integer v)         { this.late6089Days = v; }
    public void setLate90Days(Integer v)           { this.late90Days = v; }
}