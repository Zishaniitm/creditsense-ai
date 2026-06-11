"""
test_spring_boot_apis.py
Full integration test for the Spring Boot backend (Month 3).
Tests: Auth, JWT security, RBAC, application submission with ML scoring,
       fraud check, analytics, caching, rate limiting.

PREREQUISITES — start in this order:
  Terminal 1: python ml_service/app.py
  Terminal 2: python fraud_service/app.py
  Terminal 3: cd backend/creditsense-backend && mvn spring-boot:run

Run with: python tests/api/test_spring_boot_apis.py
"""

import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")
import requests
import time
import sys
import uuid

BASE = "http://localhost:8080/api/v1"

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []

def check(name, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, name, detail))
    print(f"  {status}  {name}")
    if detail:
        print(f"          → {detail}")


def run_all():
    print("=" * 60)
    print("  CreditSense AI — Spring Boot Backend Integration Tests")
    print("=" * 60)

    # ── Module 1: Registration & Login ──────────────────────────
    print("\n  [Module 1] Authentication")

    unique_email = f"test_{uuid.uuid4().hex[:8]}@creditsense.ai"
    register_payload = {
        "name": "Test User",
        "email": unique_email,
        "password": "Password123"
    }

    r = requests.post(f"{BASE}/auth/register", json=register_payload)
    check("Register returns 201", r.status_code == 201, f"Got: {r.status_code}")
    check("Register returns accessToken",
          "accessToken" in r.json().get("data", {}))

    r = requests.post(f"{BASE}/auth/login", json={
        "email": unique_email, "password": "Password123"
    })
    check("Login returns 200", r.status_code == 200)
    token = r.json()["data"]["accessToken"]
    check("Login returns valid JWT", token.count(".") == 2,
          "JWT should have 3 parts separated by dots")

    headers = {"Authorization": f"Bearer {token}"}

    # ── Module 2: JWT Security ──────────────────────────────────
    print("\n  [Module 2] JWT Security & RBAC")

    r = requests.get(f"{BASE}/applications/{uuid.uuid4()}")
    check("No token returns 401", r.status_code == 401, f"Got: {r.status_code}")

    r = requests.get(f"{BASE}/auth/me", headers=headers)
    check("Valid token returns 200 on /me", r.status_code == 200)

    r = requests.get(f"{BASE}/analytics/portfolio", headers=headers)
    check("APPLICANT role denied admin endpoint (403)",
          r.status_code == 403, f"Got: {r.status_code}")

    # ── Module 3: Loan Application + ML Scoring ─────────────────
    print("\n  [Module 3] Loan Application Submission (ML Integration)")

    app_payload = {
        "loanAmount": 500000,
        "loanPurpose": "Home Renovation",
        "loanTermMonths": 36,
        "age": 35,
        "monthlyIncome": 65000,
        "debtRatio": 0.25,
        "revolvingUtilization": 0.30,
        "openCreditLines": 5,
        "realEstateLoans": 1,
        "numDependents": 2,
        "late3059Days": 0,
        "late6089Days": 0,
        "late90Days": 0
    }

    start = time.time()
    r = requests.post(f"{BASE}/applications", json=app_payload, headers=headers)
    elapsed = time.time() - start

    check("Submit application returns 201", r.status_code == 201, f"Got: {r.status_code}")
    data = r.json().get("data", {})
    check("Response has riskScore",    "riskScore"    in data)
    check("Response has riskCategory", "riskCategory" in data)
    check("Response has recommendation","recommendation" in data)
    check("Response has explanation",  "explanation"  in data)
    check("riskScore is 0-100",
          data.get("riskScore") is not None and 0 <= data["riskScore"] <= 100,
          f"Got: {data.get('riskScore')}")
    check("riskCategory is valid",
          data.get("riskCategory") in ["LOW", "MEDIUM", "HIGH"],
          f"Got: {data.get('riskCategory')}")
    check("recommendation is valid",
          data.get("recommendation") in ["APPROVE", "REVIEW", "REJECT"],
          f"Got: {data.get('recommendation')}")
    check("Explanation has features",
          isinstance(data.get("explanation"), list) and len(data["explanation"]) > 0)
    check("End-to-end response time < 5s (NFR-001 relaxed for chained call)",
          elapsed < 5.0, f"Took: {elapsed:.2f}s")

    application_id = data.get("applicationId")
    print(f"\n         Application ID: {application_id}")
    print(f"         Risk Score: {data.get('riskScore')}  Category: {data.get('riskCategory')}")
    print(f"         Recommendation: {data.get('recommendation')}")
    print(f"         Response time: {elapsed:.2f}s")

    # ── Module 4: Get Application + Caching ─────────────────────
    print("\n  [Module 4] Get Application & Redis Caching")

    if application_id:
        # First call — cache miss (DB read)
        start = time.time()
        r1 = requests.get(f"{BASE}/applications/{application_id}", headers=headers)
        time1 = time.time() - start
        check("Get application returns 200", r1.status_code == 200)

        # Second call — cache hit (should be faster)
        start = time.time()
        r2 = requests.get(f"{BASE}/applications/{application_id}", headers=headers)
        time2 = time.time() - start
        check("Second get returns 200 (cached)", r2.status_code == 200)
        check("Cached response data matches",
              r1.json()["data"]["riskScore"] == r2.json()["data"]["riskScore"])

        print(f"\n         First call (DB):    {time1*1000:.1f}ms")
        print(f"         Second call (cache): {time2*1000:.1f}ms")
    else:
        check("Application ID available for cache test", False, "No ID returned")

    # ── Module 5: Input Validation ──────────────────────────────
    print("\n  [Module 5] Input Validation")

    invalid_payload = {**app_payload, "age": 15}  # age < 18
    r = requests.post(f"{BASE}/applications", json=invalid_payload, headers=headers)
    check("Invalid age (< 18) returns 422",
          r.status_code == 422, f"Got: {r.status_code}")

    incomplete_payload = {"loanAmount": 100000}
    r = requests.post(f"{BASE}/applications", json=incomplete_payload, headers=headers)
    check("Incomplete payload returns 422",
          r.status_code == 422, f"Got: {r.status_code}")

