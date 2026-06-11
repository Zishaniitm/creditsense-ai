package com.creditsense.service;

import com.creditsense.dto.response.CreditScoreResponse;
import com.creditsense.entity.ApplicantFinancials;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.HashMap;
import java.util.Map;

/**
 * Calls the Python Flask ML service (port 5000).
 * Sends applicant financial features, receives risk score + SHAP explanation.
 *
 * Uses Spring WebClient for non-blocking HTTP.
 * Falls back gracefully if Flask service is unavailable.
 */
@Service
public class MLService {

    private static final Logger log = LoggerFactory.getLogger(MLService.class);
    private final WebClient mlWebClient;

    public MLService(@Qualifier("mlWebClient") WebClient mlWebClient) {
        this.mlWebClient = mlWebClient;
    }

    /**
     * Calls Flask /explain endpoint — returns score + SHAP top-5 features.
     * We use /explain (not /predict) so every assessment includes explainability.
     */
    public CreditScoreResponse scoreApplicant(ApplicantFinancials fin) {
        Map<String, Object> payload = buildFeaturePayload(fin);

        try {
            log.info("Calling ML service /explain for applicant financials");

            CreditScoreResponse response = mlWebClient.post()
                    .uri("/explain")
                    .bodyValue(payload)
                    .retrieve()
                    .bodyToMono(CreditScoreResponse.class)
                    .block();   // blocking call — acceptable for v1.0

            log.info("ML service responded: score={}, category={}",
                    response.getRiskScore(), response.getRiskCategory());
            return response;

        } catch (WebClientResponseException e) {
            log.error("ML service error: {} {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new RuntimeException("ML scoring service returned error: " + e.getMessage());
        } catch (Exception e) {
            log.error("ML service unreachable: {}", e.getMessage());
            throw new RuntimeException(
                "ML scoring service is unavailable. " +
                "Ensure ml_service is running on port 5000.");
        }
    }

    /**
     * Builds the feature payload the Flask /explain endpoint expects.
     * Must match FEATURE_COLS order defined in ml_service/app.py exactly.
     */
    private Map<String, Object> buildFeaturePayload(ApplicantFinancials fin) {
        Map<String, Object> payload = new HashMap<>();

        // Raw features
        payload.put("age",                    fin.getAge());
        payload.put("monthly_income",         fin.getMonthlyIncome().doubleValue());
        payload.put("debt_ratio",             fin.getDebtRatio().doubleValue());
        payload.put("revolving_utilization",  fin.getRevolvingUtilization().doubleValue());
        payload.put("open_credit_lines",      fin.getOpenCreditLines());
        payload.put("real_estate_loans",      fin.getRealEstateLoans());
        payload.put("num_dependents",         fin.getNumDependents());
        payload.put("late_30_59_days",        fin.getLate3059Days());
        payload.put("late_60_89_days",        fin.getLate6089Days());
        payload.put("late_90_days",           fin.getLate90Days());

        // Engineered features — compute from raw if not stored
        double dti = fin.getDebtToIncomeRatio() != null
                ? fin.getDebtToIncomeRatio().doubleValue()
                : computeDTI(fin);
        double pcs = fin.getPaymentConsistencyScore() != null
                ? fin.getPaymentConsistencyScore().doubleValue()
                : 100.0;
        int ruc = fin.getRevolvingUtilizationCat() != null
                ? fin.getRevolvingUtilizationCat()
                : categorizeUtil(fin.getRevolvingUtilization().doubleValue());
        double lpf = fin.getLatePaymentFrequency() != null
                ? fin.getLatePaymentFrequency().doubleValue()
                : 0.0;
        int isf = fin.getIncomeStabilityFlag() != null
                ? fin.getIncomeStabilityFlag() : 0;

        payload.put("debt_to_income_ratio",       dti);
        payload.put("payment_consistency_score",  pcs);
        payload.put("revolving_utilization_cat",  ruc);
        payload.put("late_payment_frequency",     lpf);
        payload.put("income_stability_flag",      isf);

        return payload;
    }

    private double computeDTI(ApplicantFinancials fin) {
        double income = fin.getMonthlyIncome().doubleValue();
        if (income <= 0) return 5.0;
        return Math.min(fin.getDebtRatio().doubleValue(), 5.0);
    }

    private int categorizeUtil(double util) {
        if (util <= 0.30) return 0;
        if (util <= 0.70) return 1;
        if (util <= 1.00) return 2;
        return 3;
    }
}