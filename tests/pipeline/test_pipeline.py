"""
test_pipeline.py
Verifies the data pipeline output is correct and ML-ready.
Run with: python tests/pipeline/test_pipeline.py
"""


import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import numpy as np
import json
import os

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []

def check(name, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, name, detail))
    print(f"  {status}  {name}")
    if detail and not condition:
        print(f"          → {detail}")

def run_all():
    print("=" * 60)
    print("  CreditSense AI — Pipeline Integration Tests")
    print("=" * 60)

    # ── Test 1: Raw data exists ────────────────────────────────
    print("\n  [Module 1] Raw Data")
    check("credit_raw.csv exists",
          os.path.exists("data/raw/credit_raw.csv"))
    check("fraud_transactions.csv exists",
          os.path.exists("data/synthetic/fraud_transactions.csv"))

    # ── Test 2: Cleaned data ───────────────────────────────────
    print("\n  [Module 2] Cleaned Data")
    if os.path.exists("data/cleaned/credit_cleaned.csv"):
        df = pd.read_csv("data/cleaned/credit_cleaned.csv")
        check("No nulls in cleaned credit data",
              df.isnull().sum().sum() == 0,
              f"Found {df.isnull().sum().sum()} nulls")
        check("No duplicate rows",
              df.duplicated().sum() == 0,
              f"Found {df.duplicated().sum()} duplicates")
        check("Target column is binary (0/1)",
              set(df["target"].unique()).issubset({0, 1}),
              f"Unexpected values: {df['target'].unique()}")
        check("Age range valid (18-100)",
              df["age"].between(18, 100).all(),
              f"Min={df['age'].min()}, Max={df['age'].max()}")
        check("Monthly income non-negative",
              (df["monthly_income"] >= 0).all())
    else:
        check("credit_cleaned.csv exists", False, "File missing")

    # ── Test 3: Engineered features ────────────────────────────
    print("\n  [Module 3] Feature Engineering")
    if os.path.exists("data/engineered/credit_features.csv"):
        df = pd.read_csv("data/engineered/credit_features.csv")
        for feat in ["debt_to_income_ratio", "payment_consistency_score",
                     "revolving_utilization_cat", "late_payment_frequency",
                     "income_stability_flag"]:
            check(f"Feature '{feat}' exists", feat in df.columns)

        check("payment_consistency_score range (0-100)",
              df["payment_consistency_score"].between(0, 100).all(),
              f"Min={df['payment_consistency_score'].min():.2f}")
        check("revolving_utilization_cat values (0-3)",
              df["revolving_utilization_cat"].isin([0,1,2,3]).all())
        check("income_stability_flag is binary",
              df["income_stability_flag"].isin([0,1]).all())
        check("Row count matches cleaned data",
              len(df) == len(pd.read_csv("data/cleaned/credit_cleaned.csv")),
              f"Engineered: {len(df)}")
    else:
        check("credit_features.csv exists", False, "File missing")

    # ── Test 4: Logs exist ─────────────────────────────────────
    print("\n  [Module 4] Pipeline Logs")
    for log in ["cleaning_log.json", "encoding_log.json",
                "feature_engineering_log.json"]:
        path = f"pipeline/logs/{log}"
        check(f"{log} exists", os.path.exists(path))
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            check(f"{log} is valid JSON with content", len(data) > 0)

    # ── Test 5: Model files ────────────────────────────────────
    print("\n  [Module 5] Model Files")
    for fname in [
        "ml/models/credit_model_v1.0.0.joblib",
        "ml/models/credit_scaler_v1.0.0.joblib",
        "ml/models/shap_explainer_v1.0.0.joblib",
        "ml/models/fraud_model_v1.0.0.joblib",
        "ml/models/fraud_scaler_v1.0.0.joblib",
        "ml/models/label_encoders.joblib",
    ]:
        check(f"{os.path.basename(fname)} exists",
              os.path.exists(fname))
        if os.path.exists(fname):
            size_kb = os.path.getsize(fname) / 1024
            check(f"{os.path.basename(fname)} not empty (>{1}KB)",
                  size_kb > 1,
                  f"Size: {size_kb:.1f}KB")

    # ── Test 6: Evaluation outputs ─────────────────────────────
    print("\n  [Module 6] Evaluation Outputs")
    for fname in [
        "ml/evaluation/roc_curves.png",
        "ml/evaluation/shap_global_importance.png",
        "ml/evaluation/shap_beeswarm.png",
        "ml/evaluation/shap_feature_importance.json",
        "ml/evaluation/fraud_evaluation_charts.png",
        "ml/evaluation/fraud_model_report.json",
        "ml/evaluation/credit_model_meta_v1.0.0.json",
    ]:
        check(f"{os.path.basename(fname)} exists",
              os.path.exists(fname))

    # ── Summary ────────────────────────────────────────────────
    passed = sum(1 for r in results if r[0] == PASS)
    failed = sum(1 for r in results if r[0] == FAIL)
    total  = len(results)

    print(f"\n{'=' * 60}")
    print(f"  Results: {passed}/{total} passed  |  {failed} failed")
    if failed == 0:
        print("  ✅ ALL PIPELINE TESTS PASSED — safe to proceed to Month 3")
    else:
        print("  ⚠️  Fix failing tests before proceeding")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)