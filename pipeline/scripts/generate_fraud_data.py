"""
generate_fraud_data.py
Generates a synthetic financial transaction dataset for fraud detection training.
Produces 100,000 transactions with realistic feature distributions and ~3% fraud rate.
"""

import numpy as np
import pandas as pd
from faker import Faker
import os
from datetime import datetime, timedelta
import random

# ── Reproducibility ────────────────────────────────────────────────────────
np.random.seed(42)
random.seed(42)
fake = Faker('en_IN')   # Indian locale for realistic data
Faker.seed(42)

# ── Config ─────────────────────────────────────────────────────────────────
NUM_TRANSACTIONS  = 100_000
FRAUD_RATE        = 0.03          # 3% fraud — realistic for Indian NBFC data
OUTPUT_PATH       = "data/synthetic/fraud_transactions.csv"

MERCHANTS = [
    "Amazon", "Flipkart", "Swiggy", "Zomato", "PhonePe",
    "Paytm", "BigBasket", "Myntra", "Nykaa", "MakeMyTrip",
    "ATM_Withdrawal", "POS_Terminal", "UPI_Transfer", "NEFT",
    "International_Online"
]

CHANNELS = ["UPI", "Net Banking", "Credit Card", "Debit Card", "ATM", "NEFT/RTGS"]
CITIES   = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
            "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow"]


def generate_normal_transaction():
    """Generate a single legitimate transaction with realistic patterns."""
    return {
        "amount":                round(np.random.lognormal(mean=7.5, sigma=1.2), 2),
        "merchant_category":     random.choice(MERCHANTS[:-2]),   # no international
        "channel":               random.choice(CHANNELS[:4]),     # common channels
        "hour_of_day":           int(np.random.choice(
                                     range(24),
                                     p=_hour_distribution()
                                 )),
        "day_of_week":           random.randint(0, 6),
        "city":                  random.choice(CITIES),
        "is_international":      0,
        "transactions_last_1h":  int(np.random.poisson(lam=1.2)),
        "transactions_last_24h": int(np.random.poisson(lam=5.0)),
        "avg_txn_amount_30d":    round(np.random.lognormal(mean=7.2, sigma=0.8), 2),
        "days_since_last_txn":   int(np.random.exponential(scale=2)),
        "account_age_days":      int(np.random.randint(180, 3650)),
        "num_failed_txns_24h":   int(np.random.poisson(lam=0.2)),
        "is_new_device":         int(np.random.binomial(1, 0.05)),
        "is_fraud":              0
    }


def generate_fraud_transaction():
    """
    Generate a fraudulent transaction.
    Frauds show: unusual hours, high amounts, international, burst activity,
    new devices, many failed attempts before success.
    """
    fraud_pattern = random.choice(["card_theft", "account_takeover", "synthetic_id"])

    if fraud_pattern == "card_theft":
        # High amount, odd hour, international
        return {
            "amount":                round(np.random.uniform(15000, 150000), 2),
            "merchant_category":     random.choice(["International_Online", "ATM_Withdrawal"]),
            "channel":               random.choice(["Credit Card", "ATM"]),
            "hour_of_day":           random.choice([0,1,2,3,4,22,23]),
            "day_of_week":           random.randint(0, 6),
            "city":                  random.choice(CITIES),
            "is_international":      1,
            "transactions_last_1h":  int(np.random.poisson(lam=6)),
            "transactions_last_24h": int(np.random.poisson(lam=12)),
            "avg_txn_amount_30d":    round(np.random.lognormal(mean=6.5, sigma=0.5), 2),
            "days_since_last_txn":   0,
            "account_age_days":      int(np.random.randint(180, 3650)),
            "num_failed_txns_24h":   int(np.random.poisson(lam=4)),
            "is_new_device":         1,
            "is_fraud":              1
        }
    elif fraud_pattern == "account_takeover":
        # Burst of many small transactions followed by one large
        return {
            "amount":                round(np.random.uniform(8000, 80000), 2),
            "merchant_category":     random.choice(MERCHANTS),
            "channel":               "Net Banking",
            "hour_of_day":           random.choice([1,2,3,14,15]),
            "day_of_week":           random.randint(0, 6),
            "city":                  random.choice(CITIES),
            "is_international":      0,
            "transactions_last_1h":  int(np.random.poisson(lam=8)),
            "transactions_last_24h": int(np.random.poisson(lam=18)),
            "avg_txn_amount_30d":    round(np.random.lognormal(mean=6.0, sigma=0.6), 2),
            "days_since_last_txn":   0,
            "account_age_days":      int(np.random.randint(30, 365)),
            "num_failed_txns_24h":   int(np.random.poisson(lam=6)),
            "is_new_device":         1,
            "is_fraud":              1
        }
    else:   # synthetic_id — new account, moderate amounts, odd patterns
        return {
            "amount":                round(np.random.uniform(3000, 30000), 2),
            "merchant_category":     "UPI_Transfer",
            "channel":               "UPI",
            "hour_of_day":           random.choice([10,11,12,13,14]),
            "day_of_week":           random.randint(0, 6),
            "city":                  random.choice(CITIES),
            "is_international":      0,
            "transactions_last_1h":  int(np.random.poisson(lam=3)),
            "transactions_last_24h": int(np.random.poisson(lam=8)),
            "avg_txn_amount_30d":    round(np.random.lognormal(mean=5.5, sigma=0.4), 2),
            "days_since_last_txn":   int(np.random.exponential(scale=0.5)),
            "account_age_days":      int(np.random.randint(1, 90)),
            "num_failed_txns_24h":   int(np.random.poisson(lam=2)),
            "is_new_device":         int(np.random.binomial(1, 0.7)),
            "is_fraud":              1
        }


