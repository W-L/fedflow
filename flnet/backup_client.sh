#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="backups/$(date +%Y-%m-%d_%H-%M-%S)"
mkdir -p "$BACKUP_DIR"

echo "Creating backup in $BACKUP_DIR"

docker compose exec -T local-learning-api-db \
  pg_dump -U user -d local-learning-management \
  > "$BACKUP_DIR/local-learning-api-db.sql"

docker compose exec -T orch-api-db \
  pg_dump -U user -d local-learning-management \
  > "$BACKUP_DIR/orch-api-db.sql"

docker compose exec -T keycloak-postgres \
  pg_dump -U keycloak -d keycloak \
  > "$BACKUP_DIR/keycloak-db.sql"

printf "Backup completed: %s\n" "$BACKUP_DIR"

tar -czf backup.tar.gz backups/ nginx.conf env/ .env
