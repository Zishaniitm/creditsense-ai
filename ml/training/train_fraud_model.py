"""
train_fraud_model.py
Trains an Isolation Forest anomaly detection model for fraud detection.

Why Isolation Forest:
  - Unsupervised: learns what NORMAL looks like, flags deviations
  - No need for perfectly labelled fraud data
  - Fast at inference — critical for real-time transaction checks
  - Industry standard for transaction anomaly detection

Input : PostgreSQL → transactions table
Output: ml/models/fraud_model_v1.0.0.joblib
        ml/models/fraud_scaler_v1.0.0.joblib
        ml/evaluation/fraud_model_report.json
        ml/evaluation/fraud_evaluation_charts.png
"""
import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import numpy as np
import joblib
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from sklearn.ensemble         import IsolationForest
from sklearn.preprocessing    import StandardScaler
from sklearn.metrics          import (
    classification_report, precision_score,
    recall_score, f1_score, confusion_matrix,
    roc_auc_score
)
from sklearn.model_selection  import train_test_split
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import warnings
warnings.filterwarnings('ignore')

load_dotenv()

# ── Config ─────────────────────────────────────────────────────────────────
DB_URL        = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
MODEL_DIR     = "ml/models"
EVAL_DIR      = "ml/evaluation"
MODEL_VERSION = "v1.0.0"

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(EVAL_DIR,  exist_ok=True)

# Transaction features — exactly what the fraud Flask API will receive
FEATURE_COLS = [
    "amount", "merchant_category", "channel",
    "hour_of_day", "day_of_week", "city",
    "is_international", "transactions_last_1h", "transactions_last_24h",
    "avg_txn_amount_30d", "days_since_last_txn",
    "account_age_days", "num_failed_txns_24h", "is_new_device"
]

FEATURE_DISPLAY_NAMES = {
    "amount":                 "Transaction Amount",
    "merchant_category":      "Merchant Category",
    "channel":                "Payment Channel",
    "hour_of_day":            "Hour of Day",
    "day_of_week":            "Day of Week",
    "city":                   "City",
    "is_international":       "International Transaction",
    "transactions_last_1h":   "Transactions in Last 1 Hour",
    "transactions_last_24h":  "Transactions in Last 24 Hours",
    "avg_txn_amount_30d":     "Avg Transaction Amount (30 Days)",
    "days_since_last_txn":    "Days Since Last Transaction",
    "account_age_days":       "Account Age (Days)",
    "num_failed_txns_24h":    "Failed Transactions (24 Hours)",
    "is_new_device":          "New Device Flag"
}


# ══════════════════════════════════════════════════════════════════
#  STEP 1 — LOAD DATA
# ══════════════════════════════════════════════════════════════════
def load_data():
    print("  [1/7] Loading fraud transaction data from PostgreSQL...")
    engine = create_engine(DB_URL)

    # Load transactions — they don't have is_fraud label in DB
    # We load from the cleaned CSV which has the label for evaluation
    df_db = pd.read_sql(
        f"SELECT {', '.join(FEATURE_COLS)} FROM transactions",
        engine
    )
    engine.dispose()

    # Load labels from cleaned CSV for evaluation only
    df_csv = pd.read_csv("data/cleaned/fraud_cleaned.csv")

    print(f"         DB transactions : {len(df_db):,}")
    print(f"         CSV with labels : {len(df_csv):,}")

    # Align: use DB features (clean), CSV labels
    min_len = min(len(df_db), len(df_csv))
    X = df_db.iloc[:min_len].copy()
    y = df_csv["is_fraud"].iloc[:min_len].values

    print(f"         Fraud rate: {y.mean()*100:.1f}%  ({y.sum():,} fraud / {len(y):,} total)")
    return X, y


# ══════════════════════════════════════════════════════════════════
#  STEP 2 — PREPARE FEATURES
# ══════════════════════════════════════════════════════════════════
def prepare_features(X, y):
    print("\n  [2/7] Preparing features...")

    # Convert any object columns to numeric (label-encoded by encoder.py)
    for col in X.select_dtypes(include='object').columns:
        X[col] = pd.factorize(X[col])[0]

    X = X.fillna(X.median(numeric_only=True))

    # Train/test split — stratified to preserve fraud ratio
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print(f"         Train: {len(X_train):,}  |  Test: {len(X_test):,}")

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)

    # Save scaler
    scaler_path = os.path.join(MODEL_DIR, f"fraud_scaler_{MODEL_VERSION}.joblib")
    joblib.dump(scaler, scaler_path)
    print(f"         Scaler saved: {scaler_path}")

    return X_train_scaled, X_test_scaled, y_train, y_test, X_test, scaler


