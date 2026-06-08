"""
train_credit_model.py
Trains and evaluates three credit scoring models:
  1. Logistic Regression (baseline)
  2. Random Forest
  3. XGBoost (target: AUC-ROC >= 0.85)

Saves the best model + registers it in model_versions table.
Input : PostgreSQL → applicant_financials (joined with loan_applications)
Output: ml/models/credit_model_v1.joblib
        ml/models/credit_scaler_v1.joblib
"""
import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import numpy as np
import joblib
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from sklearn.model_selection    import train_test_split, StratifiedKFold, cross_val_score
from sklearn.linear_model       import LogisticRegression
from sklearn.ensemble           import RandomForestClassifier
from sklearn.preprocessing      import StandardScaler
from sklearn.metrics            import (
    classification_report, roc_auc_score,
    precision_score, recall_score, f1_score,
    confusion_matrix, RocCurveDisplay
)
from imblearn.over_sampling     import SMOTE
import xgboost                  as xgb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot        as plt
import warnings
warnings.filterwarnings('ignore')

load_dotenv()

# ── Config ─────────────────────────────────────────────────────────────────
DB_URL      = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
MODEL_DIR   = "ml/models"
EVAL_DIR    = "ml/evaluation"
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(EVAL_DIR,  exist_ok=True)

MODEL_VERSION = "v1.0.0"

# Features we feed into the model (all engineered + raw financial features)
FEATURE_COLS = [
    "age", "monthly_income", "debt_ratio", "revolving_utilization",
    "open_credit_lines", "real_estate_loans", "num_dependents",
    "late_30_59_days", "late_60_89_days", "late_90_days",
    "debt_to_income_ratio", "payment_consistency_score",
    "revolving_utilization_cat", "late_payment_frequency",
    "income_stability_flag"
]
TARGET_COL = "target"


# ══════════════════════════════════════════════════════════════════
#  STEP 1 — LOAD DATA FROM POSTGRESQL
# ══════════════════════════════════════════════════════════════════
def load_data_from_db():
    print("  [1/7] Loading data from PostgreSQL...")
    engine = create_engine(DB_URL)

    query = """
        SELECT
            af.age, af.monthly_income, af.debt_ratio,
            af.revolving_utilization, af.open_credit_lines,
            af.real_estate_loans, af.num_dependents,
            af.late_30_59_days, af.late_60_89_days, af.late_90_days,
            af.debt_to_income_ratio, af.payment_consistency_score,
            af.revolving_utilization_cat, af.late_payment_frequency,
            af.income_stability_flag,
            CASE WHEN la.status = 'REJECTED' THEN 1 ELSE 0 END AS target
        FROM applicant_financials af
        JOIN loan_applications la
          ON af.application_id = la.application_id
    """
    df = pd.read_sql(query, engine)
    print(f"         Loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"         Default rate: {df['target'].mean()*100:.1f}%")
    engine.dispose()
    return df


# ══════════════════════════════════════════════════════════════════
#  STEP 2 — PREPARE DATA
# ══════════════════════════════════════════════════════════════════
def prepare_data(df):
    print("\n  [2/7] Preparing data...")

    X = df[FEATURE_COLS].copy()
    y = df[TARGET_COL].copy()

    # Drop any remaining nulls
    mask = X.isnull().any(axis=1)
    if mask.sum() > 0:
        print(f"         Dropping {mask.sum()} rows with nulls")
        X, y = X[~mask], y[~mask]

    # Train / validation / test split  (60 / 20 / 20)
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.25, random_state=42, stratify=y_temp
    )

    print(f"         Train : {len(X_train):,} rows")
    print(f"         Val   : {len(X_val):,}   rows")
    print(f"         Test  : {len(X_test):,}  rows")
    print(f"         Class balance (train) — 0:{(y_train==0).sum():,}  1:{(y_train==1).sum():,}")

    # SMOTE on training set only — never on val/test
    print("         Applying SMOTE to fix class imbalance...")
    smote = SMOTE(random_state=42, k_neighbors=5)
    X_train_sm, y_train_sm = smote.fit_resample(X_train, y_train)
    print(f"         After SMOTE — 0:{(y_train_sm==0).sum():,}  1:{(y_train_sm==1).sum():,}")

    # Scale features (required for Logistic Regression)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_sm)
    X_val_scaled   = scaler.transform(X_val)
    X_test_scaled  = scaler.transform(X_test)

    # Save scaler for Flask service
    scaler_path = os.path.join(MODEL_DIR, f"credit_scaler_{MODEL_VERSION}.joblib")
    joblib.dump(scaler, scaler_path)
    print(f"         Scaler saved: {scaler_path}")

    return (X_train_sm, X_train_scaled, y_train_sm,
            X_val,  X_val_scaled,  y_val,
            X_test, X_test_scaled, y_test,
            scaler)


