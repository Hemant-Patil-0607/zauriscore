# ZauriScore Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                        Users                            │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTPS
                          ▼
┌─────────────────────────────────────────────────────────┐
│                     Nginx                               │
│              (Reverse Proxy / TLS)                      │
└──────────┬──────────────────────────┬───────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────┐      ┌──────────────────────────────┐
│  Next.js         │      │  FastAPI Backend              │
│  Frontend        │      │  (API Gateway)                │
│  :3000           │      │  :8000                        │
└──────────────────┘      └─────────────┬────────────────┘
                                        │
                          ┌─────────────▼────────────────┐
                          │  Redis Queue                  │
                          │  (Celery Broker)              │
                          └─────────────┬────────────────┘
                                        │
                          ┌─────────────▼────────────────┐
                          │  Celery Workers               │
                          │  (Analysis Pipeline)          │
                          │                               │
                          │  Stage 1: Source Retrieval    │
                          │  Stage 2: Compilation         │
                          │  Stage 3: Slither Analysis    │
                          │  Stage 4: Heuristics          │
                          │  Stage 5: ML Engine           │
                          │  Stage 6: Decision Engine     │
                          │  Stage 7: Report Generation   │
                          └──────┬──────────────┬─────────┘
                                 │              │
                    ┌────────────▼──┐    ┌──────▼──────────┐
                    │  PostgreSQL   │    │  S3 / MinIO      │
                    │  (Primary DB) │    │  (Report Files)  │
                    └───────────────┘    └─────────────────-┘
```

## Scan Pipeline Detail

```
┌──────────────────────────────────────────────────────────┐
│  scan.status = "queued"                                  │
│                                                          │
│  INPUT: contract_address + chain_id                      │
└────────────────────┬─────────────────────────────────────┘
                     │
          ┌──────────▼──────────┐
          │  Stage 1            │
          │  Source Retrieval   │
          │  Etherscan API      │
          │  → source_code      │
          │  → compiler_version │
          │  → source_hash      │
          └──────────┬──────────┘
                     │  abort if not verified
          ┌──────────▼──────────┐
          │  Stage 2            │
          │  Compilation        │
          │  solc + solc-select │
          │  → AST              │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │  Stage 3            │
          │  Slither Analysis   │
          │  → findings[]       │
          │  → static_score     │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │  Stage 4            │
          │  Heuristic Engine   │
          │  10 pattern checks  │
          │  → findings[]       │
          │  → heuristic_score  │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │  Stage 5            │
          │  ML Risk Engine     │
          │  CodeBERT embeddings│
          │  → ml_probability   │
          │  → ml_score         │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │  Stage 6            │
          │  Decision Engine    │
          │                     │
          │  risk = 0.5*static  │
          │      + 0.3*heur     │
          │      + 0.2*ml       │
          │                     │
          │  0-40  → GO         │
          │  40-70 → REVIEW     │
          │  70-100→ NO-GO      │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │  Stage 7            │
          │  Report Generator   │
          │  → report.json      │
          │  → report.md        │
          │  → report.pdf       │
          │  → stored in S3     │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │  scan.status =      │
          │  "completed"        │
          │  + all scores saved │
          └─────────────────────┘
```

## Risk Score Formula

```
risk_score = (0.5 × static_analysis_score)
           + (0.3 × heuristic_score)
           + (0.2 × ml_score)

Where each component score is 0–100.
```

## Database Schema

```
users ──────────────────── scans
  id                         id
  email                      user_id ──────────► users.id
  password_hash              contract_id ──────► contracts.id
  plan                       status
  created_at                 risk_score
                             decision
contracts                    confidence
  id                         static_score
  address ◄── scans          heuristic_score
  chain_id                   ml_score
  source_hash                report_json_url
  verified                   report_md_url
  compiler_version           report_pdf_url
  created_at                 created_at
                             completed_at
vulnerabilities
  id                       provenance
  scan_id ──► scans.id       id
  severity                   scan_id ──► scans.id
  detector                   contract_address
  description                chain_id
  location                   block_number
  source                     source_hash
                             solc_version
risk_scores                  slither_version
  id                         analysis_timestamp
  scan_id ──► scans.id
  total_score              billing_subscriptions
  static_analysis_score      id
  heuristic_score            user_id ──► users.id
  ml_score                   stripe_customer_id
  decision                   stripe_subscription_id
  confidence                 plan
  created_at                 status
                             current_period_end
```

## Security Model

```
THREAT: Malicious contract code execution
MITIGATION: Workers run in isolated containers with:
  - Read-only filesystem
  - Limited memory (512MB)
  - Network restricted
  - Timeout enforced (120s)
  - No root privileges

THREAT: API abuse / scan flooding
MITIGATION: Redis token bucket rate limiting
  - Free: 5 scans/day
  - Pro: 100 scans/day
  - Enterprise: Unlimited

THREAT: SQL Injection
MITIGATION: SQLAlchemy ORM with parameterized queries

THREAT: Unauthorized access
MITIGATION: JWT authentication on all protected routes
  - Tokens expire in 24 hours
  - Secrets via environment variables only
```

## Tech Stack Versions

| Component | Version |
|---|---|
| Python | 3.11 |
| FastAPI | 0.111 |
| SQLAlchemy | 2.0 |
| Celery | 5.4 |
| Next.js | 14 |
| TypeScript | 5.4 |
| PostgreSQL | 16 |
| Redis | 7 |
| CodeBERT | microsoft/codebert-base |
| Slither | 0.10 |
