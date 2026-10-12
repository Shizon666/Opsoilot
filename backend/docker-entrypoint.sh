#!/bin/sh
# Wait for Postgres, apply pending *.up.sql once, then start the API server.
set -e

MIGRATIONS_DIR="${MIGRATIONS_DIR:-/migrations}"

if [ -z "$DATABASE_URL" ]; then
  echo "entrypoint: DATABASE_URL is required" >&2
  exit 1
fi

echo "entrypoint: waiting for postgres..."
i=0
until psql "$DATABASE_URL" -c "SELECT 1" >/dev/null 2>&1; do
  i=$((i + 1))
  if [ "$i" -ge 60 ]; then
    echo "entrypoint: postgres not ready after 60s" >&2
    exit 1
  fi
  sleep 1
done
echo "entrypoint: postgres is ready"

psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -c \
  "CREATE TABLE IF NOT EXISTS schema_migrations (
     filename   TEXT PRIMARY KEY,
     applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
   );"

if [ -d "$MIGRATIONS_DIR" ]; then
  for f in $(ls "$MIGRATIONS_DIR"/*.up.sql 2>/dev/null | sort); do
    name=$(basename "$f")
    applied=$(psql "$DATABASE_URL" -tAc "SELECT 1 FROM schema_migrations WHERE filename = '$name'")
    if [ "$applied" = "1" ]; then
      echo "entrypoint: skip $name (already applied)"
      continue
    fi
    echo "entrypoint: applying $name"
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -c \
      "INSERT INTO schema_migrations (filename) VALUES ('$name');"
  done
else
  echo "entrypoint: warning: migrations dir not found: $MIGRATIONS_DIR" >&2
fi

echo "entrypoint: starting server"
exec /app/server
