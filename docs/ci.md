# CI/CD (M7)

## Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) | PR + `main` | Per-service lint/unit tests (Go `-race`, Rust clippy, etc.) |
| [`.github/workflows/contracts.yml`](../.github/workflows/contracts.yml) | PR + `main` | OpenAPI + JSON Schema validation |
| [`.github/workflows/integration.yml`](../.github/workflows/integration.yml) | PR + `main` | Docker Compose stack, e2e smoke, k6 ingest thresholds |
| [`.github/workflows/images.yml`](../.github/workflows/images.yml) | Push `main` | Build service images, Trivy scan, SBOM, push to GHCR |

Dependabot: [`.github/dependabot.yml`](../.github/dependabot.yml) (Actions, Go, Rust, npm, pip).

## Local parity

```bash
make contracts
make lint
make test
cp .env.example .env
make infra && make up
pip install httpx && python tests/e2e/smoke.py
# k6 (after creating an API key with ingest scope):
# API_KEY=mc_live_... k6 run tests/load/ingest_smoke.js
```

## Container registry (GHCR)

Images: `ghcr.io/<owner>/<repo>/<service>:<tag>`

Tags on `main`:

- `main` (rolling)
- `<git-sha>` (immutable)
- Semver tags `v*` when you push a Git tag (optional release flow)

Example: `ghcr.io/myuser/mimicron/control-api:main`

Pull (after making the package public or with a PAT):

```bash
docker pull ghcr.io/<owner>/<repo>/control-api:main
```

## Version / release strategy

- **App version:** CalVer or SemVer git tags `v0.1.0`, `v0.2.0` on `main` when you cut a portfolio release.
- **Images:** Tag pipeline listens for `v*` tags and publishes the same SHA as `v0.1.0` plus `latest` (optional).
- **Migrations:** Timescale + Alembic run via compose init / entrypoint; never skip in prod without a runbook entry.

## Branch protection (GitHub settings)

Recommended for `main`:

1. Require PR before merge (no direct pushes if you want audit trail).
2. Require status checks: `ci`, `contracts`, `integration` (and `images` only applies on merge to main).
3. Require branches up to date before merge.
4. Do not require signed commits unless you use them locally.

## Security scans

- **Trivy** scans built images in `images.yml`; fails on CRITICAL (configurable in workflow).
- **SBOM** SPDX JSON uploaded as workflow artifacts per image (Syft).

Cloud-neutral: registry is **GHCR only**; no ECR/AWS in the default path (see ADR 0007).