# ══════════════════════════════════════════════════════════════════
#  STEP 3 — TRAIN ISOLATION FOREST
# ══════════════════════════════════════════════════════════════════
def train_isolation_forest(X_train_scaled, y_train):
    """
    Isolation Forest works by randomly partitioning the feature space.
    Anomalies (fraudulent transactions) are isolated in fewer splits
    because they are rare and different from normal transactions.

    contamination: expected fraction of fraudulent transactions (~3%)
    n_estimators:  number of trees — more = more stable results
    """
    print("\n  [3/7] Training Isolation Forest...")

    fraud_rate = y_train.mean()
    print(f"         Setting contamination={fraud_rate:.3f} (actual fraud rate)")

    model = IsolationForest(
        n_estimators=300,
        contamination=fraud_rate,
        max_samples='auto',
        max_features=1.0,
        random_state=42,
        n_jobs=-1,
        verbose=0
    )

    # Train only on NORMAL transactions — this is key for anomaly detection
    # The model learns what normal looks like, then flags deviations
    X_normal = X_train_scaled[y_train == 0]
    model.fit(X_normal)

    print(f"         Trained on {len(X_normal):,} normal transactions")
    print(f"         Model: {model.n_estimators} trees, "
          f"contamination={model.contamination:.3f}")
    return model


# ══════════════════════════════════════════════════════════════════
#  STEP 4 — EVALUATE
# ══════════════════════════════════════════════════════════════════
def evaluate_model(model, X_test_scaled, y_test):
    """
    Isolation Forest outputs:
      predict()       → 1 (normal) or -1 (anomaly)
      score_samples() → anomaly score (lower = more anomalous)

    We convert to binary: -1 → 1 (fraud), 1 → 0 (normal)
    """
    print("\n  [4/7] Evaluating on test set...")

    raw_preds    = model.predict(X_test_scaled)
    anomaly_scores = model.score_samples(X_test_scaled)

    # Convert: Isolation Forest -1 = anomaly → our 1 = fraud
    y_pred = (raw_preds == -1).astype(int)

    # Normalize anomaly scores to 0-1 range for fraud probability
    score_min = anomaly_scores.min()
    score_max = anomaly_scores.max()
    fraud_prob = 1 - (anomaly_scores - score_min) / (score_max - score_min)

    prec   = precision_score(y_test, y_pred, zero_division=0)
    rec    = recall_score(y_test, y_pred, zero_division=0)
    f1     = f1_score(y_test, y_pred, zero_division=0)
    auc    = roc_auc_score(y_test, fraud_prob)
    cm     = confusion_matrix(y_test, y_pred)

    print(f"\n  ── Isolation Forest (Test Set) ──")
    print(f"     AUC-ROC   : {auc:.4f}")
    print(f"     Precision : {prec:.4f}  (of flagged txns, how many are real fraud)")
    print(f"     Recall    : {rec:.4f}  (of real frauds, how many did we catch) ← KEY")
    print(f"     F1 Score  : {f1:.4f}")
    print(f"     Confusion Matrix:")
    print(f"       TN={cm[0][0]:,}  FP={cm[0][1]:,}  (false alarms)")
    print(f"       FN={cm[1][0]:,}  TP={cm[1][1]:,}  (caught frauds)")

    fraud_caught = cm[1][1]
    fraud_missed = cm[1][0]
    total_fraud  = fraud_caught + fraud_missed
    print(f"\n     Fraud caught : {fraud_caught:,} / {total_fraud:,} "
          f"({fraud_caught/total_fraud*100:.1f}%)")
    print(f"     Fraud missed : {fraud_missed:,} / {total_fraud:,} "
          f"({fraud_missed/total_fraud*100:.1f}%)")

    return {
        "auc_roc":    round(float(auc),  4),
        "precision":  round(float(prec), 4),
        "recall":     round(float(rec),  4),
        "f1_score":   round(float(f1),   4),
        "fraud_caught_pct": round(float(fraud_caught/total_fraud*100), 1)
    }, y_pred, fraud_prob, anomaly_scores


