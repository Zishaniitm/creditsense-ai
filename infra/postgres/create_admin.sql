INSERT INTO users (name, email, password_hash, role, is_active)
VALUES (
    'System Admin',
    'admin@creditsense.ai',
    '$2b$12$NZwNnVTUvTEf/M0sL1FUCeO5krsDJvl9nkgPdjnI9oK5ISB6xCazK
',
    'ADMIN',
    true
)
ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash;
