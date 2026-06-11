package com.creditsense.service;

import com.creditsense.dto.request.TransactionRequest;
import com.creditsense.dto.response.FraudCheckResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.HashMap;
import java.util.Map;

@Service
public class FraudService {

    private static final Logger log = LoggerFactory.getLogger(FraudService.class);
    private final WebClient fraudWebClient;

    public FraudService(@Qualifier("fraudWebClient") WebClient fraudWebClient) {
        this.fraudWebClient = fraudWebClient;
    }

    public FraudCheckResponse checkTransaction(TransactionRequest request) {
        Map<String, Object> payload = buildPayload(request);

        try {
            log.info("Calling fraud service /fraud-check, amount={}",
                    request.getAmount());

            FraudCheckResponse response = fraudWebClient.post()
                    .uri("/fraud-check")
                    .bodyValue(payload)
                    .retrieve()
                    .bodyToMono(FraudCheckResponse.class)
                    .block();

            log.info("Fraud check result: isFraudulent={}, action={}",
                    response.getIsFraudulent(), response.getAction());
            return response;

        } catch (WebClientResponseException e) {
            log.error("Fraud service error: {}", e.getMessage());
            throw new RuntimeException("Fraud service error: " + e.getMessage());
        } catch (Exception e) {
            log.error("Fraud service unreachable: {}", e.getMessage());
            throw new RuntimeException(
                "Fraud detection service unavailable. " +
                "Ensure fraud_service is running on port 5001.");
        }
    }

    private Map<String, Object> buildPayload(TransactionRequest r) {
        Map<String, Object> p = new HashMap<>();
        p.put("amount",                 r.getAmount());
        p.put("merchant_category",      r.getMerchantCategory() != null ? r.getMerchantCategory() : 0);
        p.put("channel",                r.getChannel() != null ? r.getChannel() : 0);
        p.put("hour_of_day",            r.getHourOfDay() != null ? r.getHourOfDay() : 12);
        p.put("day_of_week",            r.getDayOfWeek() != null ? r.getDayOfWeek() : 0);
        p.put("city",                   r.getCity() != null ? r.getCity() : 0);
        p.put("is_international",       r.getIsInternational() != null ? r.getIsInternational() : 0);
        p.put("transactions_last_1h",   r.getTransactionsLast1h() != null ? r.getTransactionsLast1h() : 0);
        p.put("transactions_last_24h",  r.getTransactionsLast24h() != null ? r.getTransactionsLast24h() : 0);
        p.put("avg_txn_amount_30d",     r.getAvgTxnAmount30d() != null ? r.getAvgTxnAmount30d() : 0.0);
        p.put("days_since_last_txn",    r.getDaysSinceLastTxn() != null ? r.getDaysSinceLastTxn() : 0);
        p.put("account_age_days",       r.getAccountAgeDays() != null ? r.getAccountAgeDays() : 365);
        p.put("num_failed_txns_24h",    r.getNumFailedTxns24h() != null ? r.getNumFailedTxns24h() : 0);
        p.put("is_new_device",          r.getIsNewDevice() != null ? r.getIsNewDevice() : 0);
        return p;
    }
}