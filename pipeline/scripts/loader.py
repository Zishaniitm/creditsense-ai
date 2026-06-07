"""
loader.py
Loads cleaned and engineered datasets into PostgreSQL using bulk insert.
Uses pandas to_sql() for fast batch loading instead of row-by-row inserts.
"""

import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime

load_dotenv()

DB_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

CREDIT_PATH = "data/engineered/credit_features.csv"
FRAUD_PATH  = "data/cleaned/fraud_cleaned.csv"
LOG_DIR     = "pipeline/logs"


def get_engine():
    return create_engine(DB_URL, pool_pre_ping=True)


def test_connection(engine):
    print("  Testing database connection...")
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version()")).fetchone()[0]
        print(f"  ✅ Connected: {version[:55]}...")


def load_credit_data(engine):
    """
    Bulk load credit data using pandas to_sql().
    Builds all three tables as DataFrames first, then inserts in one shot.
    """
    print("\n  Loading credit scoring dataset (bulk insert)...")
    df = pd.read_csv(CREDIT_PATH)
    n  = len(df)
    print(f"  Rows: {n:,}")

    # ── Build users DataFrame ──────────────────────────────────────────────
    print("  Building users table...")
    user_ids = [str(uuid.uuid4()) for _ in range(n)]
    users_df = pd.DataFrame({
        "user_id":      user_ids,
        "name":         [f"Applicant_{i}" for i in range(n)],
        "email":        [f"applicant_{i}@demo.creditsense.ai" for i in range(n)],
        "password_hash":"$2a$12$placeholder_hash_for_demo_data",
        "role":         "APPLICANT",
        "is_active":    True,
        "created_at":   datetime.now(),
        "updated_at":   datetime.now()
    })

    # ── Build loan_applications DataFrame ─────────────────────────────────
    print("  Building loan_applications table...")
    app_ids = [str(uuid.uuid4()) for _ in range(n)]

    # Fix: ensure loan_amount > 0
    loan_amounts = (df["monthly_income"] * 6).clip(lower=500.0).round(2)

    apps_df = pd.DataFrame({
        "application_id":  app_ids,
        "user_id":         user_ids,
        "loan_amount":     loan_amounts,
        "loan_purpose":    "Personal Loan",
        "loan_term_months":36,
        "status":          df["target"].map({1: "REJECTED", 0: "APPROVED"}),
        "submitted_at":    datetime.now()
    })

    # ── Build applicant_financials DataFrame ───────────────────────────────
    print("  Building applicant_financials table...")
    financials_df = pd.DataFrame({
        "financial_id":              [str(uuid.uuid4()) for _ in range(n)],
        "application_id":            app_ids,
        "age":                       df["age"].clip(lower=18).astype(int),
        "monthly_income":            df["monthly_income"].round(2),
        "debt_ratio":                df["debt_ratio"].round(4),
        "revolving_utilization":     df["revolving_utilization"].round(4),
        "open_credit_lines":         df["open_credit_lines"].astype(int),
        "real_estate_loans":         df["real_estate_loans"].astype(int),
        "num_dependents":            df["num_dependents"].astype(int),
        "late_30_59_days":           df["late_30_59_days"].astype(int),
        "late_60_89_days":           df["late_60_89_days"].astype(int),
        "late_90_days":              df["late_90_days"].astype(int),
        "debt_to_income_ratio":      df["debt_to_income_ratio"].round(4),
        "payment_consistency_score": df["payment_consistency_score"].round(2),
        "revolving_utilization_cat": df["revolving_utilization_cat"].astype(int),
        "late_payment_frequency":    df["late_payment_frequency"].round(4),
        "income_stability_flag":     df["income_stability_flag"].astype(int),
        "created_at":                datetime.now()
    })

    # ── Bulk insert all three tables ───────────────────────────────────────
    print("  Inserting users...           ", end="", flush=True)
    users_df.to_sql("users", engine, if_exists="append",
                    index=False, method="multi", chunksize=2000)
    print(f"✅  {len(users_df):,} rows")

    print("  Inserting loan_applications... ", end="", flush=True)
    apps_df.to_sql("loan_applications", engine, if_exists="append",
                   index=False, method="multi", chunksize=2000)
    print(f"✅  {len(apps_df):,} rows")

    print("  Inserting applicant_financials...", end="", flush=True)
    financials_df.to_sql("applicant_financials", engine, if_exists="append",
                         index=False, method="multi", chunksize=2000)
    print(f"✅  {len(financials_df):,} rows")

    return len(df), 0


