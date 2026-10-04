#!/usr/bin/env sh
set -eu

ENDPOINT="${MINIO_ENDPOINT:-http://minio:9000}"
BUCKET="${MINIO_BUCKET:-mimicron-archives}"
USER="${MINIO_ROOT_USER:-mimicron}"
PASS="${MINIO_ROOT_PASSWORD:-mimicron_dev_minio}"

mc alias set local "$ENDPOINT" "$USER" "$PASS"
mc mb --ignore-existing "local/${BUCKET}"
echo "MinIO bucket ${BUCKET} ready."
