COMPOSE ?= docker compose
ENV_FILE ?= .env

.PHONY: infra up down logs migrate contracts test lint e2e load \
	test-control-api test-sim-engine test-ingestion-gateway test-stream-processor test-stream-gateway

infra:
	$(COMPOSE) --env-file $(ENV_FILE) --profile infra up -d
	@echo "Waiting for init jobs (topics, bucket, migrations)..."
	$(COMPOSE) --env-file $(ENV_FILE) --profile infra up timescale-migrate redpanda-init object-store-init

up:
	$(COMPOSE) --env-file $(ENV_FILE) --profile all up -d --build

down:
	$(COMPOSE) --env-file $(ENV_FILE) --profile all down

logs:
	$(COMPOSE) --env-file $(ENV_FILE) logs -f

migrate:
	$(COMPOSE) --env-file $(ENV_FILE) run --rm timescale-migrate

contracts:
	cd scripts && npm install --silent && node validate-contracts.mjs

test: test-control-api test-sim-engine test-ingestion-gateway test-stream-processor test-stream-gateway

lint: contracts
	cd services/control-api && pip install -q -e ".[dev]" && ruff check app tests
	cd services/sim-engine && go vet ./...
	cd services/ingestion-gateway && go vet ./...
	cd services/stream-processor && cargo fmt --check && cargo clippy -- -D warnings
	cd services/stream-gateway && npm install --silent && npm run build

test-control-api:
	cd services/control-api && pip install -q -e ".[dev]" && pytest

test-sim-engine:
	cd services/sim-engine && go test ./...

test-ingestion-gateway:
	cd services/ingestion-gateway && go test ./...

test-stream-processor:
	cd services/stream-processor && cargo test

test-stream-gateway:
	cd services/stream-gateway && npm install --silent && npm test

seed:
	python scripts/demo.py $(API_URL)

demo: seed

e2e:
	pip install -q httpx
	python tests/e2e/smoke.py

load:
	@test -n "$(API_KEY)" || (echo "Set API_KEY=mc_live_..." && exit 1)
	k6 run tests/load/ingest_smoke.js

API_URL ?= http://localhost:8000
