-- ============================================================
--  CreditSense AI — PostgreSQL Database Schema v1.0
--  Run with: psql -U creditsense_user -d creditsense_db -f infra/postgres/schema.sql
-- ============================================================

-- ── Extensions ────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Drop existing tables (safe re-run) ────────────────────────
DROP TABLE IF EXISTS fraud_alerts        CASCADE;
DROP TABLE IF EXISTS credit_assessments  CASCADE;
DROP TABLE IF EXISTS transactions        CASCADE;
DROP TABLE IF EXISTS applicant_financials CASCADE;
DROP TABLE IF EXISTS loan_applications   CASCADE;
DROP TABLE IF EXISTS model_versions      CASCADE;
DROP TABLE IF EXISTS etl_run_logs        CASCADE;
DROP TABLE IF EXISTS users               CASCADE;

-- ============================================================
--  TABLE 1: users
--  All system users: applicants, loan officers, admins
-- ============================================================
CREATE TABLE users (
    user_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(150)  NOT NULL,
    email       VARCHAR(255)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role        VARCHAR(20)   NOT NULL DEFAULT 'APPLICANT'
                    CHECK (role IN ('APPLICANT', 'OFFICER', 'ADMIN')),
    is_active   BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role  ON users(role);

-- ============================================================
--  TABLE 2: loan_applications
--  Core application entity. One row per loan request.
-- ============================================================
CREATE TABLE loan_applications (
    application_id  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    loan_amount     NUMERIC(15, 2) NOT NULL CHECK (loan_amount > 0),
    loan_purpose    VARCHAR(100)   NOT NULL,
    loan_term_months INT          NOT NULL CHECK (loan_term_months > 0),
    status          VARCHAR(20)   NOT NULL DEFAULT 'SUBMITTED'
                        CHECK (status IN ('SUBMITTED','UNDER_REVIEW','APPROVED','REJECTED')),
    reviewed_by     UUID          REFERENCES users(user_id),
    decision_notes  TEXT,
    submitted_at    TIMESTAMP     NOT NULL DEFAULT NOW(),
    reviewed_at     TIMESTAMP,
    decision_at     TIMESTAMP
);

CREATE INDEX idx_applications_user_id ON loan_applications(user_id);
CREATE INDEX idx_applications_status  ON loan_applications(status);
CREATE INDEX idx_applications_submitted_at ON loan_applications(submitted_at);

-- ============================================================
--  TABLE 3: applicant_financials
--  Detailed financial profile linked to an application.
--  These are the raw features fed into the ML model.
-- ============================================================
CREATE TABLE applicant_financials (
    financial_id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id              UUID NOT NULL UNIQUE
                                    REFERENCES loan_applications(application_id) ON DELETE CASCADE,
    age                         INT         NOT NULL CHECK (age BETWEEN 18 AND 100),
    monthly_income              NUMERIC(12,2) NOT NULL,
    debt_ratio                  NUMERIC(8,4)  NOT NULL,
    revolving_utilization       NUMERIC(8,4)  NOT NULL,
    open_credit_lines           INT         NOT NULL DEFAULT 0,
    real_estate_loans           INT         NOT NULL DEFAULT 0,
    num_dependents              INT         NOT NULL DEFAULT 0,
    late_30_59_days             INT         NOT NULL DEFAULT 0,
    late_60_89_days             INT         NOT NULL DEFAULT 0,
    late_90_days                INT         NOT NULL DEFAULT 0,

    -- Engineered features (computed by pipeline, stored for audit)
    debt_to_income_ratio        NUMERIC(8,4),
    payment_consistency_score   NUMERIC(6,2),
    revolving_utilization_cat   INT,
    late_payment_frequency      NUMERIC(8,4),
    income_stability_flag       INT DEFAULT 0,

    created_at                  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_financials_application_id ON applicant_financials(application_id);

-- ============================================================
--  TABLE 4: credit_assessments
--  ML model output for each application.
-- ============================================================
CREATE TABLE credit_assessments (
    assessment_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id      UUID NOT NULL UNIQUE
                            REFERENCES loan_applications(application_id) ON DELETE CASCADE,
    risk_score          NUMERIC(5,2) NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
    risk_category       VARCHAR(10)  NOT NULL CHECK (risk_category IN ('LOW','MEDIUM','HIGH')),
    confidence          NUMERIC(5,4) NOT NULL,
    model_version       VARCHAR(20)  NOT NULL,
    shap_explanation    JSONB,
    assessed_at         TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_assessments_application_id ON credit_assessments(application_id);
CREATE INDEX idx_assessments_risk_category  ON credit_assessments(risk_category);
CREATE INDEX idx_assessments_risk_score     ON credit_assessments(risk_score);

-- ============================================================
--  TABLE 5: transactions
--  All financial transactions submitted for fraud checking.
-- ============================================================
CREATE TABLE transactions (
    transaction_id       VARCHAR(20) PRIMARY KEY,
    user_id              UUID REFERENCES users(user_id),
    amount               NUMERIC(15,2) NOT NULL,
    merchant_category    VARCHAR(50),
    channel              VARCHAR(30),
    hour_of_day          INT          CHECK (hour_of_day BETWEEN 0 AND 23),
    day_of_week          INT          CHECK (day_of_week BETWEEN 0 AND 6),
    city                 VARCHAR(50),
    is_international     INT          NOT NULL DEFAULT 0,
    transactions_last_1h  INT         NOT NULL DEFAULT 0,
    transactions_last_24h INT         NOT NULL DEFAULT 0,
    avg_txn_amount_30d   NUMERIC(15,2),
    days_since_last_txn  INT          NOT NULL DEFAULT 0,
    account_age_days     INT          NOT NULL DEFAULT 0,
    num_failed_txns_24h  INT          NOT NULL DEFAULT 0,
    is_new_device        INT          NOT NULL DEFAULT 0,
    submitted_at         TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_transactions_user_id      ON transactions(user_id);
CREATE INDEX idx_transactions_submitted_at ON transactions(submitted_at);

-- ============================================================
--  TABLE 6: fraud_alerts
--  Fraud detection model output for each transaction.
-- ============================================================
CREATE TABLE fraud_alerts (
    alert_id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id          VARCHAR(20) NOT NULL
                                REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    anomaly_score           NUMERIC(8,6) NOT NULL,
    fraud_probability       NUMERIC(5,4) NOT NULL,
    is_fraudulent           BOOLEAN      NOT NULL DEFAULT FALSE,
    top_anomalous_features  JSONB,
    model_version           VARCHAR(20)  NOT NULL,
    detected_at             TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alerts_transaction_id ON fraud_alerts(transaction_id);
CREATE INDEX idx_alerts_is_fraudulent  ON fraud_alerts(is_fraudulent);
CREATE INDEX idx_alerts_detected_at    ON fraud_alerts(detected_at);

-- ============================================================
--  TABLE 7: model_versions
--  Registry of all trained ML models.
-- ============================================================
CREATE TABLE model_versions (
    version_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name      VARCHAR(50)   NOT NULL,
    version_tag     VARCHAR(20)   NOT NULL UNIQUE,
    auc_roc         NUMERIC(6,4)  NOT NULL,
    precision_score NUMERIC(6,4)  NOT NULL,
    recall_score    NUMERIC(6,4)  NOT NULL,
    f1_score        NUMERIC(6,4)  NOT NULL,
    feature_list    JSONB         NOT NULL,
    model_path      TEXT          NOT NULL,
    is_active       BOOLEAN       NOT NULL DEFAULT FALSE,
    trained_at      TIMESTAMP     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_model_versions_is_active ON model_versions(is_active);

-- ============================================================
--  TABLE 8: etl_run_logs
--  Audit trail for every ETL pipeline execution.
-- ============================================================
CREATE TABLE etl_run_logs (
    run_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pipeline_name     VARCHAR(100) NOT NULL,
    dataset_name      VARCHAR(100) NOT NULL,
    records_ingested  INT          NOT NULL DEFAULT 0,
    records_rejected  INT          NOT NULL DEFAULT 0,
    status            VARCHAR(20)  NOT NULL DEFAULT 'STARTED'
                          CHECK (status IN ('STARTED','SUCCESS','FAILED')),
    error_message     TEXT,
    started_at        TIMESTAMP    NOT NULL DEFAULT NOW(),
    completed_at      TIMESTAMP
);

CREATE INDEX idx_etl_logs_status     ON etl_run_logs(status);
CREATE INDEX idx_etl_logs_started_at ON etl_run_logs(started_at);

-- ============================================================
--  Seed: Insert 1 default admin user (password: Admin@123 → bcrypt)
--  Real bcrypt hash — do not change manually, Spring Boot will verify
-- ============================================================

-- Confirmation message
SELECT
    'Schema created successfully' AS status,
    COUNT(*) AS table_count
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type   = 'BASE TABLE';