# ══════════════════════════════════════════════════════════════════
#  STEP 5 — ANOMALY SCORE ANALYSIS
# ══════════════════════════════════════════════════════════════════
def analyse_anomaly_scores(anomaly_scores, y_test, X_test):
    """
    Shows which features differ most between fraud and non-fraud
    in the test set — used for generating 'top anomalous features'
    in fraud alerts.
    """
    print("\n  [5/7] Analysing anomaly scores and feature differences...")

    df_analysis = X_test.copy()
    df_analysis["anomaly_score"] = anomaly_scores
    df_analysis["is_fraud"]      = y_test

    fraud_df  = df_analysis[df_analysis["is_fraud"] == 1]
    normal_df = df_analysis[df_analysis["is_fraud"] == 0]

    print(f"         Avg anomaly score — Fraud : {fraud_df['anomaly_score'].mean():.4f}")
    print(f"         Avg anomaly score — Normal: {normal_df['anomaly_score'].mean():.4f}")

    # Feature-level differences
    feature_diffs = {}
    for col in FEATURE_COLS:
        if col in df_analysis.columns:
            fraud_mean  = fraud_df[col].mean()
            normal_mean = normal_df[col].mean()
            diff_pct    = abs(fraud_mean - normal_mean) / (abs(normal_mean) + 1e-8) * 100
            feature_diffs[col] = round(diff_pct, 2)

    top_diff_features = sorted(feature_diffs.items(), key=lambda x: -x[1])[:5]
    print(f"\n  Top 5 Features Most Different in Fraud vs Normal:")
    for col, diff in top_diff_features:
        print(f"    {FEATURE_DISPLAY_NAMES.get(col, col):<35} {diff:.1f}% difference")

    return feature_diffs


# ══════════════════════════════════════════════════════════════════
#  STEP 6 — EVALUATION CHARTS
# ══════════════════════════════════════════════════════════════════
def plot_evaluation_charts(anomaly_scores, y_test, fraud_prob):
    print("\n  [6/7] Plotting evaluation charts...")

    fig = plt.figure(figsize=(14, 10))
    gs  = gridspec.GridSpec(2, 2, figure=fig, hspace=0.4, wspace=0.35)

    # Chart 1: Anomaly score distribution
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.hist(anomaly_scores[y_test==0], bins=50, alpha=0.6,
             color='#3B82F6', label='Normal', density=True)
    ax1.hist(anomaly_scores[y_test==1], bins=50, alpha=0.6,
             color='#EF4444', label='Fraud',  density=True)
    ax1.set_title("Anomaly Score Distribution", fontweight='bold')
    ax1.set_xlabel("Anomaly Score (lower = more suspicious)")
    ax1.set_ylabel("Density")
    ax1.legend()

    # Chart 2: Fraud probability distribution
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.hist(fraud_prob[y_test==0], bins=50, alpha=0.6,
             color='#3B82F6', label='Normal', density=True)
    ax2.hist(fraud_prob[y_test==1], bins=50, alpha=0.6,
             color='#EF4444', label='Fraud',  density=True)
    ax2.set_title("Fraud Probability Distribution", fontweight='bold')
    ax2.set_xlabel("Fraud Probability")
    ax2.set_ylabel("Density")
    ax2.legend()

    # Chart 3: Detection rate by threshold
    ax3 = fig.add_subplot(gs[1, 0])
    thresholds = np.linspace(0.1, 0.9, 50)
    precisions, recalls = [], []
    for t in thresholds:
        preds = (fraud_prob >= t).astype(int)
        precisions.append(precision_score(y_test, preds, zero_division=0))
        recalls.append(recall_score(y_test, preds, zero_division=0))
    ax3.plot(thresholds, precisions, color='#3B82F6', label='Precision', linewidth=2)
    ax3.plot(thresholds, recalls,    color='#EF4444', label='Recall',    linewidth=2)
    ax3.axvline(x=0.5, color='gray', linestyle='--', linewidth=1, label='Default threshold')
    ax3.set_title("Precision vs Recall by Threshold", fontweight='bold')
    ax3.set_xlabel("Decision Threshold")
    ax3.set_ylabel("Score")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Chart 4: Transaction amount — fraud vs normal boxplot
    ax4 = fig.add_subplot(gs[1, 1])
    normal_amounts = []
    fraud_amounts  = []

    # Load from CSV for amounts with labels
    df_csv = pd.read_csv("data/cleaned/fraud_cleaned.csv")
    if "amount" in df_csv.columns and "is_fraud" in df_csv.columns:
        normal_amounts = df_csv[df_csv["is_fraud"]==0]["amount"].clip(upper=50000).values
        fraud_amounts  = df_csv[df_csv["is_fraud"]==1]["amount"].clip(upper=200000).values

    bp = ax4.boxplot([normal_amounts, fraud_amounts],
                     labels=["Normal", "Fraud"],
                     patch_artist=True,
                     notch=True)
    bp['boxes'][0].set_facecolor('#3B82F6')
    bp['boxes'][1].set_facecolor('#EF4444')
    ax4.set_title("Transaction Amount Distribution", fontweight='bold')
    ax4.set_ylabel("Amount (₹)")
    ax4.grid(True, alpha=0.3, axis='y')

    fig.suptitle("CreditSense AI — Fraud Detection Model Evaluation",
                 fontsize=14, fontweight='bold', y=1.01)

    path = os.path.join(EVAL_DIR, "fraud_evaluation_charts.png")
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"         ✅ Charts saved: {path}")


