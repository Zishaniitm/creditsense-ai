package com.creditsense.controller;

import com.creditsense.dto.response.ApiResponse;
import com.creditsense.repository.LoanApplicationRepository;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/analytics")
@Tag(name = "Analytics")
@SecurityRequirement(name = "bearerAuth")
public class AnalyticsController {

    private final LoanApplicationRepository applicationRepo;

    public AnalyticsController(LoanApplicationRepository applicationRepo) {
        this.applicationRepo = applicationRepo;
    }

    @GetMapping("/portfolio")
    @Operation(summary = "Portfolio summary — Admin only")
    public ResponseEntity<ApiResponse<Map<String, Object>>> portfolio() {
        long total    = applicationRepo.count();
        long approved = applicationRepo.countApproved();
        long rejected = applicationRepo.countRejected();
        Double avgScore = applicationRepo.avgRiskScore();

        Map<String, Object> stats = new HashMap<>();
        stats.put("totalApplications",  total);
        stats.put("approved",           approved);
        stats.put("rejected",           rejected);
        stats.put("underReview",        total - approved - rejected);
        stats.put("approvalRate",       total > 0
                ? Math.round((double) approved / total * 100 * 10) / 10.0 : 0);
        stats.put("averageRiskScore",   avgScore != null
                ? Math.round(avgScore * 100) / 100.0 : 0);

        return ResponseEntity.ok(ApiResponse.ok("Portfolio summary", stats));
    }
}