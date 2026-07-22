#!/bin/bash
set -e

# ============================================================
# ZauriScore Setup Script
# ============================================================

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

step() { echo -e "\n${YELLOW}▶ $1${NC}"; }
ok() { echo -e "${GREEN}✓ $1${NC}"; }
err() { echo -e "${RED}✗ $1${NC}"; exit 1; }

step "Checking prerequisites"
command -v docker &>/dev/null || err "Docker not found. Install from https://docker.com"
command -v docker-compose &>/dev/null || err "docker-compose not found"
ok "Prerequisites met"

step "Setting up environment"
if [ ! -f .env ]; then
  cp .env.example .env
  echo -e "${YELLOW}⚠  .env file created from template.${NC}"
  echo "   Please edit .env and add your API keys before continuing."
  echo "   Required: ETHERSCAN_API_KEY, STRIPE_SECRET_KEY, SECRET_KEY"
  echo ""
  echo "   Generate SECRET_KEY with: openssl rand -hex 32"
  echo ""
  read -p "Press Enter after configuring .env to continue..."
fi
ok "Environment configured"

step "Building Docker images"
docker-compose build --parallel
ok "Images built"

step "Starting infrastructure services"
docker-compose up -d postgres redis minio
echo "Waiting for services to be ready..."
sleep 8
ok "Infrastructure ready"

step "Running database migrations"
docker-compose run --rm backend alembic upgrade head
ok "Database migrations applied"

step "Creating S3 bucket"
docker-compose up -d minio
sleep 3
docker-compose run --rm backend python -c "
from app.services.report_generator import report_generator
report_generator._ensure_bucket()
print('Bucket ready')
" 2>/dev/null || echo "Bucket setup skipped (will be created on first report)"
ok "Storage ready"

step "Starting all services"
docker-compose up -d
ok "All services started"

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  ZauriScore is running! 🛡️${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "  Frontend:    http://localhost:3000"
echo "  API:         http://localhost:8000"
echo "  API Docs:    http://localhost:8000/docs"
echo "  MinIO:       http://localhost:9001"
echo ""
echo "  Logs:        docker-compose logs -f"
echo "  Stop:        docker-compose down"
echo ""
