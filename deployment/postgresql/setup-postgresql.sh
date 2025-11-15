#!/bin/bash

# PostgreSQL Docker Compose Setup Script for Ubuntu Server
# For SaaS Survey Platform

set -e

echo "========================================="
echo "PostgreSQL Setup for SaaS Survey Platform"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

echo -e "${GREEN}[1/8] Updating system packages...${NC}"
apt-get update -qq
apt-get upgrade -y -qq

echo -e "${GREEN}[2/8] Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
    echo -e "${GREEN}Docker installed successfully${NC}"
else
    echo -e "${YELLOW}Docker already installed${NC}"
fi

echo -e "${GREEN}[3/8] Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    apt-get install -y docker-compose-plugin
    echo -e "${GREEN}Docker Compose installed successfully${NC}"
else
    echo -e "${YELLOW}Docker Compose already installed${NC}"
fi

echo -e "${GREEN}[4/8] Creating SSL certificates...${NC}"
mkdir -p ssl
if [ ! -f ssl/server.crt ]; then
    openssl req -new -x509 -days 365 -nodes -text \
        -out ssl/server.crt \
        -keyout ssl/server.key \
        -subj "/CN=postgresql.local"
    chmod 600 ssl/server.key
    chmod 644 ssl/server.crt
    echo -e "${GREEN}SSL certificates created${NC}"
else
    echo -e "${YELLOW}SSL certificates already exist${NC}"
fi

echo -e "${GREEN}[5/8] Setting up environment variables...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env

    # Generate random password
    RANDOM_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

    # Replace password in .env
    sed -i "s/CHANGE_THIS_TO_STRONG_PASSWORD/$RANDOM_PASSWORD/g" .env

    echo -e "${GREEN}Environment file created with generated password${NC}"
    echo -e "${YELLOW}Password: $RANDOM_PASSWORD${NC}"
    echo -e "${YELLOW}IMPORTANT: Save this password! It's in .env file${NC}"
else
    echo -e "${YELLOW}.env file already exists${NC}"
fi

echo -e "${GREEN}[6/8] Creating data directory...${NC}"
mkdir -p postgres-data
chmod 755 postgres-data

echo -e "${GREEN}[7/8] Starting PostgreSQL container...${NC}"
docker compose down 2>/dev/null || true
docker compose up -d

echo -e "${GREEN}[8/8] Waiting for PostgreSQL to be ready...${NC}"
sleep 5

# Wait for PostgreSQL to be healthy
MAX_RETRIES=30
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if docker compose ps | grep -q "healthy"; then
        echo -e "${GREEN}PostgreSQL is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 2
    RETRY=$((RETRY+1))
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    echo -e "${RED}PostgreSQL failed to start properly${NC}"
    docker compose logs
    exit 1
fi

echo ""
echo "========================================="
echo -e "${GREEN}Setup completed successfully!${NC}"
echo "========================================="
echo ""
echo "Database Information:"
echo "  - Host: localhost (or your server IP)"
echo "  - Port: 5432"
echo "  - Database: saas_survey"
echo "  - User: survey_admin"
echo "  - Password: Check .env file"
echo ""
echo "Connection string:"
source .env
echo "  postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432/$POSTGRES_DB"
echo ""
echo "To view logs:"
echo "  docker compose logs -f"
echo ""
echo "To stop:"
echo "  docker compose down"
echo ""
echo "To restart:"
echo "  docker compose restart"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update your FastAPI project's .env file with DATABASE_URL"
echo "2. Change storage_type from 'sqlite' to 'postgresql' in config"
echo "3. Run database migrations if needed"
echo ""
