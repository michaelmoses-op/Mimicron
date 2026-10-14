# ADR 0008: CI/CD on GitHub Actions and GHCR

## Context

Mimicron needs portfolio-grade CI: fast PR checks, integration tests on real Compose dependencies, and published container images without tying deployment to a single cloud vendor.

## Decision

- **CI:** GitHub Actions with path-scoped unit jobs, contracts validation, Compose-based integration (e2e smoke + k6 thresholds).
- **Images:** Build on `main`, push to **GHCR** (`ghcr.io/<owner>/<repo>/<service>`). No AWS ECR in the default pipeline.
- **Supply chain:** Trivy image scan (fail on CRITICAL) and Syft SBOM artifacts on publish.
- **Go tests:** `-race` in CI for sim-engine and ingestion-gateway.

## Consequences

- **Pros:** Free tier friendly, matches cloud-neutral deployment story, reproducible images for VM Compose installs.
- **Cons:** Integration jobs are slower than unit-only CI; GHCR package visibility must be configured for public demos.
- **Follow-up:** Sign images (cosign), cache Rust/Go layers aggressively, add full heat-wave e2e when sim determinism test lands.
