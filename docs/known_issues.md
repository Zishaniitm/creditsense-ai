# CreditSense AI — Known Issues & Technical Debt

## Resolved
- [v1.1.0] Credit model calibration bias fixed with Platt Scaling
- [v1.0.1] Duplicate rows in credit_cleaned.csv fixed
- [v1.0.1] Database loader fixed with bulk insert + savepoints
- [v1.0.1] JSON snake_case/camelCase mapping fixed in Spring Boot

## Open — Planned for Post-Launch
- Kafka integration for full async transaction streaming (Month 4 partial)
- Model drift monitoring — alert if AUC drops below 0.82 on live data
- HTTPS/TLS setup on AWS EC2 (Month 4 deployment)
- Swagger authentication token persistence across page refresh
- Redis cluster mode for high availability (single node currently)

## Acknowledged Production Gaps (BCA Scope)
- No HSM for JWT secret management
- No PCI-DSS compliance layer
- No VAPT conducted
- Synthetic training data only — real NBFC data would improve AUC by ~3-5%

## [v1.2.0] Resolved — Payment Consistency Score SHAP Direction Bug
**Found:** During Week 13 frontend testing, SHAP explanations showed
payment_consistency_score=90 marked as "increases_risk" — contradicting
the feature's known -0.4151 correlation with default.

**Root cause:** XGBoost picked up a local non-monotonic pattern around
pcs=90 from training data sparsity after SMOTE oversampling. Confirmed
via diagnose_pcs_direction.py: SHAP value jumped from 0.5754 (pcs=75)
back up to 0.8359 (pcs=90) before dropping at pcs=100 — a real violation,
not noise.

**Fix:** Added monotone_constraints=-1 on payment_consistency_score in
XGBoost training (train_credit_model.py). Retrained as v1.2.0.

**Verification:** diagnose_pcs_direction.py now shows strictly monotonic
decrease across pcs=0→100 with no exceptions. Test AUC held at 0.8481
(vs 0.8497 in v1.1.0 — negligible cost). Operational recall at the real
0.25-0.40 decision thresholds remains 28-44%, confirmed via threshold
sweep persisted in credit_model_meta_v1.2.0.json. test_models.py updated
to check recall at the 0.30 operational threshold instead of the unused
0.5 generic cutoff — 17/17 tests passing.

## [v1.0.0] Final Release Status — All Critical Issues Resolved

| Issue | Status |
|---|---|
| Credit model calibration bias | ✅ Fixed v1.1.0 — Platt Scaling |
| SHAP direction bug (pcs=90) | ✅ Fixed v1.2.0 — monotonic constraint |
| Duplicate rows in training data | ✅ Fixed — pandas drop_duplicates |
| DB loader timeout (30min) | ✅ Fixed — bulk insert, chunksize=2000 |
| JSON snake_case mapping bug | ✅ Fixed — @JsonProperty annotations |
| Lombok annotation processor | ✅ Fixed — removed Lombok, plain Java |
| System Health showing Spring Boot offline | ✅ Fixed — actuator dependency |
| Auth page CORS silent failure | ✅ Fixed — api.js script tag added |
| Admin bcrypt hash corruption | ✅ Fixed — Python-direct DB update |
| payment_consistency_score SHAP non-monotonic | ✅ Fixed v1.2.0 |
