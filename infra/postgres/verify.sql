SELECT 'users'               AS tbl, COUNT(*) AS rows FROM users
UNION ALL
SELECT 'loan_applications',          COUNT(*) FROM loan_applications
UNION ALL
SELECT 'applicant_financials',       COUNT(*) FROM applicant_financials
UNION ALL
SELECT 'transactions',               COUNT(*) FROM transactions
UNION ALL
SELECT 'etl_run_logs',               COUNT(*) FROM etl_run_logs;
