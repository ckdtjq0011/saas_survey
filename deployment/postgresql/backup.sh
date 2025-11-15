#!/bin/bash

# PostgreSQL Backup Script
# Creates a backup of the database with timestamp

set -e

# Load environment variables
source .env

# Backup directory
BACKUP_DIR="./backups"
mkdir -p $BACKUP_DIR

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/saas_survey_backup_$TIMESTAMP.sql"

echo "Starting backup of $POSTGRES_DB database..."

# Create backup using docker exec
docker exec saas_survey_db pg_dump \
    -U $POSTGRES_USER \
    -d $POSTGRES_DB \
    -F c \
    -b \
    -v \
    -f /tmp/backup.dump

# Copy backup from container to host
docker cp saas_survey_db:/tmp/backup.dump $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

echo "Backup completed: ${BACKUP_FILE}.gz"

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.gz" -type f -mtime +7 -delete

echo "Old backups cleaned up (kept last 7 days)"

# Display backup size
ls -lh "${BACKUP_FILE}.gz"
