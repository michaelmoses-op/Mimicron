#!/bin/sh
# Reference cloud-init for a single Ubuntu VM (install Docker, run Compose).
set -eu
apt-get update
apt-get install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sh
usermod -aG docker "$USER" 2>/dev/null || true
mkdir -p /opt/mimicron
echo "Clone Mimicron into /opt/mimicron, copy .env, then:"
echo "  docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile all up -d --build"
