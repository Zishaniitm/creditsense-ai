package com.creditsense.controller;

import com.creditsense.dto.request.TransactionRequest;
import com.creditsense.dto.response.ApiResponse;
import com.creditsense.dto.response.FraudCheckResponse;
import com.creditsense.service.FraudService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/transactions")
@Tag(name = "Transactions")
@SecurityRequirement(name = "bearerAuth")
public class TransactionController {

    private final FraudService fraudService;

    public TransactionController(FraudService fraudService) {
        this.fraudService = fraudService;
    }

    @PostMapping("/verify")
    @Operation(summary = "Submit a transaction for real-time fraud detection")
    public ResponseEntity<ApiResponse<FraudCheckResponse>> verify(
            @Valid @RequestBody TransactionRequest request) {
        FraudCheckResponse result = fraudService.checkTransaction(request);
        return ResponseEntity.ok(ApiResponse.ok("Fraud check complete", result));
    }
}