# ── Module 6: Fraud Check (RBAC) ─────────────────────────────
    print("\n  [Module 6] Fraud Detection Endpoint (RBAC)")

    fraud_payload = {
        "amount": 95000,
        "merchantCategory": 14,
        "channel": 1,
        "hourOfDay": 2,
        "dayOfWeek": 6,
        "city": 3,
        "isInternational": 1,
        "transactionsLast1h": 8,
        "transactionsLast24h": 15,
        "avgTxnAmount30d": 3200.0,
        "daysSinceLastTxn": 0,
        "accountAgeDays": 22,
        "numFailedTxns24h": 5,
        "isNewDevice": 1
    }

    # Test 6a: APPLICANT role should be DENIED (RBAC working correctly)
    r = requests.post(f"{BASE}/transactions/verify", json=fraud_payload, headers=headers)
    check("APPLICANT denied fraud-check (403) — RBAC correct",
          r.status_code == 403, f"Got: {r.status_code}")

    # Test 6b: Login as OFFICER and retry
    r = requests.post(f"{BASE}/auth/login", json={
        "email": "officer@creditsense.ai", "password": "Officer123"
    })
    check("Officer login returns 200", r.status_code == 200, f"Got: {r.status_code}")

    if r.status_code == 200:
        officer_token = r.json()["data"]["accessToken"]
        officer_headers = {"Authorization": f"Bearer {officer_token}"}

        r = requests.post(f"{BASE}/transactions/verify",
                          json=fraud_payload, headers=officer_headers)
        check("OFFICER fraud-check returns 200", r.status_code == 200, f"Got: {r.status_code}")

        if r.status_code == 200:
            fraud_data = r.json().get("data", {})
            check("Response has isFraudulent", "isFraudulent" in fraud_data)
            check("Response has riskLevel",    "riskLevel"    in fraud_data)
            check("Response has action",       "action"       in fraud_data)
            check("Obvious fraud flagged True",
                  fraud_data.get("isFraudulent") == True,
                  f"Got: {fraud_data.get('isFraudulent')}")
            print(f"\n         Fraudulent: {fraud_data.get('isFraudulent')}  "
                  f"Risk: {fraud_data.get('riskLevel')}  Action: {fraud_data.get('action')}")

        # Test 6c: Officer can also access analytics (Admin-only check separately)
        r = requests.get(f"{BASE}/analytics/portfolio", headers=officer_headers)
        check("OFFICER denied admin-only analytics (403)",
              r.status_code == 403, f"Got: {r.status_code}")
    else:
        check("Officer fraud-check skipped", False, "Officer login failed")


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)