# ══════════════════════════════════════════════════════════════════
#  STEP 3 — EVALUATION HELPER
# ══════════════════════════════════════════════════════════════════
def evaluate(name, model, X, y, use_scaled=False, X_scaled=None):
    X_input = X_scaled if use_scaled else X
    y_pred  = model.predict(X_input)
    y_prob  = model.predict_proba(X_input)[:, 1]

    auc  = roc_auc_score(y, y_prob)
    prec = precision_score(y, y_pred, zero_division=0)
    rec  = recall_score(y, y_pred, zero_division=0)
    f1   = f1_score(y, y_pred, zero_division=0)
    cm   = confusion_matrix(y, y_pred)

    print(f"\n  ── {name} ──")
    print(f"     AUC-ROC   : {auc:.4f}  {'✅' if auc >= 0.85 else '⚠️ below target'}")
    print(f"     Precision : {prec:.4f}")
    print(f"     Recall    : {rec:.4f}")
    print(f"     F1 Score  : {f1:.4f}")
    print(f"     Confusion Matrix:")
    print(f"       TN={cm[0][0]:,}  FP={cm[0][1]:,}")
    print(f"       FN={cm[1][0]:,}  TP={cm[1][1]:,}")

    return {"auc": auc, "precision": prec, "recall": rec, "f1": f1, "proba": y_prob}


# ══════════════════════════════════════════════════════════════════
#  STEP 4 — MODEL 1: LOGISTIC REGRESSION (Baseline)
# ══════════════════════════════════════════════════════════════════
def train_logistic_regression(X_train_scaled, y_train, X_val, y_val, X_val_scaled):
    print("\n  [3/7] Training Model 1: Logistic Regression (Baseline)...")

    lr = LogisticRegression(
        C=1.0,
        max_iter=1000,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    lr.fit(X_train_scaled, y_train)
    metrics = evaluate("Logistic Regression (Val)", lr,
                        X_val, y_val, use_scaled=True, X_scaled=X_val_scaled)
    return lr, metrics


# ══════════════════════════════════════════════════════════════════
#  STEP 5 — MODEL 2: RANDOM FOREST
# ══════════════════════════════════════════════════════════════════
def train_random_forest(X_train, y_train, X_val, y_val):
    print("\n  [4/7] Training Model 2: Random Forest...")

    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_split=10,
        min_samples_leaf=5,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    metrics = evaluate("Random Forest (Val)", rf, X_val, y_val)
    return rf, metrics


# ══════════════════════════════════════════════════════════════════
#  STEP 6 — MODEL 3: XGBOOST
# ══════════════════════════════════════════════════════════════════
def train_xgboost(X_train, y_train, X_val, y_val):
    print("\n  [5/7] Training Model 3: XGBoost...")

    # Calculate scale_pos_weight for imbalanced data
    neg  = (y_train == 0).sum()
    pos  = (y_train == 1).sum()
    spw  = neg / pos
    print(f"         scale_pos_weight = {spw:.2f}")

    xgb_model = xgb.XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=spw,
        use_label_encoder=False,
        eval_metric='auc',
        early_stopping_rounds=50,
        random_state=42,
        n_jobs=-1,
        verbosity=0
    )

    xgb_model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )

    best_iter = xgb_model.best_iteration
    print(f"         Best iteration: {best_iter}")

    metrics = evaluate("XGBoost (Val)", xgb_model, X_val, y_val)
    return xgb_model, metrics


