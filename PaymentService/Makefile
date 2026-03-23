# PaymentService - Docker build and compose (primary way to run).
# Copy .env.example to .env and set SPLUNK_ACCESS_TOKEN (and optional APPD_*), then: make up
# Run from project root; compose file in docker/, config in config/, ingest script in ingest/.
IMAGE_NAME := payment-service
IMAGE_TAG  := latest
CONTAINER  := payment-service
PORT       := 8080
# Load .env from project root (compose file is in docker/, so default .env would be docker/.env)
COMPOSE    := docker compose -f docker/docker-compose.yml --env-file .env
DOCKERFILE := docker/Dockerfile

.PHONY: build run stop run-detached logs up down compose-logs ps build-up restart ingest help clean default

.DEFAULT_GOAL := help

# List available targets (default when you run make with no arguments)
help:
	@echo "PaymentService - available targets:"
	@echo ""
	@echo "  make              show this help"
	@echo "  make up           start otel-collector + payment-service (requires .env with SPLUNK_ACCESS_TOKEN)"
	@echo "  make down         stop and remove compose containers"
	@echo "  make build        build Docker image"
	@echo "  make build-up     build image then start compose"
	@echo "  make run          run container in foreground (port 8080)"
	@echo "  make run-detached run container in background"
	@echo "  make stop         stop and remove single container"
	@echo "  make logs         follow compose logs (after make up)"
	@echo "  make compose-logs same as logs"
	@echo "  make ps           list compose services"
	@echo "  make restart      down then up"
	@echo "  make ingest       generate traffic (INGEST_ARGS=... optional)"
	@echo "  make clean        stop containers, remove image, and mvn clean (target/)"
	@echo ""

# Build the Docker image (context = project root; Dockerfile in docker/)
build:
	docker build -f $(DOCKERFILE) -t $(IMAGE_NAME):$(IMAGE_TAG) .

# Run container (foreground, port 8080)
run:
	docker run --rm -p $(PORT):8080 --name $(CONTAINER) $(IMAGE_NAME):$(IMAGE_TAG)

# Run container detached (background)
run-detached:
	docker run -d -p $(PORT):8080 --name $(CONTAINER) $(IMAGE_NAME):$(IMAGE_TAG)

# Stop and remove the container
stop:
	docker stop $(CONTAINER) 2>/dev/null || true
	docker rm $(CONTAINER) 2>/dev/null || true

# Follow logs of both otel-collector and payment-service (use after make up)
logs:
	$(COMPOSE) logs -f

# --- Docker Compose (otel-collector + payment-service); reads .env ---

# Start otel-collector and payment-service (detached). Requires .env with SPLUNK_ACCESS_TOKEN.
up:
	$(COMPOSE) up -d

# Stop and remove compose containers and networks
down:
	$(COMPOSE) down

# Alias for logs (follow both services)
compose-logs: logs

# List compose services
ps:
	$(COMPOSE) ps

# Build image and start compose (build + up)
build-up: build up

# Restart: down then up
restart: down up

# --- Clean ---
# Stop compose, stop/remove single container, remove image, and Maven target/ (best-effort; errors ignored).
clean:
	-$(COMPOSE) down
	-$(MAKE) --no-print-directory stop
	-docker rmi $(IMAGE_NAME):$(IMAGE_TAG)
	-mvn -q clean

# --- Ingest (generate traffic to PaymentService; requires service on localhost:8080) ---
# Run: make ingest [INGEST_ARGS='--count 20 --failures']. Uses ingest/ingest.py.
ingest:
	python3 ingest/ingest.py $(INGEST_ARGS)
