"""
fix_admin_password.py
Generates a fresh BCrypt hash and updates it directly in PostgreSQL.
Bypasses terminal copy-paste entirely to avoid hash corruption.
"""
import bcrypt
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL    = "admin@creditsense.ai"
PASSWORD = "Admin@123"

# Generate fresh hash
hashed = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(rounds=12)).decode()
print(f"Generated hash ({len(hashed)} chars): {hashed}")
assert len(hashed) == 60, "Hash length is wrong — generation failed"

# Connect directly to PostgreSQL and update — no shell, no copy-paste
conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432"),
    dbname=os.getenv("DB_NAME", "creditsense_db"),
    user=os.getenv("DB_USER", "creditsense_user"),
    password=os.getenv("DB_PASSWORD")
)
cur = conn.cursor()

cur.execute("""
    INSERT INTO users (name, email, password_hash, role, is_active)
    VALUES (%s, %s, %s, 'ADMIN', true)
    ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash
""", ("System Admin", EMAIL, hashed))

conn.commit()

# Verify immediately
cur.execute("SELECT email, LENGTH(password_hash), role FROM users WHERE email=%s", (EMAIL,))
result = cur.fetchone()
print(f"Verified in DB: email={result[0]}, hash_length={result[1]}, role={result[2]}")

cur.close()
conn.close()
print("Admin password fixed successfully")
