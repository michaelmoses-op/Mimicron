#!/usr/bin/env sh
set -eu

ENDPOINT="${MINIO_ENDPOINT:-http://minio:9000}"
BUCKET="${MINIO_BUCKET:-mimicron-archives}"

aws --endpoint-url "$ENDPOINT" s3 mb "s3://${BUCKET}" 2>/dev/null || true
echo "S3 bucket ${BUCKET} ready at ${ENDPOINT}."
