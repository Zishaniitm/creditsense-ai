"""
cleaner.py
Cleans the raw credit scoring dataset.
Handles: missing values, outliers, duplicates, invalid entries.
Input : data/raw/credit_raw.csv
Output: data/cleaned/credit_cleaned.csv
"""
import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

# ── Config ─────────────────────────────────────────────────────────────────
INPUT_PATH  = "data/raw/credit_raw.csv"
OUTPUT_PATH = "data/cleaned/credit_cleaned.csv"
LOG_DIR     = "pipeline/logs"

COLUMN_RENAME = {
    "SeriousDlqin2yrs":                     "target",
    "RevolvingUtilizationOfUnsecuredLines":  "revolving_utilization",
    "age":                                   "age",
    "NumberOfTime30-59DaysPastDueNotWorse":  "late_30_59_days",
    "DebtRatio":                             "debt_ratio",
    "MonthlyIncome":                         "monthly_income",
    "NumberOfOpenCreditLinesAndLoans":       "open_credit_lines",
    "NumberOfTimes90DaysLate":               "late_90_days",
    "NumberRealEstateLoansOrLines":          "real_estate_loans",
    "NumberOfTime60-89DaysPastDueNotWorse":  "late_60_89_days",
    "NumberOfDependents":                    "num_dependents"
}

# Columns to impute with median (numerical, skewed)
MEDIAN_IMPUTE_COLS = ["monthly_income", "num_dependents"]

# Hard business rules: values outside these ranges are invalid
VALID_RANGES = {
    "age":                  (18, 100),
    "revolving_utilization":(0,  10),
    "debt_ratio":           (0,  100),
    "late_30_59_days":      (0,  20),
    "late_60_89_days":      (0,  20),
    "late_90_days":         (0,  20),
    "open_credit_lines":    (0,  60),
    "real_estate_loans":    (0,  20),
    "num_dependents":       (0,  15),
}


def load_data():
    print("  [1/7] Loading raw data...")
    df = pd.read_csv(INPUT_PATH)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.rename(columns=COLUMN_RENAME, inplace=True)
    print(f"         Loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df


def remove_duplicates(df):
    print("  [2/7] Removing duplicates...")
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    removed = before - len(df)
    print(f"         Removed: {removed:,} duplicate rows")
    return df


def fix_invalid_values(df):
    """Replace out-of-range values with NaN so imputation handles them."""
    print("  [3/7] Fixing invalid values (out-of-range → NaN)...")
    total_fixed = 0
    for col, (lo, hi) in VALID_RANGES.items():
        if col not in df.columns:
            continue
        mask  = (df[col] < lo) | (df[col] > hi)
        count = mask.sum()
        if count > 0:
            df.loc[mask, col] = np.nan
            print(f"         '{col}': {count:,} values outside [{lo}, {hi}] → NaN")
            total_fixed += count
    print(f"         Total invalid values fixed: {total_fixed:,}")
    return df


def impute_missing_values(df):
    print("  [4/7] Imputing missing values...")
    impute_log = {}

    for col in MEDIAN_IMPUTE_COLS:
        if col not in df.columns:
            continue
        null_count = df[col].isnull().sum()
        if null_count > 0:
            median_val = df[col].median()
            df[col].fillna(median_val, inplace=True)
            impute_log[col] = {
                "strategy": "median",
                "value":    round(median_val, 4),
                "filled":   int(null_count)
            }
            print(f"         '{col}': filled {null_count:,} nulls with median={median_val:.2f}")

    # Fill remaining numeric nulls with median
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            median_val = df[col].median()
            df[col].fillna(median_val, inplace=True)
            impute_log[col] = {
                "strategy": "median",
                "value":    round(float(median_val), 4),
                "filled":   int(null_count)
            }
            print(f"         '{col}': filled {null_count:,} nulls with median={median_val:.4f}")

    return df, impute_log


def cap_outliers(df):
    """
    Cap extreme outliers at 1st and 99th percentile (Winsorization).
    Preserves data while reducing extreme skew effect on ML models.
    """
    print("  [5/7] Capping outliers (Winsorization at 1st–99th percentile)...")
    cap_log = {}
    skip_cols = {"target"}
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    for col in numeric_cols:
        if col in skip_cols:
            continue
        p01 = df[col].quantile(0.01)
        p99 = df[col].quantile(0.99)
        before_min, before_max = df[col].min(), df[col].max()
        df[col] = df[col].clip(lower=p01, upper=p99)
        if df[col].min() != before_min or df[col].max() != before_max:
            cap_log[col] = {
                "lower_cap": round(float(p01), 4),
                "upper_cap": round(float(p99), 4)
            }
            print(f"         '{col}': capped to [{p01:.4f}, {p99:.4f}]")

    return df, cap_log


def validate_final(df):
    """Final checks — confirm no nulls remain and target is binary."""
    print("  [6/7] Final validation...")
    remaining_nulls = df.isnull().sum().sum()
    if remaining_nulls > 0:
        print(f"         ⚠️  WARNING: {remaining_nulls} nulls remain after imputation!")
    else:
        print(f"         ✅ No nulls remaining.")

    target_vals = df["target"].unique()
    assert set(target_vals).issubset({0, 1}), f"Target has unexpected values: {target_vals}"
    print(f"         ✅ Target column: {dict(df['target'].value_counts())}")
    print(f"         ✅ Final shape  : {df.shape[0]:,} rows × {df.shape[1]} columns")


def save_output(df, impute_log, cap_log):
    print("  [7/7] Saving cleaned data and cleaning log...")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"         ✅ Saved: {OUTPUT_PATH}")

    log = {
        "cleaned_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "output_shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
        "imputation":   impute_log,
        "outlier_caps": cap_log
    }
    log_path = os.path.join(LOG_DIR, "cleaning_log.json")
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)
    print(f"         ✅ Log saved: {log_path}")


def main():
    print("=" * 60)
    print("  CreditSense AI — Data Cleaner")
    print("=" * 60)

    df = load_data()
    df = remove_duplicates(df)
    df = fix_invalid_values(df)
    df, impute_log = impute_missing_values(df)
    df, cap_log    = cap_outliers(df)
    validate_final(df)
    save_output(df, impute_log, cap_log)

    print("=" * 60)
    print("  ✅ Cleaning complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()