TRUNCATE TABLE fraud_alerts CASCADE;
TRUNCATE TABLE transactions CASCADE;
TRUNCATE TABLE applicant_financials CASCADE;
TRUNCATE TABLE credit_assessments CASCADE;
TRUNCATE TABLE loan_applications CASCADE;
DELETE FROM users WHERE role = 'APPLICANT';
DELETE FROM etl_run_logs;
