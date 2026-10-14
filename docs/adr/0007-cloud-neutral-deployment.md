# ADR 0007: Cloud-neutral deployment

## Context

Mimicron is designed as a self-hosted platform (Compose on a generic Linux VM first). Docs and layout previously referred to an `s3` Terraform module and "MinIO / S3" in ways that implied AWS or a single vendor. Object storage is only needed for a later archive/replay path; the live pipeline uses Postgres, TimescaleDB, Redis, and Redpanda in containers.

## Decision

- **Deployment target:** Docker Compose on a provider-agnostic VM (Hetzner, DigitalOcean, Linode, GCP, Azure, on-prem, etc.). Kubernetes/GitOps remains a later stage.
- **Object storage:** Access only through the **S3-compatible HTTP API** with configurable `S3_ENDPOINT`, `S3_REGION`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, and `S3_FORCE_PATH_STYLE` (default path-style `true`). No provider SDK features that assume AWS (IAM roles, S3 Express, SSE-KMS-only flows).
- **Local dev:** S3-compatible server in compose (`object-store` service). When official MinIO images are unavailable, RustFS is used as a drop-in API stand-in.
- **Terraform:** Provider-specific code lives under `infra/terraform/providers/`; shared modules under `infra/terraform/modules/` (including `object-storage` naming, not `s3`).
- **CI/registry:** GitHub Actions and GHCR only; no AWS deployment or ECR in the default path.

## Consequences

- **Pros:** Portable across clouds and object-storage vendors; predictable cost; no surprise AWS bills; interview story stays "boring infrastructure."
- **Cons:** We operate Postgres, Timescale, Redis, Redpanda, and object storage ourselves instead of using managed RDS/MSK/ElastiCache/S3. More ops work at scale; acceptable for portfolio and single-VM first target.
- **Follow-up:** When archive/replay ships, implement clients with generic S3 signing (Rust: `object_store` or SDK with custom endpoint; Go: `minio-go` or `aws-sdk-go-v2` with custom resolver).
