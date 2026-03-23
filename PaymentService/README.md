# PaymentService - Java Test App

A simple Java (Spring Boot) Payment Service for testing and demonstrations. It supports **dual ingestion**: telemetry flows to **AppDynamics** (Java agent → controller) and to **Splunk Observability Cloud** (OpenTelemetry via the bundled collector → SignalFx ingest)—see [Dual ingestion](#dual-ingestion-appdynamics-and-splunk-observability-cloud).

## Features

- REST API with Spring Boot
- In-memory payment storage
- Health check and payment CRUD
- Capture (complete) payment with simulated delay
- Failure simulation modes: normal, timeout, exception, memory
- **Dual-backend observability:** AppDynamics + Splunk Observability Cloud (OTLP through `otel-collector`; see below)

## Dual ingestion: AppDynamics and Splunk Observability Cloud

This walkthrough runs one PaymentService instance and sends **the same application traffic** into both backends: **AppDynamics** receives BTs/metrics from the Java agent, and **Splunk Observability Cloud** receives OTLP from the Splunk OTel Java agent via the local collector (which authenticates with your org using `SPLUNK_ACCESS_TOKEN`).

| Destination | Path | What to look for |
|-------------|------|------------------|
| **AppDynamics** | JVM → AppDynamics Controller | Application `APPD_APP_NAME` (default `payment-space`), tier `PaymentService`, business transactions on `/payments`, `/health`, etc. |
| **Splunk Observability Cloud** | JVM → `otel-collector:4318` → `https://ingest.<realm>.signalfx.com` | APM / **Explore** traces for `service.name=PaymentService` (see `OTEL_RESOURCE_ATTRIBUTES` in `docker/docker-compose.yml`) |

**Steps**

1. **Environment** — Copy `.env.example` to `.env`. Set `SPLUNK_ACCESS_TOKEN` and `SPLUNK_REALM` (e.g. `us0`, `eu0`, `sg0`) so the **otel-collector** can export to Splunk. For AppDynamics, set `APPD_CONTROLLER_HOST`, `APPD_ACCOUNT_NAME`, and `APPD_ACCOUNT_ACCESS_KEY` (optional App name / tier / node overrides are in `.env.example`).
2. **Agents** — Place the AppDynamics `javaagent.jar` under `./agents/` (e.g. `./agents/javaagent.jar` or `./agents/ver*/javaagent.jar`). For dual mode, put the **Splunk OTel Java agent** (or compatible OpenTelemetry Java agent) JARs under **`./agents/otel/`** so the AppDynamics agent can attach it and emit OTLP. Details: [AppDynamics dual agent](#appdynamics-dual-agent).
3. **Start stack** — From the project root: `make build-up` (or `make up` if the image is already built). This starts `otel-collector` and `payment-service` with ports `4317`/`4318` (collector) and `8080` (API).
4. **Verify** — `curl -s http://localhost:8080/health` should return `200`. Check container logs: `make logs` or `docker compose -f docker/docker-compose.yml --env-file .env logs payment-service` for the AppD agent line and OTLP target (`http://otel-collector:4318`).
5. **Generate load (ingestion demo)** — Run traffic against the service (mapped to `localhost:8080`):

   ```bash
   pip install -r ingest/requirements.txt   # once
   make ingest
   # or, e.g. sustained demo with failures:
   make ingest INGEST_ARGS='--count 50 --failures --delay 0.3'
   ```

6. **Validate both UIs** — In **AppDynamics**, open the configured application and tier and confirm BTs and response times under load. In **Splunk Observability Cloud**, open **APM** (or **Explore** → traces) for your realm and confirm spans for `PaymentService` and downstream collector health (`docker compose ... logs otel-collector` should show no 401 / connection errors).

**AppDynamics only (no Splunk)** — You can set `APPD_*` and run with the AppD agent while leaving `SPLUNK_ACCESS_TOKEN` unset if you only want to validate the controller (the collector may error on export; you can stop the `otel-collector` service if unused). **Full dual ingestion** requires valid `APPD_*` + `javaagent.jar`, **`agents/otel/`** with the Splunk OTel agent, and **`SPLUNK_*`** on the collector. **Neither backend** — omitting `APPD_*` starts PaymentService **without** `-javaagent` in the default Docker entrypoint, so no JVM OTLP is produced; use dual mode or a custom launch if you need Splunk-only instrumentation.

## Requirements

- Java 17+
- Maven 3.6+

## Build

```bash
mvn -q clean package -DskipTests
```

## Run

```bash
# Default port 8080
mvn spring-boot:run

# Custom port (e.g. 8081)
PORT=8081 mvn spring-boot:run
```

Or run the JAR:

```bash
java -jar target/payment-service-1.0.0.jar
# Or with port:
PORT=8081 java -jar target/payment-service-1.0.0.jar
```

## AppDynamics dual agent

For the end-to-end **dual ingestion** demo (load script + both UIs), see [Dual ingestion](#dual-ingestion-appdynamics-and-splunk-observability-cloud) above.

PaymentService can run with the AppDynamics Java agent in **dual mode** (AppD Controller + Splunk OTel): one process sends to both AppD and OTLP (Splunk Observability Cloud via `otel-collector`).

### 1. Get the AppDynamics Java agent

- **Create the `agents` folder** in the project root if it does not exist. The agent (and optional OTel agent) will be placed under `agents/`.
- **Configure `controller-info.xml`** for your AppDynamics controller (host, port, account name, access key, etc.). This file is typically part of the agent distribution or placed in the agent directory; ensure it points to your controller before running.
- Download the **App Server Agent** (Java) from the AppDynamics portal and extract it so `javaagent.jar` is available.
- **Standalone:** place the agent at `./agents/javaagent.jar` or under `./agents/ver*/javaagent.jar` (or set `APPD_AGENT_JAR` when using Docker).
- **Docker Compose:** mount the agent at `./agents`; the entrypoint discovers `javaagent.jar` under `/app/agents` (override with `APPD_AGENT_JAR` in `.env` if needed).

Optional helper (if you have a direct download URL):

```bash
APPD_DOWNLOAD_URL=https://... ./scripts/download-agents.sh
```

### 2. Docker Compose with Makefile (recommended)

- Copy `.env.example` to `.env` and set your tokens (Splunk required for collector export; AppD optional).
- Ensure `./agents/javaagent.jar` or `./agents/ver*/javaagent.jar` exists inside the mounted `./agents` volume.

```bash
make        # list available targets (default)
make up     # start otel-collector + payment-service
```

To use the AppD dual agent, set `APPD_CONTROLLER_HOST`, `APPD_ACCOUNT_NAME`, and `APPD_ACCOUNT_ACCESS_KEY` in `.env`. For Splunk Observability, set `SPLUNK_ACCESS_TOKEN` and `SPLUNK_REALM` (default `sg0`) in `.env`.

**`.env` and `.env.example`:** Copy `.env.example` to `.env` and fill in `SPLUNK_ACCESS_TOKEN` (required for data to reach Splunk Observability Cloud via the collector). Optionally set `APPD_*` for AppDynamics. `.env` is gitignored; do not commit real tokens.

The entrypoint enables dual mode when `APPD_CONTROLLER_HOST` is set, account env vars are present, and `javaagent.jar` is found under `/app/agents`. OTLP is sent to `http://otel-collector:4318` when the Splunk OTel agent is present under `agents/otel/` (see troubleshooting below).

**Data in AppD but not in Splunk O11y (otel-collector):**

1. **Set token and realm for the collector**  
   `otel-collector` needs `SPLUNK_ACCESS_TOKEN` and `SPLUNK_REALM` (e.g. `us0`, `us1`, `eu0`, `sg0`). Set them in `.env` or pass them to `docker compose` so they are available to the **otel-collector** service (not only payment-service).

2. **Check otel-collector logs for errors**  
   ```bash
   docker compose logs otel-collector
   ```  
   Look for exporter errors (e.g. 401 Unauthorized, connection refused, or invalid ingest URL). The config uses `https://ingest.${SPLUNK_REALM}.signalfx.com` and header `X-SF-Token: ${SPLUNK_ACCESS_TOKEN}`; if either is empty or wrong, ingest will fail.

3. **Confirm realm**  
   Use the realm for your Splunk Observability Cloud org (e.g. from the ingest URL in the UI).

**PaymentService not sending data to otel-collector:**

OTLP data is sent to the collector only when the **OTel agent** (e.g. Splunk OTel Java agent) is loaded from **`agents/otel/`** by the AppDynamics Java agent. The JVM is given `-Dotel.exporter.otlp.endpoint=http://otel-collector:4318` and related options, but those are used by the OTel agent when it is attached.

- **Gap 1 – OTel agent not found:** If PaymentService logs show "Attaching agents: []" or "No OTel Agent found in .../otel", the AppD agent did not find the OTel JAR in `agents/otel/`. Put the Splunk OTel Java agent (or OpenTelemetry Java agent) JAR in **`agents/otel/`** so the dual agent can load it and send OTLP to the collector.
- **Gap 2 – AppD agent jar not found:** Ensure `./agents` is mounted and `./agents/javaagent.jar` or `./agents/ver*/javaagent.jar` exists, or set `APPD_AGENT_JAR` in `.env`.
- **Verify:** After starting, check PaymentService logs for: `[PaymentService] OTLP export target: http://otel-collector:4318 (data sent only if OTel agent in agents/otel is loaded by AppD)`. Then check collector logs: `docker compose logs otel-collector` to see if traces/metrics are received.

### 3. Without the agent

If the agent is not present or `APPD_CONTROLLER_HOST` is not set, the service starts as usual with no instrumentation.

## API Endpoints

Base URL: `http://localhost:8080` (or your `PORT`).

### Health

```bash
GET /health
```

**Example:** `curl http://localhost:8080/health`

### List payments

```bash
GET /payments
GET /payments?status=pending
GET /payments?customerId=customer-123
GET /payments?status=completed&customerId=customer-123
```

### Create payment

```bash
POST /payments
Content-Type: application/json

{
  "orderId": "order-123",
  "customerId": "customer-456",
  "amount": 99.99,
  "currency": "USD",
  "paymentMethod": "credit_card"
}
```

**Example:**

```bash
curl -X POST http://localhost:8080/payments \
  -H "Content-Type: application/json" \
  -d '{"orderId":"order-1","customerId":"cust-1","amount":59.99}'
```

### Get payment

```bash
GET /payments/:paymentId
```

### Capture payment (complete)

```bash
POST /payments/:paymentId/capture
Content-Type: application/json

{}
# or
{"paymentDetails": {"method": "credit_card"}}
```

Simulates processing delay (500–1500 ms). Marks payment as `completed`.

**Example:** `curl -X POST http://localhost:8080/payments/{paymentId}/capture -H "Content-Type: application/json" -d '{}'`

### Simulate failure

```bash
POST /payments/:paymentId/fail?type=<type>
Content-Type: application/json

{"reason": "Gateway unavailable"}
```

**Types:**

- `normal` (default) – mark payment as failed
- `timeout` – respond after 5 seconds with timeout error
- `exception` – throw an exception
- `memory` – return “Resource exhaustion” error (simulated)

**Examples:**

```bash
# Normal failure
curl -X POST http://localhost:8080/payments/{paymentId}/fail -H "Content-Type: application/json" -d '{"reason":"Declined"}'

# Timeout
curl -X POST "http://localhost:8080/payments/{paymentId}/fail?type=timeout"

# Exception
curl -X POST "http://localhost:8080/payments/{paymentId}/fail?type=exception"

# Memory (simulated)
curl -X POST "http://localhost:8080/payments/{paymentId}/fail?type=memory"
```

## Example test workflow

```bash
# 1. Health
curl http://localhost:8080/health

# 2. Create payment
PAYMENT_RESPONSE=$(curl -s -X POST http://localhost:8080/payments \
  -H "Content-Type: application/json" \
  -d '{"orderId":"order-1","customerId":"cust-1","amount":29.99}')

# Get paymentId (requires jq or similar)
PAYMENT_ID=$(echo $PAYMENT_RESPONSE | jq -r '.paymentId')

# 3. Get payment
curl http://localhost:8080/payments/$PAYMENT_ID

# 4. Capture
curl -X POST http://localhost:8080/payments/$PAYMENT_ID/capture -H "Content-Type: application/json" -d '{}'

# 5. Simulate failure on another payment
curl -X POST http://localhost:8080/payments/$PAYMENT_ID/fail -H "Content-Type: application/json" -d '{"reason":"Test"}'
```

## Data ingestion script

The script `ingest/ingest.py` generates HTTP traffic against PaymentService so you can **demonstrate dual ingestion** to AppDynamics and Splunk Observability Cloud (run it after `make up` as in [Dual ingestion](#dual-ingestion-appdynamics-and-splunk-observability-cloud)).

**Install:** `pip install -r ingest/requirements.txt`

**Usage (from project root):**

```bash
# Recommended: Makefile passes through to ingest/ingest.py (localhost:8080)
make ingest
make ingest INGEST_ARGS='--count 50 --failures --delay 0.3'

# Or invoke Python directly
python3 ingest/ingest.py --count 10

# Create 50 payments with failure scenarios
python3 ingest/ingest.py --count 50 --failures

# Continuous ingestion for 5 minutes
python3 ingest/ingest.py --duration 300

# Custom URL and delay (e.g. remote host)
python3 ingest/ingest.py --url http://localhost:8080 --count 20 --delay 1.0

# Quiet mode
python3 ingest/ingest.py --count 100 --quiet
```

**Options:** `--url`, `--count`, `--duration`, `--failures`, `--delay`, `--quiet`.

## Docker

```bash
# Build
docker build -t payment-service:latest .

# Run (port 8080)
docker run -d --name payment-service -p 8080:8080 payment-service:latest

# With custom port
docker run -d --name payment-service -p 8081:8081 -e PORT=8081 payment-service:latest
```

Health check is configured in the Dockerfile (`/health`).

### Docker Compose (otel-collector + payment-service)

Runs the Splunk OpenTelemetry Collector and PaymentService together. Set `SPLUNK_ACCESS_TOKEN` and optionally `SPLUNK_REALM` (default `sg0`) in the environment or a `.env` file.

```bash
# List all Make targets (default when you run make with no arguments)
make

# Build image and start both services
make build-up
# or
docker compose -f docker/docker-compose.yml --env-file .env up -d

# View logs
make logs
# or
make compose-logs

# Stop and remove containers
make down

# Clean: stop containers, remove the payment-service image, and mvn clean (target/)
make clean
```

## License

ISC
