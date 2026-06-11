package com.creditsense.controller;

import com.creditsense.dto.request.LoanApplicationRequest;
import com.creditsense.dto.response.ApiResponse;
import com.creditsense.service.ApplicationService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.*;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/applications")
@Tag(name = "Loan Applications")
@SecurityRequirement(name = "bearerAuth")
public class ApplicationController {

    private final ApplicationService applicationService;

    public ApplicationController(ApplicationService applicationService) {
        this.applicationService = applicationService;
    }

    @PostMapping
    @Operation(summary = "Submit a loan application — triggers ML credit scoring")
    public ResponseEntity<ApiResponse<Map<String, Object>>> submit(
            @Valid @RequestBody LoanApplicationRequest request,
            Authentication auth) {
        Map<String, Object> result =
                applicationService.submitApplication(request, auth.getName());
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.ok("Application submitted and scored", result));
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get application details with credit assessment")
    public ResponseEntity<ApiResponse<Map<String, Object>>> getById(
            @PathVariable UUID id,
            Authentication auth) {
        Map<String, Object> result =
                applicationService.getApplicationById(id, auth.getName());
        return ResponseEntity.ok(ApiResponse.ok("Application retrieved", result));
    }

    @PatchMapping("/{id}/decision")
    @Operation(summary = "Officer submits final decision — APPROVE or REJECT")
    public ResponseEntity<ApiResponse<Map<String, Object>>> decision(
            @PathVariable UUID id,
            @RequestParam String decision,
            @RequestParam(required = false) String notes,
            Authentication auth) {
        Map<String, Object> result =
                applicationService.updateDecision(id, decision, notes, auth.getName());
        return ResponseEntity.ok(ApiResponse.ok("Decision recorded", result));
    }
}