def load_fraud_data(engine):
    """Bulk load fraud transaction data."""
    print("\n  Loading fraud transaction dataset (bulk insert)...")
    df = pd.read_csv(FRAUD_PATH)
    n  = len(df)
    print(f"  Rows: {n:,}")

    if "transaction_id" not in df.columns:
        df["transaction_id"] = [f"TXN{str(i).zfill(8)}" for i in range(n)]

    txn_df = pd.DataFrame({
        "transaction_id":       df["transaction_id"] if "transaction_id" in df.columns
                                else [f"TXN{str(i).zfill(8)}" for i in range(n)],
        "amount":               df["amount"].round(2),
        "merchant_category":    df["merchant_category"].astype(str),
        "channel":              df["channel"].astype(str),
        "hour_of_day":          df["hour_of_day"].astype(int),
        "day_of_week":          df["day_of_week"].astype(int),
        "city":                 df["city"].astype(str),
        "is_international":     df["is_international"].astype(int),
        "transactions_last_1h": df["transactions_last_1h"].astype(int),
        "transactions_last_24h":df["transactions_last_24h"].astype(int),
        "avg_txn_amount_30d":   df["avg_txn_amount_30d"].round(2),
        "days_since_last_txn":  df["days_since_last_txn"].astype(int),
        "account_age_days":     df["account_age_days"].astype(int),
        "num_failed_txns_24h":  df["num_failed_txns_24h"].astype(int),
        "is_new_device":        df["is_new_device"].astype(int),
        "submitted_at":         datetime.now()
    })

    print("  Inserting transactions...     ", end="", flush=True)
    txn_df.to_sql("transactions", engine, if_exists="append",
                  index=False, method="multi", chunksize=2000)
    print(f"✅  {len(txn_df):,} rows")

    return len(df), 0


def log_etl_run(engine, pipeline, dataset, ingested, rejected):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO etl_run_logs
                (pipeline_name, dataset_name, records_ingested,
                 records_rejected, status, completed_at)
            VALUES (:pipeline, :dataset, :ingested,
                    :rejected, 'SUCCESS', :completed)
        """), {
            "pipeline":  pipeline,
            "dataset":   dataset,
            "ingested":  ingested,
            "rejected":  rejected,
            "completed": datetime.now()
        })


def verify_load(engine):
    print("\n  Running verification queries...")
    tables = [
        "users", "loan_applications", "applicant_financials",
        "transactions", "etl_run_logs"
    ]
    with engine.connect() as conn:
        for table in tables:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"  {table:<30} → {count:>9,} rows")


def main():
    print("=" * 60)
    print("  CreditSense AI — Database Loader (Bulk Mode)")
    print("=" * 60)

    engine = get_engine()
    test_connection(engine)

    start = datetime.now()

    c_ingested, c_rejected = load_credit_data(engine)
    log_etl_run(engine, "loader.py", "credit_features", c_ingested, c_rejected)

    f_ingested, f_rejected = load_fraud_data(engine)
    log_etl_run(engine, "loader.py", "fraud_transactions", f_ingested, f_rejected)

    elapsed = (datetime.now() - start).seconds
    verify_load(engine)

    print(f"\n  Total time: {elapsed}s")
    print("=" * 60)
    print("  ✅ All data loaded into PostgreSQL successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()