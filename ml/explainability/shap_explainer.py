"""
shap_explainer.py
Generates SHAP explanations for the trained XGBoost credit scoring model.

Produces:
  - Global feature importance chart (what matters most across all applicants)
  - Individual waterfall chart (why THIS applicant got THIS score)
  - Saved SHAP explainer object for use in Flask API
  - SHAP values stored for sample predictions

Input : ml/models/credit_model_v1.0.0.joblib
Output: ml/models/shap_explainer_v1.0.0.joblib
        ml/evaluation/shap_summary_plot.png
        ml/evaluation/shap_waterfall_sample.png
        ml/evaluation/shap_feature_importance.json
"""
import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import numpy as np
import joblib
import shap
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

load_dotenv()

# ── Config ─────────────────────────────────────────────────────────────────
DB_URL    = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
MODEL_PATH    = "ml/models/credit_model_v1.2.0.joblib"
EXPLAINER_PATH= "ml/models/shap_explainer_v1.2.0.joblib"
EVAL_DIR      = "ml/evaluation"
MODEL_VERSION = "v1.2.0"

FEATURE_COLS = [
    "age", "monthly_income", "debt_ratio", "revolving_utilization",
    "open_credit_lines", "real_estate_loans", "num_dependents",
    "late_30_59_days", "late_60_89_days", "late_90_days",
    "debt_to_income_ratio", "payment_consistency_score",
    "revolving_utilization_cat", "late_payment_frequency",
    "income_stability_flag"
]

# Human-readable feature names for charts and API responses
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


# ══════════════════════════════════════════════════════════════════
#  STEP 1 — LOAD MODEL + SAMPLE DATA
# ══════════════════════════════════════════════════════════════════
def load_model_and_data():
    print("  [1/6] Loading model and sample data...")
    model = joblib.load(MODEL_PATH)

    # CalibratedClassifierCV wraps the real tree model — extract it for SHAP
    if hasattr(model, "calibrated_classifiers_"):
        base_model = model.calibrated_classifiers_[0].estimator
        print(f"         Detected calibrated model — using base estimator for SHAP")
    else:
        base_model = model

    print(f"         Model loaded: {MODEL_PATH}")
    ...
    # use base_model for explainer, but 'model' for predict_proba in demo section

    engine = create_engine(DB_URL)
    query  = f"""
        SELECT {', '.join([f'af.{c}' for c in FEATURE_COLS])}
        FROM applicant_financials af
        LIMIT 5000
    """
    df = pd.read_sql(query, engine)
    engine.dispose()
    print(f"         Sample data: {df.shape[0]:,} rows loaded for SHAP analysis")
    return base_model, df


# ══════════════════════════════════════════════════════════════════
#  STEP 2 — BUILD SHAP EXPLAINER
# ════════════════════════════════════════════════════════════════════
def build_explainer(base_model, X_sample):
    """
    TreeExplainer is the fastest and most accurate SHAP method for
    tree-based models like XGBoost and Random Forest.
    It computes exact Shapley values (not approximations).
    """
    print("\n  [2/6] Building SHAP TreeExplainer...")
    explainer   = shap.TreeExplainer(base_model)
    shap_values = explainer(X_sample)

    print(f"         SHAP values shape: {shap_values.values.shape}")
    print(f"         Base value (expected output): {explainer.expected_value:.4f}")

    # Save explainer for use in Flask API
    joblib.dump(explainer, EXPLAINER_PATH)
    print(f"         ✅ Explainer saved: {EXPLAINER_PATH}")

    return explainer, shap_values


