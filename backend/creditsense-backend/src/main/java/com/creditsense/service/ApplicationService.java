package com.creditsense.service;

import com.creditsense.dto.request.LoanApplicationRequest;
import com.creditsense.dto.response.CreditScoreResponse;
import com.creditsense.entity.*;
import com.creditsense.repository.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.*;
import com.creditsense.service.CacheService;

@Service
public class ApplicationService {

    private static final Logger log = LoggerFactory.getLogger(ApplicationService.class);

    private final LoanApplicationRepository    applicationRepo;
    private final CreditAssessmentRepository   assessmentRepo;
    private final UserRepository               userRepo;
    private final MLService                    mlService;
    private final ObjectMapper                 objectMapper;
    private final CacheService                cacheService;

    public ApplicationService(LoanApplicationRepository applicationRepo,
                           CreditAssessmentRepository assessmentRepo,
                           UserRepository userRepo,
                           MLService mlService,
                           ObjectMapper objectMapper,
                           CacheService cacheService) {
    this.applicationRepo = applicationRepo;
    this.assessmentRepo  = assessmentRepo;
    this.userRepo        = userRepo;
    this.mlService       = mlService;
    this.objectMapper    = objectMapper;
    this.cacheService    = cacheService;
}

    /**
     * Submit a loan application, run ML scoring, persist everything.
     * Steps:
     *  1. Create LoanApplication record
     *  2. Create ApplicantFinancials record with raw + computed features
     *  3. Call Flask ML service for credit score + SHAP explanation
     *  4. Persist CreditAssessment result
     *  5. Update application status based on ML recommendation
     */
    @Transactional
    public Map<String, Object> submitApplication(LoanApplicationRequest request,
                                                  String userEmail) {
        // Load authenticated user
        User user = userRepo.findByEmail(userEmail)
                .orElseThrow(() -> new RuntimeException("User not found: " + userEmail));

        // 1. Create application
        LoanApplication app = LoanApplication.builder()
                .user(user)
                .loanAmount(request.getLoanAmount())
                .loanPurpose(request.getLoanPurpose())
                .loanTermMonths(request.getLoanTermMonths())
                .status(LoanApplication.Status.UNDER_REVIEW)
                .build();
        applicationRepo.save(app);
        log.info("Application created: {}", app.getApplicationId());

        // 2. Create financials
        ApplicantFinancials fin = buildFinancials(request, app);
        app.setFinancials(fin);
        applicationRepo.save(app);

        // 3. Call ML service
        CreditScoreResponse mlResult = mlService.scoreApplicant(fin);

        // 4. Persist assessment
        CreditAssessment assessment = persistAssessment(app, mlResult);

        // 5. Auto-set status based on recommendation
        LoanApplication.Status newStatus =
                "APPROVE".equals(mlResult.getRecommendation())
                ? LoanApplication.Status.APPROVED
                : LoanApplication.Status.UNDER_REVIEW;
        app.setStatus(newStatus);
        applicationRepo.save(app);

        log.info("Application {} scored: {} ({})",
                app.getApplicationId(),
                mlResult.getRiskScore(),
                mlResult.getRiskCategory());

        return buildApplicationResponse(app, fin, mlResult);
    }

    public Map<String, Object> getApplicationById(UUID applicationId,
                                               String userEmail) {
    // Check cache first
    Map<String, Object> cached = cacheService.get(applicationId.toString());
    if (cached != null) {
        return cached;
    }

    LoanApplication app = applicationRepo.findById(applicationId)
            .orElseThrow(() -> new RuntimeException(
                    "Application not found: " + applicationId));

    User user = userRepo.findByEmail(userEmail)
            .orElseThrow(() -> new RuntimeException("User not found"));

    if (user.getRole() == User.Role.APPLICANT &&
        !app.getUser().getUserId().equals(user.getUserId())) {
        throw new RuntimeException("Access denied to this application");
    }

    Optional<CreditAssessment> assessment =
            assessmentRepo.findByApplication(app);

    Map<String, Object> result = new HashMap<>();
    result.put("applicationId",  app.getApplicationId());
    result.put("status",         app.getStatus());
    result.put("loanAmount",     app.getLoanAmount());
    result.put("loanPurpose",    app.getLoanPurpose());
    result.put("submittedAt",    app.getSubmittedAt());

    assessment.ifPresent(a -> {
        result.put("riskScore",    a.getRiskScore());
        result.put("riskCategory", a.getRiskCategory());
        result.put("confidence",   a.getConfidence());
        result.put("modelVersion", a.getModelVersion());
        try {
            if (a.getShapExplanation() != null) {
                result.put("explanation",
                        objectMapper.readValue(a.getShapExplanation(), List.class));
            }
        } catch (Exception e) {
            log.warn("Could not parse SHAP explanation JSON");
        }
    });

    // Cache before returning
    cacheService.put(applicationId.toString(), result);

    return result;
}