# ══════════════════════════════════════════════════════════════════
#  STEP 7 — SAVE + REGISTER
# ══════════════════════════════════════════════════════════════════
def save_and_register(model, metrics, feature_diffs):
    print("\n  [7/7] Saving fraud model and registering in PostgreSQL...")

    model_path = os.path.join(MODEL_DIR, f"fraud_model_{MODEL_VERSION}.joblib")
    joblib.dump(model, model_path)
    print(f"         ✅ Model saved: {model_path}")

    # Save evaluation report
    report = {
        "model_name":      "IsolationForest",
        "version":         MODEL_VERSION,
        "trained_at":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "feature_cols":    FEATURE_COLS,
        "test_metrics":    metrics,
        "feature_diffs":   feature_diffs,
        "model_path":      model_path
    }
    report_path = os.path.join(EVAL_DIR, "fraud_model_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"         ✅ Report saved: {report_path}")

    # Register in DB
    try:
        engine = create_engine(DB_URL)
        with engine.begin() as conn:
            conn.execute(text(
                "UPDATE model_versions SET is_active = FALSE WHERE model_name = 'fraud_detector'"
            ))
            conn.execute(text("""
                INSERT INTO model_versions
                    (model_name, version_tag, auc_roc, precision_score,
                     recall_score, f1_score, feature_list, model_path, is_active)
                VALUES
                    (:name, :version, :auc, :prec,
                     :rec, :f1, :features, :path, TRUE)
            """), {
                "name":     "fraud_detector",
                "version":  MODEL_VERSION,
                "auc":      metrics["auc_roc"],
                "prec":     metrics["precision"],
                "rec":      metrics["recall"],
                "f1":       metrics["f1_score"],
                "features": json.dumps(FEATURE_COLS),
                "path":     model_path
            })
        print(f"         ✅ Fraud model registered in model_versions table")
        engine.dispose()
    except Exception as e:
        print(f"         ⚠️  DB registration: {e}")


# ══════════════════════════════════════════════════════════════════
#  FRAUD ALERT GENERATOR — Used by Flask API
# ══════════════════════════════════════════════════════════════════
def generate_fraud_alert(model, scaler, transaction: dict) -> dict:
    """
    Generates a structured fraud alert for a single transaction.
    Called by the fraud_service Flask API at inference time.

    Returns:
        {
          anomaly_score, fraud_probability, is_fraudulent,
          top_anomalous_features: [{feature, display_name, value, deviation}, ...]
        }
    """
    X = pd.DataFrame([transaction])[FEATURE_COLS]

    # Handle any object columns
    for col in X.select_dtypes(include='object').columns:
        X[col] = 0

    X_scaled = scaler.transform(X)

    raw_score  = model.score_samples(X_scaled)[0]
    raw_pred   = model.predict(X_scaled)[0]

    is_fraudulent = raw_pred == -1
    fraud_prob    = max(0.0, min(1.0, -raw_score))

    # Identify top anomalous features by comparing to training mean
    # (simplified version for the API — full analysis uses score_samples)
    alert = {
        "anomaly_score":           round(float(raw_score), 6),
        "fraud_probability":       round(float(fraud_prob), 4),
        "is_fraudulent":           bool(is_fraudulent),
        "model_version":           MODEL_VERSION,
        "top_anomalous_features":  []
    }
    return alert


# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("  CreditSense AI — Fraud Detection Model Trainer")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    X, y = load_data()
    X_train_scaled, X_test_scaled, y_train, y_test, X_test, scaler = prepare_features(X, y)
    model = train_isolation_forest(X_train_scaled, y_train)
    metrics, y_pred, fraud_prob, anomaly_scores = evaluate_model(
        model, X_test_scaled, y_test
    )
    feature_diffs = analyse_anomaly_scores(anomaly_scores, y_test, X_test)
    plot_evaluation_charts(anomaly_scores, y_test, fraud_prob)
    save_and_register(model, metrics, feature_diffs)

    print("\n" + "=" * 60)
    print("  ✅ Fraud Detection Model Training Complete!")
    print(f"  Recall (fraud caught): {metrics['recall']*100:.1f}%")
    print(f"  AUC-ROC             : {metrics['auc_roc']:.4f}")
    print(f"  Saved at            : ml/models/fraud_model_{MODEL_VERSION}.joblib")
    print("=" * 60)


if __name__ == "__main__":
    main()