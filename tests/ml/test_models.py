"""
test_models.py
Validates ML model outputs are correct, consistent, and within expected ranges.
Run with: python tests/ml/test_models.py
"""

import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import pandas as pd
import joblib
import json

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []

def check(name, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, name, detail))
    print(f"  {status}  {name}")
    if detail and not condition:
        print(f"          → {detail}")

FEATURE_COLS = [
    "age", "monthly_income", "debt_ratio", "revolving_utilization",
    "open_credit_lines", "real_estate_loans", "num_dependents",
    "late_30_59_days", "late_60_89_days", "late_90_days",
    "debt_to_income_ratio", "payment_consistency_score",
    "revolving_utilization_cat", "late_payment_frequency",
    "income_stability_flag"
]

FRAUD_FEATURES = [
    "amount", "merchant_category", "channel", "hour_of_day", "day_of_week",
    "city", "is_international", "transactions_last_1h", "transactions_last_24h",
    "avg_txn_amount_30d", "days_since_last_txn", "account_age_days",
    "num_failed_txns_24h", "is_new_device"
]

# Test applicants
SAFE_APPLICANT = {
    "age": 45, "monthly_income": 80000, "debt_ratio": 0.15,
    "revolving_utilization": 0.20, "open_credit_lines": 7,
    "real_estate_loans": 1, "num_dependents": 2,
    "late_30_59_days": 0, "late_60_89_days": 0, "late_90_days": 0,
    "debt_to_income_ratio": 0.14, "payment_consistency_score": 99.0,
    "revolving_utilization_cat": 0, "late_payment_frequency": 0.0,
    "income_stability_flag": 0
}

RISKY_APPLICANT = {
    "age": 28, "monthly_income": 12000, "debt_ratio": 0.85,
    "revolving_utilization": 0.95, "open_credit_lines": 2,
    "real_estate_loans": 0, "num_dependents": 3,
    "late_30_59_days": 5, "late_60_89_days": 4, "late_90_days": 6,
    "debt_to_income_ratio": 4.5, "payment_consistency_score": 5.0,
    "revolving_utilization_cat": 3, "late_payment_frequency": 7.5,
    "income_stability_flag": 1
}

NORMAL_TRANSACTION = {
    "amount": 2500, "merchant_category": 1, "channel": 0,
    "hour_of_day": 14, "day_of_week": 2, "city": 0,
    "is_international": 0, "transactions_last_1h": 1,
    "transactions_last_24h": 3, "avg_txn_amount_30d": 3000.0,
    "days_since_last_txn": 2, "account_age_days": 1200,
    "num_failed_txns_24h": 0, "is_new_device": 0
}

FRAUD_TRANSACTION = {
    "amount": 95000, "merchant_category": 14, "channel": 1,
    "hour_of_day": 2, "day_of_week": 6, "city": 3,
    "is_international": 1, "transactions_last_1h": 8,
    "transactions_last_24h": 15, "avg_txn_amount_30d": 3200.0,
    "days_since_last_txn": 0, "account_age_days": 22,
    "num_failed_txns_24h": 5, "is_new_device": 1
}


