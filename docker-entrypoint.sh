#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

# 1) Run migrations
log "Migrating database..."
alembic upgrade head

# 2) Create superuser if not exists
log "Creating superuser if not exists..."
python cli.py create_superuser \
    --name "Admin" \
    --email "${SUPERUSER_EMAIL:-admin@gmail.com}" \
    --phone "01700000000" \
    --password "${SUPERUSER_PASSWORD:-admin}" \
    --check_exist True

# 3) Finally, exec the passed CMD (e.g., uvicorn)
log "Starting application..."
exec "$@"
