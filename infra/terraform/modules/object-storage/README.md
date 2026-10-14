# object-storage module (placeholder)

Optional **S3-compatible** bucket for telemetry archives (Parquet replay). Consumers use the shared `S3_*` environment variables and path-style addressing by default.

This module is intentionally provider-neutral: it should output endpoint, bucket name, and credentials — not AWS-specific IAM role ARNs. Wire it from a provider root under `infra/terraform/providers/`.

Not used by local `docker compose` (the `object-store` service covers dev).
