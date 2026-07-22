# ZauriScore API Reference

Base URL: `https://api.zauriscore.com/api/v1`

All protected endpoints require: `Authorization: Bearer <token>`

---

## Authentication

### POST /auth/register

Register a new account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "mypassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user_id": "uuid",
  "email": "user@example.com",
  "plan": "free"
}
```

---

### POST /auth/login

Authenticate and get a token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "mypassword123"
}
```

**Response:** Same as register.

---

### GET /auth/me

Get current user profile.

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "plan": "free",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

## Scans

### POST /scan

Submit a contract for scanning.

**Request:**
```json
{
  "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
  "chain_id": 1
}
```

**Supported chain_ids:**
- `1` — Ethereum Mainnet
- `137` — Polygon
- `42161` — Arbitrum One
- `8453` — Base

**Response (202 Accepted):**
```json
{
  "id": "scan-uuid",
  "status": "queued",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Errors:**
- `429` — Rate limit exceeded
- `400` — Invalid address or unsupported chain

---

### GET /scan/{id}

Get scan status and results.

**Response:**
```json
{
  "id": "scan-uuid",
  "status": "completed",
  "risk_score": 63.4,
  "decision": "REVIEW",
  "confidence": 91.2,
  "static_score": 70.0,
  "heuristic_score": 55.0,
  "ml_score": 45.0,
  "vulnerabilities": [
    {
      "id": "vuln-uuid",
      "severity": "high",
      "detector": "reentrancy-eth",
      "description": "...",
      "location": "Contract.sol:45",
      "source": "slither"
    }
  ],
  "provenance": {
    "contract_address": "0x...",
    "chain_id": 1,
    "block_number": 19500000,
    "source_hash": "0xabc...",
    "solc_version": "0.8.19",
    "slither_version": "0.10.2",
    "analysis_timestamp": "2024-01-01T00:00:00Z"
  },
  "report_json_url": "https://...",
  "report_md_url": "https://...",
  "report_pdf_url": "https://...",
  "created_at": "2024-01-01T00:00:00Z",
  "completed_at": "2024-01-01T00:01:30Z"
}
```

**Status values:** `queued` | `running` | `completed` | `failed`

---

### GET /scan

List all scans for current user.

**Query params:**
- `limit` (default: 20, max: 100)
- `offset` (default: 0)

**Response:**
```json
[
  {
    "id": "scan-uuid",
    "address": "0x...",
    "chain_id": 1,
    "status": "completed",
    "risk_score": 63.4,
    "decision": "REVIEW",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

---

## Reports

### GET /report/{scan_id}

Get the full structured report for a completed scan.

**Response:**
```json
{
  "scan_id": "uuid",
  "contract_address": "0x...",
  "chain_id": 1,
  "risk_score": 63.4,
  "decision": "REVIEW",
  "confidence": 91.2,
  "static_score": 70.0,
  "heuristic_score": 55.0,
  "ml_score": 45.0,
  "vulnerabilities": [...],
  "solc_version": "0.8.19",
  "slither_version": "0.10.2",
  "source_hash": "0xabc...",
  "block_number": 19500000,
  "analysis_timestamp": "2024-01-01T00:00:00Z",
  "report_json_url": "https://...",
  "report_md_url": "https://...",
  "report_pdf_url": "https://...",
  "completed_at": "2024-01-01T00:01:30Z"
}
```

---

## Contracts

### GET /contract/{address}?chain_id=1

Get contract info and scan history.

**Response:**
```json
{
  "id": "uuid",
  "address": "0x...",
  "chain_id": 1,
  "name": "Tether USD",
  "verified": true,
  "compiler_version": "0.8.19",
  "source_hash": "0xabc...",
  "scan_count": 3,
  "latest_risk_score": 63.4,
  "latest_decision": "REVIEW",
  "scans": [...]
}
```

---

## Billing

### POST /billing/checkout

Create a Stripe checkout session.

**Request:**
```json
{ "plan": "pro" }
```

**Response:**
```json
{ "checkout_url": "https://checkout.stripe.com/..." }
```

---

### GET /billing/subscription

Get current subscription info.

**Response:**
```json
{
  "plan": "pro",
  "status": "active",
  "current_period_end": "2024-02-01T00:00:00Z"
}
```

---

### GET /billing/usage

Get today's scan usage.

**Response:**
```json
{
  "used": 3,
  "limit": 5,
  "unlimited": false
}
```

---

### POST /billing/webhook

Stripe webhook endpoint (not authenticated — uses Stripe signature).

---

## Health

### GET /health

```json
{ "status": "healthy", "service": "zauriscore-api" }
```

### GET /metrics

Prometheus metrics endpoint.

---

## Error Format

All errors follow this format:

```json
{
  "detail": "Human readable error message"
}
```

**HTTP Status Codes:**
- `200` — Success
- `201` — Created
- `202` — Accepted (async job started)
- `400` — Bad request / validation error
- `401` — Unauthorized
- `403` — Forbidden
- `404` — Not found
- `429` — Rate limit exceeded
- `500` — Server error