# ══════════════════════════════════════════════════════════════════
#  STEP 3 — GLOBAL FEATURE IMPORTANCE (Summary Plot)
# ══════════════════════════════════════════════════════════════════
def plot_global_importance(shap_values, X_sample):
    """
    Shows which features have the biggest OVERALL impact across all predictions.
    This is the chart you show to the bank manager: 'What drives defaults?'
    """
    print("\n  [3/6] Plotting global feature importance...")

    # Rename columns to human-readable names for the chart
    X_display = X_sample.copy()
    X_display.columns = [FEATURE_DISPLAY_NAMES.get(c, c) for c in X_sample.columns]

    fig, ax = plt.subplots(figsize=(10, 7))
    shap.summary_plot(
        shap_values.values,
        X_display,
        plot_type="bar",
        show=False,
        color="#2563EB"
    )
    plt.title("Global Feature Importance — CreditSense AI\n(Mean |SHAP Value| across 5,000 applicants)",
              fontweight='bold', fontsize=13, pad=15)
    plt.xlabel("Mean |SHAP Value| (Average Impact on Model Output)")
    plt.tight_layout()

    path = os.path.join(EVAL_DIR, "shap_global_importance.png")
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"         ✅ Chart saved: {path}")


# ══════════════════════════════════════════════════════════════════
#  STEP 4 — SHAP BEE SWARM (Feature Direction Plot)
# ══════════════════════════════════════════════════════════════════
def plot_beeswarm(shap_values, X_sample):
    """
    Beeswarm shows both importance AND direction:
      - Red dots = high feature value
      - Blue dots = low feature value
      - Right of center = increases default risk
      - Left of center  = decreases default risk
    """
    print("\n  [4/6] Plotting SHAP beeswarm (feature direction)...")

    X_display = X_sample.copy()
    X_display.columns = [FEATURE_DISPLAY_NAMES.get(c, c) for c in X_sample.columns]

    fig, ax = plt.subplots(figsize=(10, 7))
    shap.summary_plot(
        shap_values.values,
        X_display,
        show=False
    )
    plt.title("Feature Impact Direction — CreditSense AI\n(Red=High Value, Blue=Low Value)",
              fontweight='bold', fontsize=13, pad=15)
    plt.tight_layout()

    path = os.path.join(EVAL_DIR, "shap_beeswarm.png")
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"         ✅ Chart saved: {path}")


# ══════════════════════════════════════════════════════════════════
#  STEP 5 — INDIVIDUAL WATERFALL PLOTS (3 samples)
# ══════════════════════════════════════════════════════════════════
def plot_individual_explanations(explainer, X_sample, base_model):
    """
    Waterfall chart explains ONE specific prediction:
    'Why did applicant #42 get a HIGH risk score?'
    Shows each feature's contribution: positive (pushes toward default)
    and negative (pushes toward non-default).
    """
    print("\n  [5/6] Plotting individual SHAP waterfall explanations...")

    y_prob = base_model.predict_proba(X_sample)[:, 1]

    # Pick 3 representative samples: low risk, medium risk, high risk
    samples = {
        "Low Risk Applicant":    X_sample.iloc[np.argmin(y_prob)],
        "Medium Risk Applicant": X_sample.iloc[len(y_prob)//2],
        "High Risk Applicant":   X_sample.iloc[np.argmax(y_prob)],
    }

    for label, sample_row in samples.items():
        idx = X_sample.index.get_loc(sample_row.name)

        # Rename to display names
        sample_display = sample_row.copy()
        sample_display.index = [FEATURE_DISPLAY_NAMES.get(c, c) for c in sample_row.index]

        shap_exp = shap.Explanation(
            values        = explainer.shap_values(X_sample.iloc[[idx]])[0],
            base_values   = explainer.expected_value,
            data          = sample_display.values,
            feature_names = list(sample_display.index)
        )

        fig, ax = plt.subplots(figsize=(10, 6))
        shap.waterfall_plot(shap_exp, max_display=10, show=False)
        risk_pct = y_prob[idx] * 100
        plt.title(f"{label} — Default Probability: {risk_pct:.1f}%",
                  fontweight='bold', fontsize=12)
        plt.tight_layout()

        filename = label.lower().replace(" ", "_") + "_waterfall.png"
        path = os.path.join(EVAL_DIR, filename)
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"         ✅ {label}: {risk_pct:.1f}% default prob → {path}")


