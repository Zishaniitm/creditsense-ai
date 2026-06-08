INSERT INTO model_versions
    (model_name, version_tag, auc_roc, precision_score,
     recall_score, f1_score, feature_list, model_path, is_active)
VALUES (
    'fraud_detector',
    'fraud-v1.0.0',
    0.9954,
    0.4928,
    0.9667,
    0.6528,
    '["amount","merchant_category","channel","hour_of_day","day_of_week","city","is_international","transactions_last_1h","transactions_last_24h","avg_txn_amount_30d","days_since_last_txn","account_age_days","num_failed_txns_24h","is_new_device"]',
    'ml/models/fraud_model_v1.0.0.joblib',
    TRUE
);