    public Map<String, Object> updateDecision(UUID applicationId,
                                               String decision,
                                               String notes,
                                               String officerEmail) {
        LoanApplication app = applicationRepo.findById(applicationId)
                .orElseThrow(() -> new RuntimeException(
                        "Application not found: " + applicationId));

        User officer = userRepo.findByEmail(officerEmail)
                .orElseThrow(() -> new RuntimeException("Officer not found"));

        LoanApplication.Status newStatus =
                "APPROVE".equalsIgnoreCase(decision)
                ? LoanApplication.Status.APPROVED
                : LoanApplication.Status.REJECTED;

        app.setStatus(newStatus);
        app.setReviewedBy(officer);
        app.setDecisionNotes(notes);
        app.setReviewedAt(LocalDateTime.now());
        app.setDecisionAt(LocalDateTime.now());
        applicationRepo.save(app);
        cacheService.evict(applicationId.toString());   // Invalidate cache on update

        log.info("Application {} {} by {}", applicationId, newStatus, officerEmail);

        Map<String, Object> result = new HashMap<>();
        result.put("applicationId", app.getApplicationId());
        result.put("newStatus",     app.getStatus());
        result.put("reviewedBy",    officer.getEmail());
        result.put("decisionAt",    app.getDecisionAt());
        return result;
    }

    // ── Private helpers ──────────────────────────────────────────────────

    private ApplicantFinancials buildFinancials(LoanApplicationRequest req,
                                                 LoanApplication app) {
        double rev    = req.getRevolvingUtilization().doubleValue();
        int    late30 = req.getLate3059Days();
        int    late60 = req.getLate6089Days();
        int    late90 = req.getLate90Days();
        int    lines  = req.getOpenCreditLines();
        double income = req.getMonthlyIncome().doubleValue();
        double debt   = req.getDebtRatio().doubleValue();

        // Compute engineered features
        double dti = income > 0 ? Math.min(debt * income / income, 5.0) : 5.0;
        double weighted = late30 * 1.0 + late60 * 2.0 + late90 * 3.0;
        double maxD  = 10.0;
        double pcs   = Math.max(0, Math.min(100, (1 - weighted / maxD) * 100));
        int    ruc   = rev <= 0.30 ? 0 : rev <= 0.70 ? 1 : rev <= 1.0 ? 2 : 3;
        double lpf   = Math.min((late30 + late60 + late90) / (double)(lines + 1), 10.0);
        int    isf   = (income < 10000 && dti > 1.0) ? 1 : 0;

        return ApplicantFinancials.builder()
                .application(app)
                .age(req.getAge())
                .monthlyIncome(req.getMonthlyIncome())
                .debtRatio(req.getDebtRatio())
                .revolvingUtilization(req.getRevolvingUtilization())
                .openCreditLines(req.getOpenCreditLines())
                .realEstateLoans(req.getRealEstateLoans())
                .numDependents(req.getNumDependents())
                .late3059Days(req.getLate3059Days())
                .late6089Days(req.getLate6089Days())
                .late90Days(req.getLate90Days())
                .debtToIncomeRatio(BigDecimal.valueOf(dti).setScale(4, java.math.RoundingMode.HALF_UP))
                .paymentConsistencyScore(BigDecimal.valueOf(pcs).setScale(2, java.math.RoundingMode.HALF_UP))
                .revolvingUtilizationCat(ruc)
                .latePaymentFrequency(BigDecimal.valueOf(lpf).setScale(4, java.math.RoundingMode.HALF_UP))
                .incomeStabilityFlag(isf)
                .build();
    }

    private CreditAssessment persistAssessment(LoanApplication app,
                                                CreditScoreResponse ml) {
        String shapJson = "[]";
        if (ml.getExplanation() != null) {
            try { shapJson = objectMapper.writeValueAsString(ml.getExplanation()); }
            catch (Exception e) { log.warn("Could not serialize SHAP explanation"); }
        }

        CreditAssessment assessment = CreditAssessment.builder()
                .application(app)
                .riskScore(ml.getRiskScore() != null
        ? BigDecimal.valueOf(ml.getRiskScore()).setScale(2, java.math.RoundingMode.HALF_UP)
        : BigDecimal.ZERO)
                .riskCategory(ml.getRiskCategory())
                .confidence(ml.getConfidence() != null
                        ? BigDecimal.valueOf(ml.getConfidence()).setScale(4, java.math.RoundingMode.HALF_UP)
                        : BigDecimal.ZERO)
                .modelVersion(ml.getModelVersion() != null ? ml.getModelVersion() : "v1.0.0")
                .shapExplanation(shapJson)
                .build();

        return assessmentRepo.save(assessment);
    }

    private Map<String, Object> buildApplicationResponse(LoanApplication app,
                                                          ApplicantFinancials fin,
                                                          CreditScoreResponse ml) {
        Map<String, Object> resp = new HashMap<>();
        resp.put("applicationId",      app.getApplicationId());
        resp.put("status",             app.getStatus());
        resp.put("loanAmount",         app.getLoanAmount());
        resp.put("riskScore",          ml.getRiskScore());
        resp.put("riskCategory",       ml.getRiskCategory());
        resp.put("defaultProbability", ml.getDefaultProbability());
        resp.put("recommendation",     ml.getRecommendation());
        resp.put("explanation",        ml.getExplanation());
        resp.put("submittedAt",        app.getSubmittedAt());
        return resp;
    }
}