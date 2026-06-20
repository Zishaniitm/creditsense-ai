<div align="center">

# 🛡️ CreditSense AI

### Intelligent Credit Risk Assessment & Financial Fraud Detection Platform

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Java](https://img.shields.io/badge/Java-17-ED8B00?style=flat&logo=openjdk&logoColor=white)](https://openjdk.org)
[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.2.5-6DB33F?style=flat&logo=springboot&logoColor=white)](https://spring.io/projects/spring-boot)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0.3-FF6600?style=flat)](https://xgboost.readthedocs.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![Tests](https://img.shields.io/badge/Tests-120%2F120%20passing-success?style=flat)](tests/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

*An end-to-end, production-style banking AI platform solving real credit risk and
fraud detection problems faced by Indian banks and NBFCs.*

[Features](#features) • [Architecture](#architecture) • [Quick Start](#quick-start) •
[API Docs](#api-documentation) • [ML Models](#ml-models) • [Testing](#testing)

</div>

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start — Docker](#quick-start--docker-recommended)
- [Quick Start — Local Development](#quick-start--local-development)
- [ML Models](#ml-models)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Known Limitations](#known-limitations)
- [Team](#team)

---

## 📌 Project Overview

CreditSense AI is a **production-style microservices platform** that replicates the
core intelligence layer of a real Indian NBFC (Non-Banking Financial Company) credit
operations team.

**The problem it solves:** Indian banks and NBFCs process thousands of loan
applications manually, with inconsistent decisions, no explainability, and slow
fraud detection. CreditSense AI automates and explains these decisions using
industry-standard machine learning.

**What makes it industry-relevant:**
- Trained on real credit bureau–style data (149,000+ applicant records)
- Follows RBI guidelines for explainable AI decisions (SHAP explanations)
- Banking-standard risk thresholds (not generic 0.5 ML cutoffs)
- Monotonic constraints to prevent model governance violations
- Full audit trail in PostgreSQL star schema

---

## ✨ Features

### Credit Risk Assessment
- **XGBoost credit scorer** — AUC-ROC 0.8481, calibrated with Platt Scaling
- **15 engineered features** including payment consistency, debt-to-income ratio,
  revolving utilization category
- **SHAP explainability** on every prediction — top-5 contributing factors with
  direction (increases/decreases risk)
- **Monotonic constraints** on payment_consistency_score — mathematically
  guarantees correct feature direction, RBI-compliant
- **Banking-grade thresholds:** LOW (<25%), MEDIUM (25-40%), HIGH (>40%) default
  probability — not generic 0.5 cutoffs

### Fraud Detection
- **Isolation Forest anomaly detector** — AUC-ROC 0.9954, Recall 96.7%
- Trained on 100,000 synthetic transactions (3% fraud rate)
- Real-time scoring with 14 behavioral transaction features
- Sub-100ms response time per transaction

### API Gateway (Spring Boot)
- **JWT authentication** with 15-minute token expiry (OWASP standard)
- **BCrypt password hashing** at cost factor 12
- **Role-Based Access Control** — APPLICANT / OFFICER / ADMIN roles
- **Redis caching** of credit assessments — 28x faster cache hits (440ms → 15ms)
- **Rate limiting** — 100 requests/minute per IP
- **Swagger/OpenAPI** documentation at `/swagger-ui.html`

### Frontend Dashboards
- **Applicant Portal** — Plain-language loan application form, real-time validation,
  instant AI assessment with SHAP visual explanation
- **Officer Dashboard** — Application review table, approve/reject workflow,
  SHAP factor breakdown per applicant
- **Admin Analytics** — Portfolio KPIs, Chart.js visualizations, system health
  monitoring, ML model performance panel

---

## 🏗️ System Architecture
┌─────────────────────────────────────────────────────────────────┐

│                        CLIENT LAYER                              │

│   Browser → Nginx (port 3000)                                   │

│   applicant/  officer/  admin/  (Bootstrap 5 + Chart.js)        │

└─────────────────────┬───────────────────────────────────────────┘

│ HTTP/REST

┌─────────────────────▼───────────────────────────────────────────┐

│                    API GATEWAY LAYER                             │

│   Java Spring Boot 3.2.5 (port 8080)                            │

│   JWT Auth │ RBAC │ Rate Limiting │ Redis Cache                  │

└──────┬──────────────┬──────────────────────────┬────────────────┘

│              │                          │

│ JPA/SQL      │ WebClient                │ WebClient

┌──────▼──────┐ ┌─────▼─────────────┐ ┌─────────▼──────────────┐

│  PostgreSQL │ │  ML Service       │ │  Fraud Service         │

│  port 5432  │ │  Python Flask     │ │  Python Flask          │

│  8 tables   │ │  port 5000        │ │  port 5001             │

│  star schema│ │  XGBoost v1.2.0   │ │  Isolation Forest      │

│             │ │  SHAP Explainer   │ │  v1.0.0                │

└─────────────┘ └───────────────────┘ └────────────────────────┘

│

┌──────▼──────┐

│    Redis    │

│  port 6379  │

│  TTL 30min  │

└─────────────┘
All services run in isolated Docker containers, orchestrated with Docker Compose.
Inter-service communication uses container DNS names (not localhost).

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **ML/Data** | Python 3.12, XGBoost, SHAP, Isolation Forest | Credit scoring, fraud detection, explainability |
| **Data Engineering** | Pandas, NumPy, SQLAlchemy, SMOTE | ETL pipeline, feature engineering, class balancing |
| **API Gateway** | Java 17, Spring Boot 3.2.5, Spring Security | JWT auth, RBAC, request routing |
| **Database** | PostgreSQL 15, Star Schema (8 tables) | Persistent storage, audit trail |
| **Cache** | Redis 7 | Credit score caching (30min TTL) |
| **Frontend** | HTML5, Bootstrap 5, Chart.js, Axios | 3 role-based dashboards |
| **Infrastructure** | Docker, Docker Compose, Nginx | Containerization, service orchestration |
| **ML Serving** | Flask 3.0, Gunicorn-ready | REST inference endpoints |
| **Security** | BCrypt (cost=12), JWT (HS384), CORS | Authentication, authorization |

---

## 📁 Project Structure
creditsense-ai/

│

├── data/                          # Raw and processed datasets

│   ├── raw/                       # Kaggle credit dataset (149K rows)

│   └── processed/                 # Cleaned, engineered features

│

├── pipeline/                      # Data engineering pipeline

│   └── scripts/

│       ├── loader.py              # PostgreSQL bulk loader

│       ├── cleaner.py             # Missing value handling

│       ├── feature_engineer.py    # 5 engineered features

│       └── etl_runner.py          # Full pipeline orchestrator

│

├── ml/                            # Machine learning

│   ├── training/

│   │   ├── train_credit_model.py  # LogReg → RF → XGBoost comparison

│   │   └── train_fraud_model.py   # Isolation Forest

│   ├── explainability/

│   │   └── shap_explainer.py      # SHAP TreeExplainer + waterfall plots

│   ├── models/                    # Trained model artifacts (.joblib)

│   └── evaluation/                # ROC curves, SHAP plots, metadata JSON

│

├── ml_service/                    # Flask credit scoring API (port 5000)

│   ├── app.py                     # /predict /explain /health endpoints

│   ├── Dockerfile

│   └── requirements.txt

│

├── fraud_service/                 # Flask fraud detection API (port 5001)

│   ├── app.py                     # /fraud-check /health endpoints

│   ├── Dockerfile

│   └── requirements.txt

│

├── backend/                       # Spring Boot API gateway (port 8080)

│   └── creditsense-backend/

│       └── src/main/java/com/creditsense/

│           ├── controller/        # REST endpoints

│           ├── service/           # Business logic

│           ├── entity/            # JPA entities

│           ├── repository/        # Spring Data repositories

│           ├── security/          # JWT filter, UserDetailsService

│           └── config/            # Security, CORS, Redis, Swagger

│

├── frontend/                      # Static frontend (served by Nginx)

│   ├── auth/index.html            # Login / Register

│   ├── applicant/index.html       # Loan application form

│   ├── officer/index.html         # Officer review dashboard

│   ├── admin/index.html           # Admin analytics dashboard

│   ├── assets/js/

│   │   ├── auth.js                # JWT management, role routing

│   │   └── api.js                 # Axios wrapper, 401 interceptor

│   └── Dockerfile

│

├── infra/

│   ├── postgres/schema.sql        # 8-table star schema DDL

│   └── docker/postgres-init/      # Auto-init SQL for Docker Postgres

│

├── tests/

│   ├── pipeline/test_pipeline.py  # 41 data pipeline tests

│   ├── ml/test_models.py          # 17 ML model validation tests

│   └── api/

│       ├── test_flask_apis.py     # 35 Flask API endpoint tests

│       └── test_spring_boot_apis.py # 27 Spring Boot integration tests

│

├── docs/

│   └── known_issues.md            # Technical debt and resolved bugs

│

├── docker-compose.yml             # Full stack orchestration

├── .dockerignore

└── README.md

---

## 🚀 Quick Start — Docker (Recommended)

The entire stack starts with one command. No Python/Java/Node installation required
beyond Docker Desktop.

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac/Linux)
- 4GB RAM minimum allocated to Docker

### 1. Clone the repository
```bash
git clone https://github.com/ZISHANiITm/creditsense-ai.git
cd creditsense-ai
```

### 2. Start all services
```bash
docker compose up -d
```

This starts 6 containers: PostgreSQL, Redis, ML Service, Fraud Service,
Spring Boot backend, and Nginx frontend. First run downloads base images
(~2GB); subsequent runs start in under 30 seconds.

### 3. Verify all services are healthy
```bash
docker compose ps
curl http://localhost:5000/health    # ML Service
curl http://localhost:5001/health    # Fraud Service
curl http://localhost:8080/actuator/health  # Spring Boot
```

### 4. Seed the database (first time only)
```bash
# Load the included seed data (149K+ records)
PGPASSWORD=creditsense2024 psql \
  -h localhost -p 5433 \
  -U creditsense_user \
  -d creditsense_db \
  -f infra/docker/postgres-init/01-schema.sql
```

### 5. Open the application
http://localhost:3000


### Default login credentials

| Role | Email | Password |
|---|---|---|
| Admin | admin@creditsense.ai | Admin@123 |
| Loan Officer | officer@creditsense.ai | Officer123 |
| Applicant | Register a new account | — |

---

## 💻 Quick Start — Local Development

### Prerequisites
- Python 3.12 + pip
- Java 17 + Maven 3.9
- PostgreSQL 15
- Redis 7

### 1. Python environment
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r ml_service/requirements.txt
pip install -r fraud_service/requirements.txt
```

### 2. Database setup
```bash
psql -U postgres -f infra/postgres/schema.sql
```

### 3. Run data pipeline
```bash
python pipeline/scripts/etl_runner.py
```

### 4. Train ML models
```bash
python ml/training/train_credit_model.py
python ml/training/train_fraud_model.py
python ml/explainability/shap_explainer.py
```

### 5. Start all services (4 separate terminals)
```bash
# Terminal 1
python ml_service/app.py

# Terminal 2
python fraud_service/app.py

# Terminal 3
cd backend/creditsense-backend && mvn spring-boot:run

# Terminal 4
python -m http.server 3000
```

---

## 🤖 ML Models

### Credit Risk Model — XGBoost v1.2.0

| Metric | Value | Notes |
|---|---|---|
| AUC-ROC | 0.8481 | Held-out test set |
| Recall @ 0.25 threshold | 44.5% | LOW/MEDIUM boundary |
| Recall @ 0.40 threshold | 28.1% | HIGH RISK cutoff |
| Precision @ 0.40 | 46.8% | |
| Training samples | 83,635 (after SMOTE) | |
| Features | 15 | 10 raw + 5 engineered |

**Key design decisions:**
- **Platt Scaling calibration** — raw XGBoost probabilities were severely biased
  (safe applicants scoring 87% default probability). Calibration fixed this.
- **Monotonic constraint** on `payment_consistency_score` (constraint=-1) —
  eliminates non-monotonic SHAP directions that would fail regulator scrutiny.
  Mathematically guarantees higher payment consistency → lower predicted risk.
- **Banking-grade thresholds** — industry standard 0.25/0.40 boundaries, not
  generic 0.5 ML default.

### Fraud Detection Model — Isolation Forest v1.0.0

| Metric | Value |
|---|---|
| AUC-ROC | 0.9954 |
| Fraud Recall | 96.7% (580/600 caught) |
| Contamination | 3% |
| Training samples | 100,000 transactions |

---

## 📡 API Documentation

Interactive Swagger UI available at:
http://localhost:8080/swagger-ui.html

### Core Endpoints

#### Authentication
```http
POST /api/v1/auth/register    # Create new applicant account
POST /api/v1/auth/login       # Login, receive JWT
GET  /api/v1/auth/me          # Current user info
```

#### Loan Applications
```http
POST  /api/v1/applications           # Submit application → triggers ML scoring
GET   /api/v1/applications/{id}      # Get application with SHAP explanation
PATCH /api/v1/applications/{id}/decision  # Officer approves/rejects
```

#### Fraud Detection
```http
POST /api/v1/transactions/verify     # Real-time fraud check (OFFICER/ADMIN)
```

#### Analytics
```http
GET /api/v1/analytics/portfolio      # Portfolio KPIs (ADMIN only)
```

### Sample: Submit Loan Application
```bash
curl -X POST http://localhost:8080/api/v1/applications \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -d '{
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
  }'
```

### Sample Response
```json
{
  "success": true,
  "message": "Application submitted and scored",
  "data": {
    "applicationId": "3c98adc1-f0a0-4dbc-886a-c6ad578b593d",
    "riskScore": 71.4,
    "riskCategory": "LOW",
    "defaultProbability": 0.2856,
    "recommendation": "APPROVE",
    "status": "APPROVED",
    "explanation": [
      {
        "feature": "payment_consistency_score",
        "display_name": "Payment Consistency Score",
        "shap_value": -0.7801,
        "direction": "decreases_risk",
        "value": 100.0
      }
    ]
  }
}
```

---

## 🧪 Testing

120 tests across 4 suites, all passing.

```bash
# Run all test suites
python tests/pipeline/test_pipeline.py   # 41 tests — data pipeline
python tests/ml/test_models.py           # 17 tests — ML model validation
python tests/api/test_flask_apis.py      # 35 tests — Flask API endpoints
python tests/api/test_spring_boot_apis.py # 27 tests — Spring Boot integration
```

| Suite | Tests | Covers |
|---|---|---|
| Pipeline | 41/41 | Data loading, cleaning, feature engineering, DB insertion |
| ML Models | 17/17 | Model loading, prediction, SHAP values, fraud detection, metadata |
| Flask APIs | 35/35 | Health checks, credit scoring, SHAP explanation, fraud detection |
| Spring Boot | 27/27 | Auth, JWT, RBAC, loan submission, ML integration, Redis caching, fraud check |

---

## ⚠️ Known Limitations

See [`docs/known_issues.md`](docs/known_issues.md) for the full list. Key
acknowledged gaps for a production deployment:

- **Synthetic training data** — model trained on Kaggle dataset + synthetic fraud
  transactions. Real NBFC data would improve AUC by an estimated 3-5%.
- **No HTTPS** — TLS termination not configured (would use AWS ACM or Let's Encrypt
  in production).
- **Single-instance Redis** — no cluster mode; sufficient for this scale,
  would need clustering at 10K+ concurrent users.
- **No VAPT** — Vulnerability Assessment and Penetration Testing not conducted.
- **Kafka not implemented** — SRS specified async transaction streaming via Kafka;
  current implementation uses synchronous Flask calls. Functionally equivalent at
  this scale; Kafka would be required at >1000 TPS.

---

## 👥 Team

Built as a final-year BCA project demonstrating industry-level engineering
and machine learning skills.

| Member | Role |
|---|---|
| **Zishan** | ML Engineering, Data Pipeline, Backend, DevOps |
| **[Collaborator]** | Frontend, Testing, Documentation |

**Academic context:** BCA Final Year Project + IIT Madras Data Science Programme

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with the goal of solving real problems in Indian banking and fintech.**

⭐ If this project helped you, consider giving it a star.

</div>

