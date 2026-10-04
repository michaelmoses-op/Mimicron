#!/usr/bin/env sh
set -eu

: "${TIMESCALE_HOST:=timescale}"
: "${TIMESCALE_PORT:=5432}"
: "${TIMESCALE_USER:=mimicron}"
: "${TIMESCALE_PASSWORD:=mimicron_dev}"
: "${TIMESCALE_DB:=mimicron_ts}"

export PGPASSWORD="$TIMESCALE_PASSWORD"
PSQL="psql -h $TIMESCALE_HOST -p $TIMESCALE_PORT -U $TIMESCALE_USER -d $TIMESCALE_DB -v ON_ERROR_STOP=1"

$PSQL -c "
CREATE TABLE IF NOT EXISTS schema_migrations (
  version text PRIMARY KEY,
  applied_at timestamptz NOT NULL DEFAULT now()
);
"

MIGRATIONS_DIR="${MIGRATIONS_DIR:-/migrations}"
for f in $(ls "$MIGRATIONS_DIR"/*.sql 2>/dev/null | sort); do
  version=$(basename "$f")
  applied=$($PSQL -tAc "SELECT 1 FROM schema_migrations WHERE version = '$version'" || true)
  if [ "$applied" = "1" ]; then
    echo "skip $version"
    continue
  fi
  echo "apply $version"
  $PSQL -f "$f"
  $PSQL -c "INSERT INTO schema_migrations (version) VALUES ('$version');"
done

echo "Timescale migrations complete."
