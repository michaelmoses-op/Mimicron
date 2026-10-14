#!/usr/bin/env sh
set -eu

ENDPOINT="${S3_ENDPOINT:?S3_ENDPOINT required}"
BUCKET="${S3_BUCKET:?S3_BUCKET required}"
export AWS_ACCESS_KEY_ID="${S3_ACCESS_KEY:?S3_ACCESS_KEY required}"
export AWS_SECRET_ACCESS_KEY="${S3_SECRET_KEY:?S3_SECRET_KEY required}"

# s5cmd speaks the S3-compatible API (MinIO, R2, B2, Spaces, etc.).
s5cmd --endpoint-url "$ENDPOINT" mb "s3://${BUCKET}/" 2>/dev/null || true
echo "S3-compatible bucket ${BUCKET} ready at ${ENDPOINT}."
