import joblib
import pandas as pd
import numpy as np

explainer = joblib.load("ml/models/shap_explainer_v1.2.0.joblib")

FEATURE_COLS = [
    "age", "monthly_income", "debt_ratio", "revolving_utilization",
    "open_credit_lines", "real_estate_loans", "num_dependents",
    "late_30_59_days", "late_60_89_days", "late_90_days",
    "debt_to_income_ratio", "payment_consistency_score",
    "revolving_utilization_cat", "late_payment_frequency",
    "income_stability_flag"
]

base = {
    "age": 35, "monthly_income": 65000, "debt_ratio": 0.25,
    "revolving_utilization": 0.3, "open_credit_lines": 5,
    "real_estate_loans": 1, "num_dependents": 2,
    "late_30_59_days": 0, "late_60_89_days": 0, "late_90_days": 0,
    "debt_to_income_ratio": 0.25, "payment_consistency_score": 50,
    "revolving_utilization_cat": 1, "late_payment_frequency": 0,
    "income_stability_flag": 0
}

print("pcs_value | shap_value | direction")
for pcs in [0, 25, 50, 75, 90, 100]:
    row = base.copy()
    row["payment_consistency_score"] = pcs
    X = pd.DataFrame([row])[FEATURE_COLS]
    sv = explainer.shap_values(X)[0]
    pcs_shap = sv[FEATURE_COLS.index("payment_consistency_score")]
    direction = "increases_risk" if pcs_shap > 0 else "decreases_risk"
    print(f"{pcs:>9} | {pcs_shap:>10.4f} | {direction}")
