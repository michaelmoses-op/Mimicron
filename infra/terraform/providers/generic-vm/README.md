# generic-vm (placeholder root)

Copy this directory when adding a real provider (e.g. `providers/hetzner/`).

Expected contents once M8 starts:

- `main.tf` — provider block, module calls for `network`, `vm`, optional `object-storage`
- `variables.tf` — region, instance size, SSH key, domain, `S3_*` passthrough for archives
- `outputs.tf` — public IP, SSH hint, Compose bootstrap status

No provider resources are defined yet; `main.tf` holds a comment-only stub so the layout is valid in reviews.
