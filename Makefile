COMPOSE ?= docker compose
ENV_FILE ?= .env

.PHONY: infra up down logs migrate contracts test lint \
	test-control-api test-sim-engine test-ingestion-gateway test-stream-processor test-stream-gateway

infra:
	$(COMPOSE) --env-file $(ENV_FILE) --profile infra up -d
	@echo "Waiting for init jobs (topics, bucket, migrations)..."
	$(COMPOSE) --env-file $(ENV_FILE) --profile infra up timescale-migrate redpanda-init minio-init

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
