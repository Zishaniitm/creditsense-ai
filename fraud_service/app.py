"""
fraud_service/app.py
Flask microservice for real-time fraud detection.

Endpoints:
  POST /fraud-check  → anomaly score + fraud probability + is_fraudulent
  GET  /health       → service health check
"""

import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")
import os
import json
import joblib
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

load_dotenv()

app = Flask(__name__)
CORS(app)

# ── Config ─────────────────────────────────────────────────────────────────
MODEL_VERSION = "v1.0.0"
MODEL_PATH    = f"ml/models/fraud_model_{MODEL_VERSION}.joblib"
SCALER_PATH   = f"ml/models/fraud_scaler_{MODEL_VERSION}.joblib"

FEATURE_COLS  = [
    "amount", "merchant_category", "channel",
    "hour_of_day", "day_of_week", "city",
    "is_international", "transactions_last_1h", "transactions_last_24h",
    "avg_txn_amount_30d", "days_since_last_txn",
    "account_age_days", "num_failed_txns_24h", "is_new_device"
]

FEATURE_DISPLAY_NAMES = {
    "amount":                "Transaction Amount",
    "merchant_category":     "Merchant Category",
    "channel":               "Payment Channel",
    "hour_of_day":           "Hour of Day",
    "day_of_week":           "Day of Week",
    "city":                  "City",
    "is_international":      "International Transaction",
    "transactions_last_1h":  "Transactions in Last 1 Hour",
    "transactions_last_24h": "Transactions in Last 24 Hours",
    "avg_txn_amount_30d":    "Avg Transaction Amount (30 Days)",
    "days_since_last_txn":   "Days Since Last Transaction",
    "account_age_days":      "Account Age (Days)",
    "num_failed_txns_24h":   "Failed Transactions (24 Hours)",
    "is_new_device":         "New Device Flag"
}

# Fraud risk thresholds
HIGH_RISK_THRESHOLD = 0.70    # above this = definitely flag
MED_RISK_THRESHOLD  = 0.40    # above this = review

# ── Load at startup ─────────────────────────────────────────────────────────
print("Loading fraud detection model...")
model  = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
print(f"✅ Fraud detection service ready on port {os.getenv('FRAUD_SERVICE_PORT', 5001)}")


# ══════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════
def validate_transaction(data: dict) -> tuple[bool, str]:
    required = ["amount", "hour_of_day", "is_international",
                "transactions_last_1h", "num_failed_txns_24h", "account_age_days"]
    missing = [f for f in required if f not in data]
    if missing:
        return False, f"Missing required fields: {missing}"
    if float(data.get("amount", 0)) <= 0:
        return False, "Transaction amount must be positive"
    return True, ""


def prepare_transaction(data: dict) -> pd.DataFrame:
    """Fill missing optional fields with safe defaults."""
    defaults = {
        "amount":                0.0,
        "merchant_category":     0,
        "channel":               0,
        "hour_of_day":           12,
        "day_of_week":           0,
        "city":                  0,
        "is_international":      0,
        "transactions_last_1h":  0,
        "transactions_last_24h": 0,
        "avg_txn_amount_30d":    0.0,
        "days_since_last_txn":   0,
        "account_age_days":      365,
        "num_failed_txns_24h":   0,
        "is_new_device":         0
    }
    row = {col: float(data.get(col, defaults[col])) for col in FEATURE_COLS}
    return pd.DataFrame([row])[FEATURE_COLS]


def get_risk_level(fraud_prob: float) -> str:
    if fraud_prob >= HIGH_RISK_THRESHOLD:
        return "HIGH"
    elif fraud_prob >= MED_RISK_THRESHOLD:
        return "MEDIUM"
    return "LOW"


def get_top_anomalous_features(X_raw: pd.DataFrame, X_scaled: np.ndarray) -> list:
    """
    Identify the most suspicious features by comparing transaction
    values against known fraud patterns from our training analysis.
    """
    fraud_indicators = {
        "is_international":     {"threshold": 0.5,  "label": "International transaction"},
        "num_failed_txns_24h":  {"threshold": 2,    "label": "Multiple failed attempts"},
        "is_new_device":        {"threshold": 0.5,  "label": "New/unrecognized device"},
        "transactions_last_1h": {"threshold": 3,    "label": "Burst of transactions"},
        "hour_of_day":          {"threshold": None, "label": "Unusual transaction hour"},
        "account_age_days":     {"threshold": 30,   "label": "Very new account"},
    }

    anomalies = []
    row = X_raw.iloc[0]

    for feat, info in fraud_indicators.items():
        if feat not in row.index:
            continue
        val = float(row[feat])
        flagged = False

        if info["threshold"] is not None:
            if feat == "account_age_days":
                flagged = val < info["threshold"]
            else:
                flagged = val > info["threshold"]
        else:
            # hour_of_day: flag if outside 6am-10pm
            flagged = not (6 <= val <= 22)

        if flagged:
            anomalies.append({
                "feature":      feat,
                "display_name": FEATURE_DISPLAY_NAMES.get(feat, feat),
                "value":        val,
                "reason":       info["label"]
            })

    return anomalies[:5]


# ══════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":        "healthy",
        "service":       "fraud_service",
        "model_version": MODEL_VERSION
    }), 200


@app.route("/fraud-check", methods=["POST"])
def fraud_check():
    """
    Real-time fraud detection endpoint.

    Request body (JSON):
    {
      "amount": 85000,
      "merchant_category": 14,
      "channel": 1,
      "hour_of_day": 2,
      "day_of_week": 6,
      "city": 3,
      "is_international": 1,
      "transactions_last_1h": 6,
      "transactions_last_24h": 12,
      "avg_txn_amount_30d": 3500.00,
      "days_since_last_txn": 0,
      "account_age_days": 45,
      "num_failed_txns_24h": 4,
      "is_new_device": 1
    }

    Response:
    {
      "is_fraudulent": true,
      "fraud_probability": 0.8734,
      "anomaly_score": -0.6521,
      "risk_level": "HIGH",
      "action": "BLOCK",
      "model_version": "v1.0.0",
      "top_anomalous_features": [...]
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        valid, error_msg = validate_transaction(data)
        if not valid:
            return jsonify({"error": error_msg}), 422

        X_raw    = prepare_transaction(data)
        X_scaled = scaler.transform(X_raw)

        # Isolation Forest inference
        raw_pred      = model.predict(X_scaled)[0]
        anomaly_score = model.score_samples(X_scaled)[0]

        # Convert to fraud probability (0-1)
        # score_samples returns negative values; more negative = more anomalous
        fraud_prob = float(np.clip(-anomaly_score, 0, 1))

        is_fraudulent  = raw_pred == -1
        risk_level     = get_risk_level(fraud_prob)
        top_features   = get_top_anomalous_features(X_raw, X_scaled)

        action = "BLOCK"  if risk_level == "HIGH"   else \
                 "REVIEW" if risk_level == "MEDIUM"  else "ALLOW"

        return jsonify({
            "is_fraudulent":          bool(is_fraudulent),
            "fraud_probability":      round(fraud_prob, 4),
            "anomaly_score":          round(float(anomaly_score), 6),
            "risk_level":             risk_level,
            "action":                 action,
            "model_version":          MODEL_VERSION,
            "top_anomalous_features": top_features
        }), 200

    except Exception as e:
        return jsonify({"error": f"Fraud check failed: {str(e)}"}), 500


# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    port = int(os.getenv("FRAUD_SERVICE_PORT", 5001))
    print(f"\n🚀 Fraud Detection Service starting on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)