def _hour_distribution():
    """Realistic hour-of-day probability for normal transactions (India)."""
    weights = [
        0.005, 0.003, 0.002, 0.002, 0.003, 0.008,   # 0-5  (late night / early morning)
        0.020, 0.045, 0.065, 0.070, 0.072, 0.075,   # 6-11 (morning surge)
        0.075, 0.072, 0.068, 0.065, 0.060, 0.058,   # 12-17 (afternoon)
        0.055, 0.060, 0.055, 0.045, 0.030, 0.010    # 18-23 (evening drop)
    ]
    total = sum(weights)
    return [w / total for w in weights]


def add_transaction_metadata(df):
    """Add timestamps and transaction IDs."""
    base_date = datetime(2024, 1, 1)
    df["transaction_id"] = [f"TXN{str(i).zfill(8)}" for i in range(len(df))]
    df["timestamp"] = [
        (base_date + timedelta(
            days=random.randint(0, 364),
            hours=row["hour_of_day"],
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )).strftime("%Y-%m-%d %H:%M:%S")
        for _, row in df.iterrows()
    ]
    # Reorder columns nicely
    cols = ["transaction_id", "timestamp"] + \
           [c for c in df.columns if c not in ["transaction_id", "timestamp"]]
    return df[cols]


def main():
    print("=" * 60)
    print("  CreditSense AI — Synthetic Fraud Data Generator")
    print("=" * 60)

    num_fraud  = int(NUM_TRANSACTIONS * FRAUD_RATE)
    num_normal = NUM_TRANSACTIONS - num_fraud

    print(f"\n  Generating {num_normal:,} normal transactions...")
    normal_txns = [generate_normal_transaction() for _ in range(num_normal)]

    print(f"  Generating {num_fraud:,} fraudulent transactions...")
    fraud_txns  = [generate_fraud_transaction() for _ in range(num_fraud)]

    # Combine and shuffle
    df = pd.DataFrame(normal_txns + fraud_txns)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    # Add metadata
    print("  Adding transaction IDs and timestamps...")
    df = add_transaction_metadata(df)

    # Save
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    # Summary
    print(f"\n  Dataset saved to: {OUTPUT_PATH}")
    print(f"  Total rows    : {len(df):,}")
    print(f"  Normal        : {(df['is_fraud']==0).sum():,} ({(df['is_fraud']==0).mean()*100:.1f}%)")
    print(f"  Fraudulent    : {(df['is_fraud']==1).sum():,} ({(df['is_fraud']==1).mean()*100:.1f}%)")
    print(f"  Features      : {len(df.columns)}")
    print(f"  File size     : {os.path.getsize(OUTPUT_PATH)/1024/1024:.1f} MB")
    print("\n  Sample rows:")
    print(df[["transaction_id","amount","merchant_category","is_fraud"]].head(5).to_string(index=False))
    print("=" * 60)


if __name__ == "__main__":
    main()