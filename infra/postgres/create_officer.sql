-- Create a dedicated officer test account
-- Password: Officer123 (bcrypt hash below)
INSERT INTO users (name, email, password_hash, role, is_active)
VALUES (
    'Test Officer',
    'officer@creditsense.ai',
    '$2a$12$8K1p/a0dURXAm7QiTRqGOOmYyQrOH3W5qChb8HXa4ZXlHhh2zJ5Ya',
    'OFFICER',
    true
)
ON CONFLICT (email) DO NOTHING;
