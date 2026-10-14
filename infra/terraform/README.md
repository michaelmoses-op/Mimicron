# Terraform (M8 skeleton)

Terraform targets a **single VM running Docker Compose**, on a provider you choose. Provider-specific resources live under `providers/`; reusable pieces under `modules/`.

## Layout

```
infra/terraform/
├── README.md                 # this file
├── modules/
│   ├── network/              # VPC/firewall patterns (provider-agnostic variables)
│   ├── vm/                   # compute + cloud-init to install Compose
│   └── object-storage/       # optional off-VM bucket (S3-compatible API), not AWS-only
└── providers/
    └── generic-vm/           # placeholder root — copy to add hetzner/, digitalocean/, etc.
```

## Adding a provider

1. Copy `providers/generic-vm/` to `providers/<name>/`.
2. Implement provider block and wire `modules/vm` + `modules/network` with that provider's resources.
3. Pass object-storage settings via `S3_*`-equivalent variables (endpoint, bucket, keys); do not hardcode AWS ARNs.

M8 is not fully implemented; this tree documents intent and keeps naming cloud-neutral.
