# Cursor master prompt

The canonical agent guide is **[AGENTS.md](AGENTS.md)** (same content as this file’s intent). Keep them aligned when editing milestone or architecture decisions.

**Cloud-neutral deployment (final):** Object storage is accessed only via the **S3-compatible API** with configurable `S3_*` environment variables. No provider-specific SDKs or managed AWS services in the default path. First deployment target: Docker Compose on a generic Linux VM; Terraform provider code lives under `infra/terraform/providers/`.