# ══════════════════════════════════════════════════════════════════
#  STEP 6 — SAVE FEATURE IMPORTANCE JSON (for Flask API)
# ══════════════════════════════════════════════════════════════════
def save_feature_importance_json(shap_values, X_sample):
    """
    Save mean absolute SHAP values as JSON.
    The Flask /explain endpoint loads this to quickly return
    global feature importance without re-computing SHAP each time.
    """
    print("\n  [6/6] Saving feature importance JSON for Flask API...")

    mean_shap = np.abs(shap_values.values).mean(axis=0)
    importance = sorted(
        [
            {
                "feature":      col,
                "display_name": FEATURE_DISPLAY_NAMES.get(col, col),
                "mean_shap":    round(float(val), 6),
                "rank":         int(rank) + 1
            }
            for rank, (col, val) in enumerate(
                sorted(zip(FEATURE_COLS, mean_shap), key=lambda x: -x[1])
            )
        ],
        key=lambda x: x["rank"]
    )

    path = os.path.join(EVAL_DIR, "shap_feature_importance.json")
    with open(path, "w") as f:
        json.dump(importance, f, indent=2)

    print(f"         ✅ Saved: {path}")
    print(f"\n  Top 5 Features by Global SHAP Importance:")
    for item in importance[:5]:
        bar = "█" * int(item["mean_shap"] * 300)
        print(f"    #{item['rank']}  {item['display_name']:<35} {item['mean_shap']:.4f}  {bar}")

    return importance


# ══════════════════════════════════════════════════════════════════
#  EXPLAIN SINGLE APPLICANT — Used by Flask API
# ══════════════════════════════════════════════════════════════════
def explain_single(explainer, feature_vector: dict, top_n: int = 5) -> list:
    """
    Generates SHAP explanation for a single applicant.
    Called by the Flask /explain endpoint at prediction time.

    Args:
        explainer:      Loaded SHAP TreeExplainer object
        feature_vector: Dict of {feature_name: value} for one applicant
        top_n:          Number of top features to return

    Returns:
        List of dicts: [{feature, display_name, value, shap_value, direction}, ...]
    """
    X = pd.DataFrame([feature_vector])[FEATURE_COLS]
    shap_vals = explainer.shap_values(X)[0]

    explanation = []
    for col, shap_val, feat_val in zip(FEATURE_COLS, shap_vals, X.iloc[0]):
        explanation.append({
            "feature":      col,
            "display_name": FEATURE_DISPLAY_NAMES.get(col, col),
            "value":        round(float(feat_val), 4),
            "shap_value":   round(float(shap_val), 6),
            "direction":    "increases_risk" if shap_val > 0 else "decreases_risk",
            "abs_impact":   abs(float(shap_val))
        })

    # Sort by absolute impact, return top N
    explanation.sort(key=lambda x: -x["abs_impact"])
    return explanation[:top_n]


# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("  CreditSense AI — SHAP Explainability")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    base_model, X_sample = load_model_and_data()
    explainer, shap_values = build_explainer(base_model, X_sample)
    plot_global_importance(shap_values, X_sample)
    plot_beeswarm(shap_values, X_sample)
    plot_individual_explanations(explainer, X_sample, base_model)
    importance = save_feature_importance_json(shap_values, X_sample)

    # Demo: explain one applicant the way the Flask API will
    print("\n  Demo: Single applicant explanation (Flask API preview)...")
    sample_input = dict(zip(FEATURE_COLS, X_sample.iloc[0].values))
    top_features = explain_single(explainer, sample_input, top_n=5)
    print("  Top 5 features for Applicant #1:")
    for f in top_features:
        arrow = "▲ RISK" if f["direction"] == "increases_risk" else "▼ safe"
        print(f"    {f['display_name']:<35} SHAP={f['shap_value']:+.4f}  {arrow}")

    print("\n" + "=" * 60)
    print("  ✅ SHAP Explainability complete!")
    print(f"  Charts saved in: {EVAL_DIR}/")
    print(f"  Explainer saved: {EXPLAINER_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()