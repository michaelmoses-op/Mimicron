terraform {
  required_version = ">= 1.5.0"
}

variable "domain" {
  type        = string
  description = "Public DNS name for Caddy (PUBLIC_DOMAIN)"
}

variable "ssh_public_key" {
  type        = string
  description = "SSH public key for the VM (provider-specific wiring goes here)"
}

output "bootstrap_notes" {
  value = <<-EOT
    1. Provision a Linux VM with ports 22, 80, 443 open.
    2. Run cloud-init from cloud-init.sh (or paste into provider user-data).
    3. Clone the repo to /opt/mimicron, set .env (secrets, PUBLIC_DOMAIN=${var.domain}).
    4. docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile all up -d --build
    EOT
}

output "cloud_init_script" {
  value       = file("${path.module}/cloud-init.sh")
  description = "User-data script contents for copy/paste"
}
