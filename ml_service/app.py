"""
ml_service/app.py
Flask microservice exposing credit scoring ML model via REST API.

Endpoints:
  POST /predict  → credit risk score + category + confidence
  POST /explain  → SHAP top-5 feature explanations
  GET  /health   → service health check
  GET  /model/info → active model metadata
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
MODEL_VERSION  = "v1.0.0"
MODEL_PATH     = f"ml/models/credit_model_{MODEL_VERSION}.joblib"
SCALER_PATH    = f"ml/models/credit_scaler_{MODEL_VERSION}.joblib"
EXPLAINER_PATH = f"ml/models/shap_explainer_{MODEL_VERSION}.joblib"
IMPORTANCE_PATH= "ml/evaluation/shap_feature_importance.json"

FEATURE_COLS = [
    "age", "monthly_income", "debt_ratio", "revolving_utilization",
    "open_credit_lines", "real_estate_loans", "num_dependents",
    "late_30_59_days", "late_60_89_days", "late_90_days",
    "debt_to_income_ratio", "payment_consistency_score",
    "revolving_utilization_cat", "late_payment_frequency",
    "income_stability_flag"
]

FEATURE_DISPLAY_NAMES = {
    "age":                       "Applicant Age",
    "monthly_income":            "Monthly Income (₹)",
    "debt_ratio":                "Debt Ratio",
    "revolving_utilization":     "Revolving Credit Utilization",
    "open_credit_lines":         "Number of Open Credit Lines",
    "real_estate_loans":         "Real Estate Loans Count",
    "num_dependents":            "Number of Dependents",
    "late_30_59_days":           "Payments 30-59 Days Late",
    "late_60_89_days":           "Payments 60-89 Days Late",
    "late_90_days":              "Payments 90+ Days Late",
    "debt_to_income_ratio":      "Debt-to-Income Ratio",
    "payment_consistency_score": "Payment Consistency Score",
    "revolving_utilization_cat": "Credit Utilization Category",
    "late_payment_frequency":    "Late Payment Frequency",
    "income_stability_flag":     "Income Stability Flag"
}

# ── Load models at startup (not per request) ───────────────────────────────
print("Loading ML models...")
model     = joblib.load(MODEL_PATH)
scaler    = joblib.load(SCALER_PATH)
explainer = joblib.load(EXPLAINER_PATH)

with open(IMPORTANCE_PATH) as f:
    global_importance = json.load(f)

print(f"✅ Credit scoring service ready on port {os.getenv('ML_SERVICE_PORT', 5000)}")


# ══════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════
def validate_input(data: dict) -> tuple[bool, str]:
    """Validate all required features are present and numeric."""
    missing = [col for col in FEATURE_COLS if col not in data]
    if missing:
        return False, f"Missing features: {missing}"

    for col in FEATURE_COLS:
        try:
            float(data[col])
        except (TypeError, ValueError):
            return False, f"Feature '{col}' must be numeric, got: {data[col]}"

    # Business rule validations
    if not (18 <= float(data["age"]) <= 100):
        return False, "Age must be between 18 and 100"
    if float(data["monthly_income"]) < 0:
        return False, "Monthly income cannot be negative"

    return True, ""


def build_feature_vector(data: dict) -> pd.DataFrame:
    """Build a single-row DataFrame in the correct feature order."""
    row = {col: float(data[col]) for col in FEATURE_COLS}
    return pd.DataFrame([row])[FEATURE_COLS]


def score_to_risk(probability: float) -> tuple[int, str]:
    """
    Convert raw default probability to credit score (0-100) and category.
    Score is INVERTED: higher score = safer applicant.
    Industry convention: CIBIL/Experian use 300-900; we use 0-100 for simplicity.
    """
    credit_score = round((1 - probability) * 100, 1)

    if probability < 0.30:
        category = "LOW"
    elif probability < 0.60:
        category = "MEDIUM"
    else:
        category = "HIGH"

    return credit_score, category


def get_shap_explanation(X: pd.DataFrame, top_n: int = 5) -> list:
    """Compute SHAP values and return top N feature contributions."""
    shap_vals = explainer.shap_values(X)

    # Handle both 1D and 2D output
    if hasattr(shap_vals, 'values'):
        sv = shap_vals.values[0]
    elif isinstance(shap_vals, list):
        sv = shap_vals[1][0] if len(shap_vals) > 1 else shap_vals[0][0]
    else:
        sv = shap_vals[0]

    explanation = []
    for col, shap_val, feat_val in zip(FEATURE_COLS, sv, X.iloc[0]):
        explanation.append({
            "feature":      col,
            "display_name": FEATURE_DISPLAY_NAMES.get(col, col),
            "value":        round(float(feat_val), 4),
            "shap_value":   round(float(shap_val), 6),
            "direction":    "increases_risk" if shap_val > 0 else "decreases_risk",
            "abs_impact":   abs(float(shap_val))
        })

    explanation.sort(key=lambda x: -x["abs_impact"])
    # Remove abs_impact from output (internal use only)
    for item in explanation:
        del item["abs_impact"]

    return explanation[:top_n]


# ══════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":        "healthy",
        "service":       "ml_service",
        "model_version": MODEL_VERSION
    }), 200


@app.route("/model/info", methods=["GET"])
def model_info():
    return jsonify({
        "model_version":  MODEL_VERSION,
        "model_type":     type(model).__name__,
        "features":       FEATURE_COLS,
        "feature_count":  len(FEATURE_COLS),
        "top_5_features": [f["display_name"] for f in global_importance[:5]]
    }), 200


@app.route("/predict", methods=["POST"])
def predict():
    """
    Credit risk prediction endpoint.

    Request body (JSON):
    {
      "age": 35,
      "monthly_income": 50000,
      "debt_ratio": 0.3,
      "revolving_utilization": 0.45,
      "open_credit_lines": 5,
      "real_estate_loans": 1,
      "num_dependents": 2,
      "late_30_59_days": 0,
      "late_60_89_days": 0,
      "late_90_days": 0,
      "debt_to_income_ratio": 0.35,
      "payment_consistency_score": 95.0,
      "revolving_utilization_cat": 1,
      "late_payment_frequency": 0.0,
      "income_stability_flag": 0
    }

    Response (JSON):
    {
      "risk_score": 78.5,
      "risk_category": "LOW",
      "default_probability": 0.215,
      "confidence": 0.89,
      "model_version": "v1.0.0",
      "recommendation": "APPROVE"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        # Validate
        valid, error_msg = validate_input(data)
        if not valid:
            return jsonify({"error": error_msg}), 422

        # Build feature vector
        X = build_feature_vector(data)

        # Scale for prediction (XGBoost doesn't need scaling
        # but we keep it consistent for future model swaps)
        X_scaled = scaler.transform(X)

        # Predict — use raw X for tree models
        model_type = type(model).__name__
        X_input    = X if "XGB" in model_type or "Forest" in model_type else X_scaled

        prob       = model.predict_proba(X_input)[0][1]
        score, cat = score_to_risk(prob)

        # Confidence: distance from 0.5 threshold, scaled to 0-1
        confidence = round(abs(prob - 0.5) * 2, 4)

        recommendation = "APPROVE" if cat == "LOW" else \
                         "REVIEW"  if cat == "MEDIUM" else "REJECT"

        return jsonify({
            "risk_score":          score,
            "risk_category":       cat,
            "default_probability": round(float(prob), 4),
            "confidence":          confidence,
            "model_version":       MODEL_VERSION,
            "recommendation":      recommendation
        }), 200

    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500


@app.route("/explain", methods=["POST"])
def explain():
    """
    SHAP explanation endpoint.
    Same request body as /predict.

    Response adds SHAP top-5 feature contributions:
    {
      ...all /predict fields...,
      "explanation": [
        {
          "feature": "payment_consistency_score",
          "display_name": "Payment Consistency Score",
          "value": 95.0,
          "shap_value": -0.4312,
          "direction": "decreases_risk"
        },
        ...
      ]
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        valid, error_msg = validate_input(data)
        if not valid:
            return jsonify({"error": error_msg}), 422

        X = build_feature_vector(data)

        model_type = type(model).__name__
        X_input    = X if "XGB" in model_type or "Forest" in model_type else scaler.transform(X)

        prob       = model.predict_proba(X_input)[0][1]
        score, cat = score_to_risk(prob)
        confidence = round(abs(prob - 0.5) * 2, 4)
        explanation = get_shap_explanation(X, top_n=5)
        recommendation = "APPROVE" if cat == "LOW" else \
                         "REVIEW"  if cat == "MEDIUM" else "REJECT"

        return jsonify({
            "risk_score":          score,
            "risk_category":       cat,
            "default_probability": round(float(prob), 4),
            "confidence":          confidence,
            "model_version":       MODEL_VERSION,
            "recommendation":      recommendation,
            "explanation":         explanation
        }), 200

    except Exception as e:
        return jsonify({"error": f"Explanation failed: {str(e)}"}), 500


# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    port = int(os.getenv("ML_SERVICE_PORT", 5000))
    print(f"\n🚀 ML Service starting on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)