# ══════════════════════════════════════════════════════════════════
#  STEP 7 — SELECT BEST MODEL, EVALUATE ON TEST SET, SAVE
# ══════════════════════════════════════════════════════════════════
def select_and_save(models_metrics, X_test, y_test, X_test_scaled, scaler):
    print("\n  [6/7] Selecting best model by AUC-ROC on validation set...")

    lr_model,  lr_m  = models_metrics["Logistic Regression"]
    rf_model,  rf_m  = models_metrics["Random Forest"]
    xgb_model, xgb_m = models_metrics["XGBoost"]

    comparison = {
        "Logistic Regression": lr_m["auc"],
        "Random Forest":       rf_m["auc"],
        "XGBoost":             xgb_m["auc"]
    }

    print("\n  Model Comparison (Validation AUC-ROC):")
    for name, auc in sorted(comparison.items(), key=lambda x: -x[1]):
        bar   = "█" * int(auc * 40)
        flag  = " ← WINNER" if auc == max(comparison.values()) else ""
        print(f"    {name:<25} {auc:.4f}  {bar}{flag}")

    best_name  = max(comparison, key=comparison.get)
    best_model = {
        "Logistic Regression": lr_model,
        "Random Forest":       rf_model,
        "XGBoost":             xgb_model
    }[best_name]

    use_scaled = best_name == "Logistic Regression"
    X_test_input = X_test_scaled if use_scaled else X_test

    print(f"\n  [7/7] Final evaluation on HELD-OUT TEST SET...")
    test_metrics = evaluate(
        f"{best_name} (TEST SET — FINAL)",
        best_model, X_test, y_test,
        use_scaled=use_scaled, X_scaled=X_test_scaled
    )

    # Save model
    model_path = os.path.join(MODEL_DIR, f"credit_model_{MODEL_VERSION}.joblib")
    joblib.dump(best_model, model_path)
    print(f"\n         ✅ Best model saved: {model_path}")

    # Save metadata
    meta = {
        "model_name":    best_name,
        "version":       MODEL_VERSION,
        "trained_at":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "feature_cols":  FEATURE_COLS,
        "test_metrics": {
            "auc_roc":   round(test_metrics["auc"],  4),
            "precision": round(test_metrics["precision"], 4),
            "recall":    round(test_metrics["recall"], 4),
            "f1_score":  round(test_metrics["f1"], 4),
        },
        "model_path":    model_path,
    }
    meta_path = os.path.join(EVAL_DIR, f"credit_model_meta_{MODEL_VERSION}.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"         ✅ Metadata saved: {meta_path}")

    return best_model, best_name, test_metrics, meta


# ══════════════════════════════════════════════════════════════════
#  PLOT ROC CURVES
# ══════════════════════════════════════════════════════════════════
def plot_roc_curves(models_metrics, X_test, y_test, X_test_scaled):
    print("\n  Plotting ROC curves...")
    fig, ax = plt.subplots(figsize=(8, 6))

    colors = {"Logistic Regression": "#6366F1",
               "Random Forest":       "#10B981",
               "XGBoost":             "#F59E0B"}

    for name, (model, _) in models_metrics.items():
        use_scaled = name == "Logistic Regression"
        X_in = X_test_scaled if use_scaled else X_test
        RocCurveDisplay.from_estimator(model, X_in, y_test,
                                        ax=ax, name=name,
                                        color=colors[name])

    ax.plot([0,1],[0,1],'k--', linewidth=0.8, label='Random classifier')
    ax.axhline(y=0.85, color='red', linestyle=':', linewidth=1,
               label='Target AUC = 0.85')
    ax.set_title("ROC Curves — Credit Scoring Models", fontweight='bold')
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)

    path = os.path.join(EVAL_DIR, "roc_curves.png")
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"         ✅ ROC curve saved: {path}")


# ══════════════════════════════════════════════════════════════════
#  REGISTER MODEL IN POSTGRESQL
# ══════════════════════════════════════════════════════════════════
def register_model_in_db(meta):
    print("\n  Registering model in PostgreSQL model_versions table...")
    engine = create_engine(DB_URL)
    try:
        with engine.begin() as conn:
            # Deactivate all previous versions
            conn.execute(text(
                "UPDATE model_versions SET is_active = FALSE WHERE model_name = 'credit_scorer'"
            ))
            # Insert new version
            conn.execute(text("""
                INSERT INTO model_versions
                    (model_name, version_tag, auc_roc, precision_score,
                     recall_score, f1_score, feature_list, model_path, is_active)
                VALUES
                    (:name, :version, :auc, :prec,
                     :rec, :f1, :features, :path, TRUE)
            """), {
                "name":     "credit_scorer",
                "version":  meta["version"],
                "auc":      meta["test_metrics"]["auc_roc"],
                "prec":     meta["test_metrics"]["precision"],
                "rec":      meta["test_metrics"]["recall"],
                "f1":       meta["test_metrics"]["f1_score"],
                "features": json.dumps(meta["feature_cols"]),
                "path":     meta["model_path"]
            })
        print(f"         ✅ Model registered as active version {meta['version']}")
    except Exception as e:
        print(f"         ⚠️  DB registration failed: {e}")
    finally:
        engine.dispose()


# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("  CreditSense AI — Credit Scoring Model Trainer")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    df = load_data_from_db()

    (X_train, X_train_scaled, y_train,
     X_val,   X_val_scaled,   y_val,
     X_test,  X_test_scaled,  y_test,
     scaler) = prepare_data(df)

    lr_model,  lr_m  = train_logistic_regression(
                            X_train_scaled, y_train, X_val, y_val, X_val_scaled)
    rf_model,  rf_m  = train_random_forest(X_train, y_train, X_val, y_val)
    xgb_model, xgb_m = train_xgboost(X_train, y_train, X_val, y_val)

    models_metrics = {
        "Logistic Regression": (lr_model,  lr_m),
        "Random Forest":       (rf_model,  rf_m),
        "XGBoost":             (xgb_model, xgb_m),
    }

    best_model, best_name, test_metrics, meta = select_and_save(
        models_metrics, X_test, y_test, X_test_scaled, scaler
    )

    plot_roc_curves(models_metrics, X_test, y_test, X_test_scaled)
    register_model_in_db(meta)

    print("\n" + "=" * 60)
    print(f"  ✅ Training complete!")
    print(f"  Best model  : {best_name}")
    print(f"  Test AUC    : {test_metrics['auc']:.4f}  {'✅ TARGET MET' if test_metrics['auc'] >= 0.85 else '⚠️ below 0.85'}")
    print(f"  Saved at    : ml/models/credit_model_{MODEL_VERSION}.joblib")
    print("=" * 60)


if __name__ == "__main__":
    main()