package com.creditsense.dto.request;

import jakarta.validation.constraints.*;

public class TransactionRequest {

    @NotNull @Positive
    private Double amount;

    private Integer merchantCategory;
    private Integer channel;

    @Min(0) @Max(23)
    private Integer hourOfDay;

    @Min(0) @Max(6)
    private Integer dayOfWeek;

    private Integer city;
    private Integer isInternational;
    private Integer transactionsLast1h;
    private Integer transactionsLast24h;
    private Double avgTxnAmount30d;
    private Integer daysSinceLastTxn;
    private Integer accountAgeDays;
    private Integer numFailedTxns24h;
    private Integer isNewDevice;

    public Double getAmount()               { return amount; }
    public Integer getMerchantCategory()    { return merchantCategory; }
    public Integer getChannel()             { return channel; }
    public Integer getHourOfDay()           { return hourOfDay; }
    public Integer getDayOfWeek()           { return dayOfWeek; }
    public Integer getCity()                { return city; }
    public Integer getIsInternational()     { return isInternational; }
    public Integer getTransactionsLast1h()  { return transactionsLast1h; }
    public Integer getTransactionsLast24h() { return transactionsLast24h; }
    public Double getAvgTxnAmount30d()      { return avgTxnAmount30d; }
    public Integer getDaysSinceLastTxn()    { return daysSinceLastTxn; }
    public Integer getAccountAgeDays()      { return accountAgeDays; }
    public Integer getNumFailedTxns24h()    { return numFailedTxns24h; }
    public Integer getIsNewDevice()         { return isNewDevice; }

    public void setAmount(Double v)               { this.amount = v; }
    public void setMerchantCategory(Integer v)    { this.merchantCategory = v; }
    public void setChannel(Integer v)             { this.channel = v; }
    public void setHourOfDay(Integer v)           { this.hourOfDay = v; }
    public void setDayOfWeek(Integer v)           { this.dayOfWeek = v; }
    public void setCity(Integer v)                { this.city = v; }
    public void setIsInternational(Integer v)     { this.isInternational = v; }
    public void setTransactionsLast1h(Integer v)  { this.transactionsLast1h = v; }
    public void setTransactionsLast24h(Integer v) { this.transactionsLast24h = v; }
    public void setAvgTxnAmount30d(Double v)      { this.avgTxnAmount30d = v; }
    public void setDaysSinceLastTxn(Integer v)    { this.daysSinceLastTxn = v; }
    public void setAccountAgeDays(Integer v)      { this.accountAgeDays = v; }
    public void setNumFailedTxns24h(Integer v)    { this.numFailedTxns24h = v; }
    public void setIsNewDevice(Integer v)         { this.isNewDevice = v; }
}