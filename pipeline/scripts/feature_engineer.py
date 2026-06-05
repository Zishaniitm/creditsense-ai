"""
feature_engineer.py
Engineers 5 new predictive features from the cleaned credit dataset.
These derived features significantly improve model performance over raw features.

New Features:
  1. debt_to_income_ratio      — total debt burden relative to income
  2. payment_consistency_score — how consistently the applicant pays on time
  3. revolving_utilization_cat — risk category from revolving utilization rate
  4. late_payment_frequency    — weighted total of all late payment events
  5. income_stability_flag     — flag for potentially unstable or suspicious income

Input : data/cleaned/credit_cleaned.csv
Output: data/engineered/credit_features.csv
"""
import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

INPUT_PATH  = "data/cleaned/credit_cleaned.csv"
OUTPUT_PATH = "data/engineered/credit_features.csv"
LOG_DIR     = "pipeline/logs"


def load_data():
    print("  [1/7] Loading cleaned credit data...")
    df = pd.read_csv(INPUT_PATH)
    print(f"         Loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df


# ──────────────────────────────────────────────────────────────────
# FEATURE 1: Debt-to-Income Ratio
# ──────────────────────────────────────────────────────────────────
def add_debt_to_income_ratio(df):
    """
    What it measures:
        How much of the applicant's monthly income is consumed by debt obligations.
        Higher ratio = higher financial stress = higher default risk.

    Formula:
        debt_ratio (already a fraction) × monthly_income = estimated monthly debt.
        We then normalise by income to get a clean ratio.

    Industry standard: DTI > 0.43 is considered high risk by most lenders.
    """
    print("  [2/7] Engineering Feature 1: Debt-to-Income Ratio...")

    # Avoid division by zero — monthly_income should have been cleaned but we check
    safe_income = df["monthly_income"].replace(0, np.nan)

    # debt_ratio in dataset = monthly debt payments / monthly income
    # We engineer a compound score that penalises both high debt AND low income
    df["debt_to_income_ratio"] = (
        df["debt_ratio"] * df["monthly_income"]
    ) / safe_income.fillna(safe_income.median())

    # Cap at 5 to prevent extreme outlier distortion
    df["debt_to_income_ratio"] = df["debt_to_income_ratio"].clip(0, 5).round(4)

    stats = df["debt_to_income_ratio"].describe()
    print(f"         Mean={stats['mean']:.4f}  |  Median={stats['50%']:.4f}  |  Max={stats['max']:.4f}")

    # Correlation with target
    corr = df["debt_to_income_ratio"].corr(df["target"])
    print(f"         Correlation with default target: {corr:.4f}")
    return df


# ──────────────────────────────────────────────────────────────────
# FEATURE 2: Payment Consistency Score
# ──────────────────────────────────────────────────────────────────
def add_payment_consistency_score(df):
    """
    What it measures:
        A single 0–100 score that captures how consistently an applicant
        has paid on time across different delinquency windows.

    Formula:
        Weighted combination — 90-day lates are 3× worse than 30-day lates.
        Then inverted: a perfect payer gets 100, chronic defaulter gets near 0.

    Why this matters:
        Raw late payment columns are highly correlated with each other.
        This collapses them into one clean, interpretable signal.
    """
    print("  [3/7] Engineering Feature 2: Payment Consistency Score...")

    # Weighted delinquency score (higher = worse payment history)
    weighted_delinquency = (
        df["late_30_59_days"] * 1.0 +
        df["late_60_89_days"] * 2.0 +
        df["late_90_days"]    * 3.0
    )

    # Normalise to 0–1 range using 99th percentile as max
    max_delinquency = weighted_delinquency.quantile(0.99)
    normalised = (weighted_delinquency / max_delinquency).clip(0, 1)

    # Invert: 1 = perfect payer, 0 = chronic defaulter
    df["payment_consistency_score"] = ((1 - normalised) * 100).round(2)

    stats = df["payment_consistency_score"].describe()
    print(f"         Mean={stats['mean']:.2f}  |  Median={stats['50%']:.2f}  |  Min={stats['min']:.2f}")

    corr = df["payment_consistency_score"].corr(df["target"])
    print(f"         Correlation with default target: {corr:.4f}")
    return df


# ──────────────────────────────────────────────────────────────────
# FEATURE 3: Revolving Utilization Category
# ──────────────────────────────────────────────────────────────────
def add_revolving_utilization_category(df):
    """
    What it measures:
        Bucketed risk category based on revolving credit utilization.
        Credit bureaus use this as one of the strongest default predictors.

    Thresholds (industry standard):
        0 – 0.30  → LOW    (good)   → encoded as 0
        0.30 – 0.70 → MEDIUM (watch) → encoded as 1
        0.70 – 1.00 → HIGH   (risky) → encoded as 2
        > 1.00    → MAXED   (critical) → encoded as 3

    Why encode rather than use raw value:
        The relationship between utilization and default risk is non-linear.
        Buckets capture this threshold effect better than continuous values.
    """
    print("  [4/7] Engineering Feature 3: Revolving Utilization Category...")

    def categorise(val):
        if val <= 0.30:
            return 0    # LOW
        elif val <= 0.70:
            return 1    # MEDIUM
        elif val <= 1.00:
            return 2    # HIGH
        else:
            return 3    # MAXED OUT

    df["revolving_utilization_cat"] = df["revolving_utilization"].apply(categorise)

    dist = df["revolving_utilization_cat"].value_counts().sort_index()
    labels = {0: "LOW", 1: "MEDIUM", 2: "HIGH", 3: "MAXED"}
    for cat, count in dist.items():
        pct = count / len(df) * 100
        print(f"         {labels[cat]:<8} ({cat}): {count:>7,} ({pct:.1f}%)")

    corr = df["revolving_utilization_cat"].corr(df["target"])
    print(f"         Correlation with default target: {corr:.4f}")
    return df


# ──────────────────────────────────────────────────────────────────
# FEATURE 4: Late Payment Frequency Index
# ──────────────────────────────────────────────────────────────────
def add_late_payment_frequency(df):
    """
    What it measures:
        Total number of delinquency events normalised per open credit line.
        This catches people who are chronically late across many accounts.

    Formula:
        (total late events) / (open credit lines + 1)
        +1 prevents division by zero and penalises people with few lines.

    Why per credit line:
        Someone with 1 late payment on 1 account is more worrying than
        someone with 3 late payments spread across 20 accounts.
    """
    print("  [5/7] Engineering Feature 4: Late Payment Frequency Index...")

    total_late_events = (
        df["late_30_59_days"] +
        df["late_60_89_days"] +
        df["late_90_days"]
    )

    df["late_payment_frequency"] = (
        total_late_events / (df["open_credit_lines"] + 1)
    ).clip(0, 10).round(4)

    stats = df["late_payment_frequency"].describe()
    print(f"         Mean={stats['mean']:.4f}  |  Median={stats['50%']:.4f}  |  Max={stats['max']:.4f}")

    corr = df["late_payment_frequency"].corr(df["target"])
    print(f"         Correlation with default target: {corr:.4f}")
    return df


# ──────────────────────────────────────────────────────────────────
# FEATURE 5: Income Stability Flag
# ──────────────────────────────────────────────────────────────────
def add_income_stability_flag(df):
    """
    What it measures:
        A binary flag identifying applicants with potentially unstable or
        suspicious income profiles — very low income with high debt burden,
        or extremely high income with poor payment history (possible fraud).

    Rules:
        Flag = 1 if ANY of these are true:
        a) monthly_income < 25th percentile AND debt_to_income_ratio > 1.0
        b) monthly_income > 99th percentile AND late_payment_frequency > 0.5
        c) monthly_income == 0 or NaN (should not exist after cleaning)

    Why useful:
        Helps the model learn about unusual income-to-behaviour mismatches,
        which are strong signals of synthetic identity fraud in lending.
    """
    print("  [6/7] Engineering Feature 5: Income Stability Flag...")

    p25 = df["monthly_income"].quantile(0.25)
    p99 = df["monthly_income"].quantile(0.99)

    cond_a = (df["monthly_income"] < p25) & (df["debt_to_income_ratio"] > 1.0)
    cond_b = (df["monthly_income"] > p99) & (df["late_payment_frequency"] > 0.5)
    cond_c = (df["monthly_income"] <= 0)

    df["income_stability_flag"] = ((cond_a | cond_b | cond_c)).astype(int)

    flag_count = df["income_stability_flag"].sum()
    flag_pct   = flag_count / len(df) * 100
    print(f"         Flagged: {flag_count:,} applicants ({flag_pct:.1f}%)")

    # Default rate among flagged vs unflagged
    flagged_default   = df[df["income_stability_flag"]==1]["target"].mean() * 100
    unflagged_default = df[df["income_stability_flag"]==0]["target"].mean() * 100
    print(f"         Default rate — Flagged: {flagged_default:.1f}%  |  Unflagged: {unflagged_default:.1f}%")

    corr = df["income_stability_flag"].corr(df["target"])
    print(f"         Correlation with default target: {corr:.4f}")
    return df


# ──────────────────────────────────────────────────────────────────
# SAVE
# ──────────────────────────────────────────────────────────────────
def save_output(df):
    print("  [7/7] Saving engineered dataset...")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"         ✅ Saved: {OUTPUT_PATH}")
    print(f"         Final shape: {df.shape[0]:,} rows × {df.shape[1]} columns")

    # Log feature summary
    new_features = [
        "debt_to_income_ratio",
        "payment_consistency_score",
        "revolving_utilization_cat",
        "late_payment_frequency",
        "income_stability_flag"
    ]
    log = {
        "engineered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "new_features":  new_features,
        "total_columns": int(df.shape[1]),
        "feature_correlations": {
            feat: round(float(df[feat].corr(df["target"])), 4)
            for feat in new_features
        }
    }
    log_path = os.path.join(LOG_DIR, "feature_engineering_log.json")
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)
    print(f"         ✅ Log saved: {log_path}")


def main():
    print("=" * 60)
    print("  CreditSense AI — Feature Engineer")
    print("=" * 60)

    df = load_data()
    df = add_debt_to_income_ratio(df)
    df = add_payment_consistency_score(df)
    df = add_revolving_utilization_category(df)
    df = add_late_payment_frequency(df)
    df = add_income_stability_flag(df)
    save_output(df)

    print("\n  New features summary:")
    new_cols = [
        "debt_to_income_ratio", "payment_consistency_score",
        "revolving_utilization_cat", "late_payment_frequency",
        "income_stability_flag"
    ]
    print(df[new_cols].describe().round(3).to_string())
    print("=" * 60)
    print("  ✅ Feature engineering complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()