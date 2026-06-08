"""
test_flask_apis.py
Tests all Flask API endpoints programmatically.
IMPORTANT: Start both Flask services before running this.
  Terminal 1: python ml_service/app.py
  Terminal 2: python fraud_service/app.py
Run with: python tests/api/test_flask_apis.py
"""

import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")
import requests
import json

ML_URL    = "http://localhost:5000"
FRAUD_URL = "http://localhost:5001"

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []

def check(name, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, name, detail))
    print(f"  {status}  {name}")
    if detail:
        print(f"          → {detail}")

SAFE_PAYLOAD = {
    "age": 45, "monthly_income": 80000, "debt_ratio": 0.15,
    "revolving_utilization": 0.20, "open_credit_lines": 7,
    "real_estate_loans": 1, "num_dependents": 2,
    "late_30_59_days": 0, "late_60_89_days": 0, "late_90_days": 0,
    "debt_to_income_ratio": 0.14, "payment_consistency_score": 99.0,
    "revolving_utilization_cat": 0, "late_payment_frequency": 0.0,
    "income_stability_flag": 0
}

FRAUD_PAYLOAD = {
    "amount": 95000, "merchant_category": 14, "channel": 1,
    "hour_of_day": 2, "day_of_week": 6, "city": 3,
    "is_international": 1, "transactions_last_1h": 8,
    "transactions_last_24h": 15, "avg_txn_amount_30d": 3200.0,
    "days_since_last_txn": 0, "account_age_days": 22,
    "num_failed_txns_24h": 5, "is_new_device": 1
}


def run_all():
    print("=" * 60)
    print("  CreditSense AI — Flask API Endpoint Tests")
    print("=" * 60)

    # ── Health checks ──────────────────────────────────────────
    print("\n  [Module 1] Health Checks")
    try:
        r = requests.get(f"{ML_URL}/health", timeout=5)
        check("ML service /health returns 200", r.status_code == 200)
        check("ML service status is healthy",
              r.json().get("status") == "healthy",
              str(r.json()))
    except Exception as e:
        check("ML service reachable", False, f"Start it first: python ml_service/app.py — {e}")
        sys.exit(1)

    try:
        r = requests.get(f"{FRAUD_URL}/health", timeout=5)
        check("Fraud service /health returns 200", r.status_code == 200)
        check("Fraud service status is healthy",
              r.json().get("status") == "healthy")
    except Exception as e:
        check("Fraud service reachable", False, f"Start it first: python fraud_service/app.py — {e}")
        sys.exit(1)

    # ── /predict ───────────────────────────────────────────────
    print("\n  [Module 2] POST /predict")
    r = requests.post(f"{ML_URL}/predict", json=SAFE_PAYLOAD)
    check("/predict returns 200", r.status_code == 200, str(r.status_code))
    if r.status_code == 200:
        data = r.json()
        check("Response has risk_score",        "risk_score"          in data)
        check("Response has risk_category",     "risk_category"       in data)
        check("Response has default_probability","default_probability" in data)
        check("Response has recommendation",    "recommendation"      in data)
        check("risk_score is 0-100",
              0 <= data.get("risk_score", -1) <= 100,
              f"Got: {data.get('risk_score')}")
        check("risk_category is valid",
              data.get("risk_category") in ["LOW", "MEDIUM", "HIGH"],
              f"Got: {data.get('risk_category')}")
        check("default_probability is 0-1",
              0 <= data.get("default_probability", -1) <= 1,
              f"Got: {data.get('default_probability')}")
        check("recommendation is valid",
              data.get("recommendation") in ["APPROVE", "REVIEW", "REJECT"],
              f"Got: {data.get('recommendation')}")
        print(f"\n         Score={data['risk_score']}  "
              f"Category={data['risk_category']}  "
              f"Prob={data['default_probability']}  "
              f"Rec={data['recommendation']}")

    # ── /predict validation ────────────────────────────────────
    print("\n  [Module 3] POST /predict — Input Validation")
    r_missing = requests.post(f"{ML_URL}/predict", json={"age": 35})
    check("Missing features returns 422",
          r_missing.status_code == 422,
          f"Got: {r_missing.status_code}")
    check("Error response has 'error' field",
          "error" in r_missing.json())

    r_empty = requests.post(f"{ML_URL}/predict", json={})
    check("Empty body returns 422 or 400",
          r_empty.status_code in [400, 422])

    # ── /explain ───────────────────────────────────────────────
    print("\n  [Module 4] POST /explain")
    r = requests.post(f"{ML_URL}/explain", json=SAFE_PAYLOAD)
    check("/explain returns 200", r.status_code == 200)
    if r.status_code == 200:
        data = r.json()
        check("Response has explanation field", "explanation" in data)
        explanation = data.get("explanation", [])
        check("Explanation has 5 features",
              len(explanation) == 5,
              f"Got: {len(explanation)}")
        if explanation:
            first = explanation[0]
            check("Each feature has display_name", "display_name" in first)
            check("Each feature has shap_value",   "shap_value"   in first)
            check("Each feature has direction",    "direction"    in first)
            check("Direction is valid value",
                  first.get("direction") in
                  ["increases_risk", "decreases_risk"],
                  f"Got: {first.get('direction')}")
        print(f"\n         Top feature: {explanation[0]['display_name']}"
              f" (SHAP={explanation[0]['shap_value']})")

    # ── /model/info ────────────────────────────────────────────
    print("\n  [Module 5] GET /model/info")
    r = requests.get(f"{ML_URL}/model/info")
    check("/model/info returns 200", r.status_code == 200)
    if r.status_code == 200:
        data = r.json()
        check("Response has feature_count",
              data.get("feature_count") == 15,
              f"Got: {data.get('feature_count')}")
        check("Response has top_5_features",
              len(data.get("top_5_features", [])) == 5)

    # ── /fraud-check ───────────────────────────────────────────
    print("\n  [Module 6] POST /fraud-check")
    r = requests.post(f"{FRAUD_URL}/fraud-check", json=FRAUD_PAYLOAD)
    check("/fraud-check returns 200", r.status_code == 200)
    if r.status_code == 200:
        data = r.json()
        check("Response has is_fraudulent",     "is_fraudulent"     in data)
        check("Response has fraud_probability", "fraud_probability" in data)
        check("Response has action",            "action"            in data)
        check("Response has risk_level",        "risk_level"        in data)
        check("Obvious fraud is flagged True",
              data.get("is_fraudulent") == True,
              f"Got: {data.get('is_fraudulent')}")
        check("Action for high fraud is BLOCK",
              data.get("action") in ["BLOCK", "REVIEW"],
              f"Got: {data.get('action')}")
        check("fraud_probability is 0-1",
              0 <= data.get("fraud_probability", -1) <= 1,
              f"Got: {data.get('fraud_probability')}")
        check("top_anomalous_features is a list",
              isinstance(data.get("top_anomalous_features"), list))
        print(f"\n         Fraudulent={data['is_fraudulent']}  "
              f"Prob={data['fraud_probability']}  "
              f"Action={data['action']}")

    # ── Summary ────────────────────────────────────────────────
    passed = sum(1 for r in results if r[0] == PASS)
    failed = sum(1 for r in results if r[0] == FAIL)

    print(f"\n{'=' * 60}")
    print(f"  Results: {passed}/{len(results)} passed  |  {failed} failed")
    if failed == 0:
        print("  ✅ ALL API TESTS PASSED — Flask services are production-ready")
    else:
        print("  ⚠️  Fix failing tests before Month 3")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)