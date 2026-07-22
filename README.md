
## 🛡️ ZauriScore## AI-Powered Smart Contract Risk Intelligence Platform
ZauriScore automates smart contract vulnerability detection, calculates deterministic risk scores, and delivers definitive GO / REVIEW / NO-GO deployment decisions with comprehensive, audit-ready reports.
------------------------------
## 🚀 Key Features

* Automated Scanning: Deep static analysis coupled with structural heuristic checks.
* Deterministic Risk Scoring: Hybrid evaluation engine combining Static Analysis, Custom Heuristics, and Machine Learning.
* Audit-Ready Reports: Instant, downloadable vulnerability reports available in JSON, Markdown, and PDF formats.
* Granular Security: Secure JWT authentication featuring strict Role-Based Access Control (RBAC).
* Tiered Monetization: Commercial-grade Stripe billing integration with hard plan enforcement.
* API Protection: Fixed rate-limiting windows scaled dynamically per user subscription tier.
* Continuous Monitoring: Interactive web dashboard tracking scan histories and real-time smart contract health metrics.
* Multi-Chain Readiness: Native compilation and analysis for Ethereum, Polygon, Arbitrum, and Base ecosystem standards. [1] 

------------------------------
## 🛠️ Tech Stack

| Layer | Technologies Used |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, TailwindCSS, TanStack Query |
| Backend API | Python 3.11+, FastAPI |
| Async Workers | Celery, Redis |
| Database | PostgreSQL |
| Storage | S3-Compatible Object Storage (AWS S3 / MinIO) |
| Static Analysis | Slither, Mythril, solc |
| Machine Learning | CodeBERT, PyTorch |
| Billing | Stripe API & Webhooks |
| Infrastructure | Docker, Docker Compose |

------------------------------
## 📁 Repository Structure

zauriscore/
├── apps/
│   ├── web/                 # Next.js 14 Frontend Application
│   └── api/                 # FastAPI Backend Application
├── workers/                 # Celery Tasks for heavy Slither/ML analysis
├── packages/                # Shared internal configurations (TS types, shared python libs)
├── docker/                  # Environment-specific Dockerfiles
├── .env.example             # Global environment variables template
├── docker-compose.yml       # Multi-container local orchestration
└── Makefile                 # Automation shortcuts for developers

------------------------------
## ⏱️ Quick Start## Prerequisites
Ensure you have the following software installed locally:

* Docker & Docker Compose (Desktop or Engine)
* Node.js v20.0.0+ & pnpm (or npm/yarn)
* Python v3.11+

------------------------------
## Step 1: Clone the Repository

git clone https://github.com/yourorg/zauriscore.git
cd zauriscore

------------------------------
## Step 2: Environment Configuration
Copy the master environment template and populate it with your local credentials:

cp .env.example .env

Open .env and configure your foundational keys:

# --- API CONFIGURATION ---
PROJECT_NAME="ZauriScore API"
SECRET_KEY="generate-a-secure-random-jwt-secret-key-here"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60

# --- DATABASES ---
POSTGRES_USER=zauri_admin
POSTGRES_PASSWORD=secure_db_password
POSTGRES_DB=zauriscore_dev
DATABASE_URL="postgresql://zauri_admin:secure_db_password@localhost:5432/zauriscore_dev"

# --- CACHE & WORKERS ---
REDIS_URL="redis://localhost:6379/0"

# --- THIRD PARTY INTEGRATIONS ---
STRIPE_API_KEY="sk_test_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
AWS_ACCESS_KEY_ID="your-s3-key"
AWS_SECRET_ACCESS_KEY="your-s3-secret"
AWS_STORAGE_BUCKET_NAME="zauriscore-reports"

------------------------------
## Step 3: Local Orchestration via Docker Compose
Spin up the entire architecture (Database, Redis Cache, FastAPI Backend, Celery Workers, and Next.js Frontend) in one command:

docker-compose up --build -d

Verify that all services are operational:

docker-compose ps

------------------------------
## Step 4: Verify the Installation

* Frontend Dashboard: Open http://localhost:3000 in your browser.
* Interactive API Documentation: Access the Swagger UI at http://localhost:8000/docs.
* API Health Check: Run a quick validation ping:

curl http://localhost:8000/api/v1/health


------------------------------
## 🧪 Running Tests
Execute isolated unit and integration test suites inside the runner containers:

# Run backend test suite (PyTest)
docker-compose exec api pytest
# Run frontend unit tests
docker-compose exec web pnpm test

------------------------------
## 📄 License
Distributed under the MIT License. See LICENSE for more information.
------------------------------
