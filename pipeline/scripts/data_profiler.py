"""
data_profiler.py
Generates an automated data quality report for any dataset.
Outputs a structured quality score and flags issues to fix in Week 3.
"""
import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

CREDIT_PATH = "data/raw/credit_raw.csv"
FRAUD_PATH  = "data/synthetic/fraud_transactions.csv"
REPORT_DIR  = "pipeline/logs"

CREDIT_COLUMNS = {
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


def profile_dataset(df, dataset_name, target_col):
    """Run full quality profiling on a dataframe. Returns a report dict."""
    print(f"\n  Profiling: {dataset_name}...")
    report = {
        "dataset":      dataset_name,
        "profiled_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "shape":        {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
        "columns":      {},
        "issues":       [],
        "quality_score": 0
    }

    total_cells = df.shape[0] * df.shape[1]
    issues      = []
    deductions  = 0

    for col in df.columns:
        series = df[col]
        null_count = int(series.isnull().sum())
        null_pct   = round(null_count / len(df) * 100, 2)
        is_numeric = pd.api.types.is_numeric_dtype(series)

        col_profile = {
            "dtype":       str(series.dtype),
            "null_count":  null_count,
            "null_pct":    null_pct,
            "unique":      int(series.nunique()),
            "unique_pct":  round(series.nunique() / len(df) * 100, 2),
        }

        if is_numeric:
            col_profile.update({
                "mean":   round(float(series.mean()), 4) if null_count < len(df) else None,
                "std":    round(float(series.std()),  4) if null_count < len(df) else None,
                "min":    round(float(series.min()),  4) if null_count < len(df) else None,
                "max":    round(float(series.max()),  4) if null_count < len(df) else None,
                "median": round(float(series.median()),4) if null_count < len(df) else None,
            })

            # Detect outliers using IQR
            q1, q3 = series.quantile(0.25), series.quantile(0.75)
            iqr = q3 - q1
            outlier_count = int(((series < q1 - 1.5*iqr) | (series > q3 + 1.5*iqr)).sum())
            outlier_pct   = round(outlier_count / len(df) * 100, 2)
            col_profile["outlier_count"] = outlier_count
            col_profile["outlier_pct"]   = outlier_pct

            if outlier_pct > 5:
                issues.append(f"HIGH OUTLIERS: '{col}' has {outlier_pct}% outliers")
                deductions += 3

        # Flag missing value issues
        if null_pct > 20:
            issues.append(f"CRITICAL NULLS: '{col}' is {null_pct}% missing → consider dropping")
            deductions += 10
        elif null_pct > 5:
            issues.append(f"MODERATE NULLS: '{col}' is {null_pct}% missing → impute")
            deductions += 5
        elif null_pct > 0:
            issues.append(f"LOW NULLS: '{col}' is {null_pct}% missing → impute")
            deductions += 2

        # Flag constant columns
        if series.nunique() <= 1:
            issues.append(f"CONSTANT COLUMN: '{col}' has only 1 unique value → drop")
            deductions += 10

        report["columns"][col] = col_profile

    # Duplicate rows
    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        issues.append(f"DUPLICATES: {dup_count:,} duplicate rows found → remove")
        deductions += min(dup_count / len(df) * 100, 10)

    # Class balance check
    if target_col in df.columns:
        minority_pct = df[target_col].value_counts(normalize=True).min() * 100
        if minority_pct < 5:
            issues.append(f"CLASS IMBALANCE: minority class is only {minority_pct:.1f}% → use SMOTE/oversampling")
            deductions += 5

    report["issues"]        = issues
    report["quality_score"] = max(0, round(100 - deductions, 1))
    return report


def print_report(report):
    """Pretty print a profiling report."""
    name  = report["dataset"]
    score = report["quality_score"]
    emoji = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"

    print(f"\n  ┌─ Quality Report: {name}")
    print(f"  │  Score: {score}/100  {emoji}")
    print(f"  │  Rows:  {report['shape']['rows']:,}  |  Columns: {report['shape']['columns']}")
    if report["issues"]:
        print(f"  │  Issues found ({len(report['issues'])}):")
        for issue in report["issues"]:
            print(f"  │    → {issue}")
    else:
        print(f"  │  No issues found.")
    print(f"  └─ Profiled at: {report['profiled_at']}")


def save_report(report, filename):
    os.makedirs(REPORT_DIR, exist_ok=True)
    path = os.path.join(REPORT_DIR, filename)
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  💾 Report saved: {path}")


def main():
    print("=" * 60)
    print("  CreditSense AI — Data Profiler")
    print("=" * 60)

    # Profile credit dataset
    credit_df = pd.read_csv(CREDIT_PATH)
    credit_df.rename(columns=CREDIT_COLUMNS, inplace=True)
    credit_df = credit_df.loc[:, ~credit_df.columns.str.contains('^Unnamed')]
    credit_report = profile_dataset(credit_df, "credit_scoring", "target")
    print_report(credit_report)
    save_report(credit_report, "credit_profile_report.json")

    # Profile fraud dataset
    fraud_df  = pd.read_csv(FRAUD_PATH)
    fraud_report = profile_dataset(fraud_df, "fraud_transactions", "is_fraud")
    print_report(fraud_report)
    save_report(fraud_report, "fraud_profile_report.json")

    print(f"\n{'='*60}")
    print(f"  ✅ Profiling complete.")
    print(f"     Reports saved in: {REPORT_DIR}/")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()