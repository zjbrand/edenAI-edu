#!/usr/bin/env bash
set -euo pipefail

# 例:
# BACKUP_DIR=/var/backups/edenai
# DATABASE_URL=postgresql://user:pass@127.0.0.1:5432/eden_teacher

: "${BACKUP_DIR:=/var/backups/edenai}"
: "${DATABASE_URL:?DATABASE_URL is required}"

mkdir -p "$BACKUP_DIR"

TS=$(date +%Y%m%d_%H%M%S)
OUT="$BACKUP_DIR/edenai_${TS}.sql.gz"

pg_dump "$DATABASE_URL" | gzip > "$OUT"

# 14日より古いバックアップを削除
find "$BACKUP_DIR" -type f -name 'edenai_*.sql.gz' -mtime +14 -delete

echo "backup created: $OUT"
