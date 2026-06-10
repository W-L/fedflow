#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <backup-folder>"
  echo "Example: $0 backups/2026-05-08_14-30-00"
  exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
  echo "Backup folder does not exist: $BACKUP_DIR"
  exit 1
fi

for file in \
  "$BACKUP_DIR/local-learning-api-db.sql" \
  "$BACKUP_DIR/orch-api-db.sql" \
  "$BACKUP_DIR/keycloak-db.sql"; do
  if [ ! -f "$file" ]; then
    echo "Missing backup file: $file"
    exit 1
  fi
done

echo "Stopping services that use the databases"
docker compose stop local-learning-api orch-api keycloak instance-manager-frontend controller

echo "Starting database containers"
docker compose up -d local-learning-api-db orch-api-db keycloak-postgres

echo "Restoring local learning database"
docker compose exec -T local-learning-api-db \
  psql -U user -d local-learning-management \
  < "$BACKUP_DIR/local-learning-api-db.sql"

echo "Restoring orchestration database"
docker compose exec -T orch-api-db \
  psql -U user -d local-learning-management \
  < "$BACKUP_DIR/orch-api-db.sql"

echo "Restoring Keycloak database"
docker compose exec -T keycloak-postgres \
  psql -U keycloak -d keycloak \
  < "$BACKUP_DIR/keycloak-db.sql"

echo "Starting complete Client stack"
docker compose up -d

printf "Restore completed from: %s\n" "$BACKUP_DIR"