def run_all():
    print("=" * 60)
    print("  CreditSense AI — ML Model Validation Tests")
    print("=" * 60)

    # ── Load models ────────────────────────────────────────────
    print("\n  [Module 1] Model Loading")
    try:
        credit_model   = joblib.load("ml/models/credit_model_v1.0.0.joblib")
        credit_scaler  = joblib.load("ml/models/credit_scaler_v1.0.0.joblib")
        shap_explainer = joblib.load("ml/models/shap_explainer_v1.0.0.joblib")
        fraud_model    = joblib.load("ml/models/fraud_model_v1.0.0.joblib")
        fraud_scaler   = joblib.load("ml/models/fraud_scaler_v1.0.0.joblib")
        check("All 5 model files loaded without error", True)
    except Exception as e:
        check("All 5 model files loaded without error", False, str(e))
        sys.exit(1)

    # ── Credit model output shape ──────────────────────────────
    print("\n  [Module 2] Credit Model Output Validation")
    X_safe  = pd.DataFrame([SAFE_APPLICANT])[FEATURE_COLS]
    X_risky = pd.DataFrame([RISKY_APPLICANT])[FEATURE_COLS]

    prob_safe  = credit_model.predict_proba(X_safe)[0][1]
    prob_risky = credit_model.predict_proba(X_risky)[0][1]

    check("predict_proba returns value between 0 and 1",
          0 <= prob_safe <= 1 and 0 <= prob_risky <= 1,
          f"safe={prob_safe:.4f}, risky={prob_risky:.4f}")
    check("Risky applicant scores higher than safe applicant",
          prob_risky > prob_safe,
          f"safe={prob_safe:.4f}, risky={prob_risky:.4f}")
    check("Safe applicant default probability < 0.7",
          prob_safe < 0.7,
          f"Got: {prob_safe:.4f}")
    check("Risky applicant default probability > 0.5",
          prob_risky > 0.5,
          f"Got: {prob_risky:.4f}")

    print(f"\n         Safe applicant  → {prob_safe*100:.1f}% default prob")
    print(f"         Risky applicant → {prob_risky*100:.1f}% default prob")

    # ── SHAP output validation ─────────────────────────────────
    print("\n  [Module 3] SHAP Explainer Validation")
    shap_vals = shap_explainer.shap_values(X_safe)
    if hasattr(shap_vals, 'values'):
        sv = shap_vals.values[0]
    elif isinstance(shap_vals, list):
        sv = shap_vals[1][0] if len(shap_vals) > 1 else shap_vals[0][0]
    else:
        sv = shap_vals[0]

    check("SHAP returns values for all features",
          len(sv) == len(FEATURE_COLS),
          f"Got {len(sv)} values for {len(FEATURE_COLS)} features")
    check("SHAP values are finite numbers",
          all(np.isfinite(v) for v in sv))
    check("SHAP values are not all zero",
          not all(v == 0 for v in sv))

    # Feature importance JSON
    with open("ml/evaluation/shap_feature_importance.json") as f:
        importance = json.load(f)
    check("Feature importance JSON has all features",
          len(importance) == len(FEATURE_COLS),
          f"Expected {len(FEATURE_COLS)}, got {len(importance)}")
    check("Features ranked correctly (rank 1 = highest)",
          importance[0]["rank"] == 1)

    # ── Fraud model validation ─────────────────────────────────
    print("\n  [Module 4] Fraud Detection Model Validation")
    X_normal = pd.DataFrame([NORMAL_TRANSACTION])[FRAUD_FEATURES]
    X_fraud  = pd.DataFrame([FRAUD_TRANSACTION])[FRAUD_FEATURES]

    X_normal_sc = fraud_scaler.transform(X_normal)
    X_fraud_sc  = fraud_scaler.transform(X_fraud)

    score_normal = fraud_model.score_samples(X_normal_sc)[0]
    score_fraud  = fraud_model.score_samples(X_fraud_sc)[0]
    pred_fraud   = fraud_model.predict(X_fraud_sc)[0]

    check("Fraud transaction gets lower anomaly score than normal",
          score_fraud < score_normal,
          f"fraud={score_fraud:.4f}, normal={score_normal:.4f}")
    check("Obvious fraud transaction flagged as anomaly (-1)",
          pred_fraud == -1,
          f"Got prediction: {pred_fraud}")
    check("Anomaly scores are finite",
          np.isfinite(score_normal) and np.isfinite(score_fraud))

    print(f"\n         Normal transaction anomaly score : {score_normal:.4f}")
    print(f"         Fraud transaction anomaly score  : {score_fraud:.4f}")

    # ── Model metadata ─────────────────────────────────────────
    print("\n  [Module 5] Model Metadata")
    with open("ml/evaluation/credit_model_meta_v1.0.0.json") as f:
        meta = json.load(f)
    check("Credit model AUC-ROC >= 0.85",
          meta["test_metrics"]["auc_roc"] >= 0.85,
          f"Got: {meta['test_metrics']['auc_roc']}")
    check("Credit model recall >= 0.60",
          meta["test_metrics"]["recall"] >= 0.60,
          f"Got: {meta['test_metrics']['recall']}")

    with open("ml/evaluation/fraud_model_report.json") as f:
        fraud_meta = json.load(f)
    check("Fraud model recall >= 0.80",
          fraud_meta["test_metrics"]["recall"] >= 0.80,
          f"Got: {fraud_meta['test_metrics']['recall']}")
    check("Fraud model AUC-ROC >= 0.90",
          fraud_meta["test_metrics"]["auc_roc"] >= 0.90,
          f"Got: {fraud_meta['test_metrics']['auc_roc']}")

    # ── Summary ────────────────────────────────────────────────
    passed = sum(1 for r in results if r[0] == PASS)
    failed = sum(1 for r in results if r[0] == FAIL)

    print(f"\n{'=' * 60}")
    print(f"  Results: {passed}/{len(results)} passed  |  {failed} failed")
    if failed == 0:
        print("  ✅ ALL ML TESTS PASSED — models are production-ready")
    else:
        print("  ⚠️  Fix failing tests before proceeding to Month 3")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)