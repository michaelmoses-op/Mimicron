# generic-vm (M8 bootstrap)

Reference Terraform root for a **single Linux VM** running Docker Compose. No cloud provider resources are wired yet — copy this folder to `providers/<your-provider>/` and add the provider block + module calls.

## Files

| File | Purpose |
|------|---------|
| `main.tf` | Outputs bootstrap notes + `cloud-init.sh` contents |
| `cloud-init.sh` | Install Docker; clone repo and run Compose manually |

## Usage

```bash
cd infra/terraform/providers/generic-vm
terraform init
terraform apply  # prints bootstrap_notes (no VM created until provider is added)
```

See [docs/deployment.md](../../../../docs/deployment.md) for Compose prod overlay and Caddy.
