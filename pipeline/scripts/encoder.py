"""
encoder.py
Encodes categorical columns in the fraud transaction dataset.
The credit dataset is already fully numeric so no encoding needed there.
Input : data/synthetic/fraud_transactions.csv
Output: data/cleaned/fraud_cleaned.csv
"""
import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import numpy as np
import os
import json
import joblib
from datetime import datetime
from sklearn.preprocessing import LabelEncoder

INPUT_PATH   = "data/synthetic/fraud_transactions.csv"
OUTPUT_PATH  = "data/cleaned/fraud_cleaned.csv"
ENCODER_PATH = "ml/models/label_encoders.joblib"
LOG_DIR      = "pipeline/logs"

# Columns to label-encode (low cardinality categorical)
LABEL_ENCODE_COLS = ["merchant_category", "channel", "city"]

# Columns to drop (IDs, timestamps — not useful as ML features)
DROP_COLS = ["transaction_id", "timestamp"]


def load_data():
    print("  [1/5] Loading fraud transaction data...")
    df = pd.read_csv(INPUT_PATH)
    print(f"         Loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df


def drop_unused_columns(df):
    print("  [2/5] Dropping non-feature columns...")
    cols_to_drop = [c for c in DROP_COLS if c in df.columns]
    df = df.drop(columns=cols_to_drop)
    print(f"         Dropped: {cols_to_drop}")
    return df


def label_encode(df):
    """
    Label encode categorical columns.
    Saves encoder objects so the Flask service can reverse-encode for explainability.
    """
    print("  [3/5] Label encoding categorical columns...")
    encoders = {}
    encode_log = {}

    for col in LABEL_ENCODE_COLS:
        if col not in df.columns:
            print(f"         ⚠️  '{col}' not found — skipping")
            continue

        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le

        encode_log[col] = {
            "type":    "LabelEncoder",
            "classes": list(le.classes_),
            "mapping": {cls: int(idx) for idx, cls in enumerate(le.classes_)}
        }
        print(f"         '{col}': {len(le.classes_)} unique values encoded")
        for cls, idx in encode_log[col]["mapping"].items():
            print(f"            {idx} → {cls}")

    # Save encoders for use in Flask service later
    os.makedirs(os.path.dirname(ENCODER_PATH), exist_ok=True)
    joblib.dump(encoders, ENCODER_PATH)
    print(f"         ✅ Encoders saved: {ENCODER_PATH}")

    return df, encode_log


def handle_fraud_nulls(df):
    print("  [4/5] Checking and handling any nulls...")
    null_counts = df.isnull().sum()
    if null_counts.sum() == 0:
        print("         ✅ No nulls found in fraud dataset.")
    else:
        for col in null_counts[null_counts > 0].index:
            df[col].fillna(df[col].median(), inplace=True)
            print(f"         '{col}': filled with median")
    return df


def save_output(df, encode_log):
    print("  [5/5] Saving encoded data...")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"         ✅ Saved: {OUTPUT_PATH}")

    log = {
        "encoded_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "output_shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
        "encodings":    encode_log
    }
    log_path = os.path.join(LOG_DIR, "encoding_log.json")
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)
    print(f"         ✅ Log saved: {log_path}")


def main():
    print("=" * 60)
    print("  CreditSense AI — Encoder")
    print("=" * 60)

    df = load_data()
    df = drop_unused_columns(df)
    df = handle_fraud_nulls(df)
    df, encode_log = label_encode(df)

    print(f"\n  Final encoded shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"  Columns: {list(df.columns)}")

    save_output(df, encode_log)

    print("=" * 60)
    print("  ✅ Encoding complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()