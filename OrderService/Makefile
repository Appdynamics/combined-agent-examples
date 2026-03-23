# OrderService - Makefile for building, running, and ingesting
# Uses .env for variables (copy from .env.example and fill in values).

.PHONY: build up down logs ps health ingest ingest-continuous ingest-failures clean help

# Default target
help:
	@echo "OrderService targets:"
	@echo "  make build             - Build order-service Docker image"
	@echo "  make up                - Start otel-collector + order-service (docker compose up -d)"
	@echo "  make down              - Stop all services"
	@echo "  make logs              - Follow compose logs"
	@echo "  make ps                - List running compose services"
	@echo "  make health            - Check order-service health"
	@echo "  make ingest            - Run ingestion (COUNT=10, set COUNT= N for more)"
	@echo "  make ingest-continuous - Run ingestion for DURATION seconds (e.g. DURATION=300)"
	@echo "  make ingest-failures   - Run ingestion with failure scenarios"
	@echo "  make clean             - Stop services and remove built image"

# Repo root = directory where this Makefile lives (so paths work from any cwd)
ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

# Load .env from repo root if present
-include $(ROOT).env
export

# Service URL (override with make ingest URL=http://host:3000)
URL ?= http://localhost:3000
COUNT ?= 10
DURATION ?= 60
DELAY ?= 0.5

COMPOSE_FILE := $(ROOT)docker/docker-compose.yml

build:
	cd $(ROOT) && docker build -f docker/Dockerfile -t order-service:latest .

up: build
	cd $(ROOT) && docker compose -f docker/docker-compose.yml --project-directory $(ROOT) up -d

down:
	cd $(ROOT) && docker compose -f docker/docker-compose.yml --project-directory $(ROOT) down

logs:
	cd $(ROOT) && docker compose -f docker/docker-compose.yml --project-directory $(ROOT) logs -f

ps:
	cd $(ROOT) && docker compose -f docker/docker-compose.yml --project-directory $(ROOT) ps

health:
	@curl -s "$(URL)/health" | jq . 2>/dev/null || curl -s "$(URL)/health"

ingest:
	cd $(ROOT) && python3 ingest/ingest.py --url "$(URL)" --count "$(COUNT)" --delay "$(DELAY)"

ingest-continuous:
	cd $(ROOT) && python3 ingest/ingest.py --url "$(URL)" --duration "$(DURATION)" --delay "$(DELAY)"

ingest-failures:
	cd $(ROOT) && python3 ingest/ingest.py --url "$(URL)" --count "$(COUNT)" --failures --delay "$(DELAY)"

clean: down
	cd $(ROOT) && docker rmi order-service:latest 2>/dev/null || true
