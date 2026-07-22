# ZauriScore Deployment Guide

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Local Development Setup](#2-local-development-setup)
3. [Environment Configuration](#3-environment-configuration)
4. [Docker Deployment](#4-docker-deployment)
5. [Database Management](#5-database-management)
6. [Production Deployment (AWS)](#6-production-deployment-aws)
7. [Monitoring Setup](#7-monitoring-setup)
8. [Stripe Integration](#8-stripe-integration)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

| Requirement | Version |
|---|---|
| Docker | 24+ |
| docker-compose | 2.20+ |
| Node.js | 20+ |
| Python | 3.11+ |
| Etherscan API key | Required |
| Stripe account | Required for billing |

---

## 2. Local Development Setup

```bash
# Clone repository
git clone https://github.com/yourorg/zauriscore
cd zauriscore

# Copy environment template
cp .env.example .env
```

Edit `.env` with your credentials (see Section 3).

```bash
# Run the setup script
bash scripts/setup.sh
```

The script will:
1. Verify Docker is running
2. Create `.env` from template (if not exists)
3. Build all Docker images
4. Start PostgreSQL and Redis
5. Run database migrations
6. Start all services

---

## 3. Environment Configuration

### Required Variables

| Variable | Description | Where to Get |
|---|---|---|
| `SECRET_KEY` | JWT signing key | `openssl rand -hex 32` |
| `ETHERSCAN_API_KEY` | Contract source fetching | https://etherscan.io/apis |
| `STRIPE_SECRET_KEY` | Payment processing | https://dashboard.stripe.com |
| `STRIPE_WEBHOOK_SECRET` | Webhook verification | Stripe dashboard |
| `DATABASE_URL` | PostgreSQL connection | Auto-configured in docker |
| `REDIS_URL` | Redis connection | Auto-configured in docker |

### Stripe Setup

1. Create a Stripe account at https://stripe.com
2. Create two products in Stripe Dashboard:
   - **ZauriScore Pro** — $49/month recurring
   - **ZauriScore Enterprise** — $299/month recurring
3. Copy Price IDs to `.env`:
   ```
   STRIPE_PRO_PRICE_ID=price_...
   STRIPE_ENTERPRISE_PRICE_ID=price_...
   ```
4. Set up webhook endpoint:
   - URL: `https://yourdomain.com/api/v1/billing/webhook`
   - Events: `checkout.session.completed`, `customer.subscription.deleted`
   - Copy webhook secret to `STRIPE_WEBHOOK_SECRET`

### Multi-Chain API Keys

| Chain | Explorer | API URL |
|---|---|---|
| Ethereum (1) | Etherscan | https://etherscan.io/apis |
| Polygon (137) | Polygonscan | https://polygonscan.com/apis |
| Arbitrum (42161) | Arbiscan | https://arbiscan.io/apis |
| Base (8453) | Basescan | https://basescan.org/apis |

---

## 4. Docker Deployment

### Start All Services

```bash
docker-compose up -d
```

### Check Status

```bash
docker-compose ps
docker-compose logs -f backend
docker-compose logs -f worker
```

### Scale Workers

```bash
# Run 4 concurrent workers
docker-compose up -d --scale worker=4
```

### Stop Everything

```bash
docker-compose down
```

### Full Reset (WARNING: destroys data)

```bash
docker-compose down -v
```

---

## 5. Database Management

### Run Migrations

```bash
docker-compose exec backend alembic upgrade head
```

### Create New Migration

```bash
docker-compose exec backend alembic revision --autogenerate -m "description"
```

### Rollback Migration

```bash
docker-compose exec backend alembic downgrade -1
```

### Database Backup

```bash
docker-compose exec postgres pg_dump -U zauriscore zauriscore > backup.sql
```

### Database Restore

```bash
cat backup.sql | docker-compose exec -T postgres psql -U zauriscore zauriscore
```

---

## 6. Production Deployment (AWS)

### Recommended Architecture

```
Route 53 (DNS)
    │
    ▼
Application Load Balancer
    │
    ├── ECS Fargate → Frontend containers
    ├── ECS Fargate → Backend API containers
    └── ECS Fargate → Worker containers (autoscaled by queue depth)
    
RDS PostgreSQL (Multi-AZ)
ElastiCache Redis
S3 Bucket (reports)
ECR (container registry)
```

### ECS Deployment Steps

1. **Push images to ECR:**
   ```bash
   aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URL
   docker tag zauriscore-backend:latest $ECR_URL/zauriscore-backend:latest
   docker push $ECR_URL/zauriscore-backend:latest
   ```

2. **Create ECS Task Definitions** for each service (backend, worker, frontend)

3. **Set environment variables** via AWS Secrets Manager or ECS task definition environment

4. **Configure ALB target groups** for frontend (3000) and backend (8000)

5. **Set up autoscaling** for workers based on Redis queue depth metric

### Worker Autoscaling Policy

Scale workers when:
- Queue depth > 10 items → add worker
- Queue depth < 2 items for 5 min → remove worker
- Min workers: 1
- Max workers: 20

---

## 7. Monitoring Setup

### Start Monitoring Stack

```bash
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

### Access Monitoring

| Service | URL | Credentials |
|---|---|---|
| Grafana | http://localhost:3001 | admin / zauriscore_grafana |
| Prometheus | http://localhost:9090 | No auth |

### Key Metrics to Watch

| Metric | Alert Threshold |
|---|---|
| Scan duration | > 90 seconds |
| API error rate | > 1% |
| Queue depth | > 50 items |
| Worker failures | > 3 in 5 minutes |
| API p95 latency | > 2 seconds |

---

## 8. Stripe Integration Testing

### Test Cards

| Card | Result |
|---|---|
| 4242 4242 4242 4242 | Success |
| 4000 0000 0000 9995 | Decline |
| 4000 0025 0000 3155 | 3D Secure required |

### Test Webhooks Locally

```bash
# Install Stripe CLI
stripe login
stripe listen --forward-to localhost:8000/api/v1/billing/webhook
```

---

## 9. Troubleshooting

### Backend won't start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# - Missing .env variables
# - Database not ready (wait 10s after postgres starts)
# - Port 8000 already in use
```

### Worker not processing scans

```bash
docker-compose logs worker
# Check Redis connection
docker-compose exec redis redis-cli ping
# Check queue depth
docker-compose exec redis redis-cli llen celery
```

### Contract scan fails immediately

- Verify `ETHERSCAN_API_KEY` is set and valid
- Confirm contract address is verified on the target explorer
- Check worker logs: `docker-compose logs worker`

### Database migration errors

```bash
# Reset and retry
docker-compose exec backend alembic downgrade base
docker-compose exec backend alembic upgrade head
```

### Reports not saving (S3 errors)

- Verify MinIO is running: `docker-compose ps minio`
- Check S3 credentials in `.env`
- Bucket is auto-created on first use — check logs for errors

---

## Performance Tuning

### Worker Concurrency

Edit `docker-compose.yml` worker command:
```yaml
command: celery -A app.workers.celery_app worker --concurrency=4 -Q scans
```

Default is 2 concurrent tasks per worker container.

### Database Connection Pool

In `backend/app/core/database.py`:
```python
engine = create_engine(
    settings.database_url,
    pool_size=20,       # Increase for high load
    max_overflow=40,
)
```

---

*ZauriScore — AI-Powered Smart Contract Risk Intelligence*
