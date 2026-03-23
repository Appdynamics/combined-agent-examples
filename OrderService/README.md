# OrderService

Demo app for **Node.js** dual ingestion to **AppDynamics** and **Splunk Observability Cloud**. Sample Order Service instrumented with Splunk Observability (OTLP traces, metrics, profiling) and optional AppDynamics (dual mode).

## Features

- RESTful API with Express.js
- In-memory order storage
- Multiple failure simulation modes
- **Splunk OTel**: tracing, metrics (runtime + HTTP + custom), snapshot & always-on profiling
- Optional AppDynamics (dual mode when `APPD_CONTROLLER_HOST` is set)

## Running the Service

The app runs only via **Docker Compose** and the **Makefile** (otel-collector + order-service). The image is built on `make up`; you do not run `npm install` or `npm start` on the host.

### Quick start

```bash
cp .env.example .env   # set SPLUNK_ACCESS_TOKEN (required) and optional AppD credentials
make up                 # build image and start services
make health             # check order-service health
make ingest             # generate traffic (optional: COUNT=20 make ingest)
make logs               # follow logs
make down               # stop services
```

The API is exposed at `http://localhost:3000` by default (`PORT` in compose).

### Makefile targets

| Target | Description |
|--------|-------------|
| `make up` | Build image and start otel-collector + order-service |
| `make down` | Stop services |
| `make logs` | Follow compose logs |
| `make ps` | List running services |
| `make health` | Hit `http://localhost:3000/health` |
| `make ingest` | Run ingestion (use `COUNT=20` etc. to override) |
| `make ingest-continuous` | Run ingestion for `DURATION` seconds |
| `make ingest-failures` | Ingestion with failure scenarios |
| `make clean` | Stop and remove order-service image |

### Compose environment blocks (order-service)

Settings in `docker/docker-compose.yml` are grouped so you can enable/disable by section:

- **App** – `NODE_ENV`, `PORT`
- **AppDynamics** – enable by setting `APPD_CONTROLLER_HOST` and account vars in `.env`
- **Splunk OTel: tracing & identity** – `SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_LOG_LEVEL`
- **Splunk OTel: resource attributes** – tags for traces/metrics
- **Splunk OTel: snapshot profiling** – call-graph; disable with `SPLUNK_SNAPSHOT_PROFILER_ENABLED=false`
- **Splunk OTel: always-on profiling** – CPU + memory; enable with `SPLUNK_PROFILER_ENABLED=true`, `SPLUNK_PROFILER_MEMORY_ENABLED=true`
- **Splunk OTel: metrics** – disable with `SPLUNK_METRICS_ENABLED=false`

Override any of these in `.env` (see `.env.example`).

### Key environment variables (.env)

- **Splunk (required for compose):** `SPLUNK_ACCESS_TOKEN`, `SPLUNK_REALM`
- **Host identity:** `HOST_NAME` (for collector hostmetrics)
- **AppDynamics (optional):** `APPD_CONTROLLER_HOST`, `APPD_ACCOUNT_NAME`, `APPD_ACCOUNT_ACCESS_KEY`, `APPD_APP_NAME`, etc.; set `agent_deployment_mode=dual` for dual mode
- **Profiling:** `SPLUNK_SNAPSHOT_PROFILER_ENABLED`, `SPLUNK_PROFILER_ENABLED`, `SPLUNK_PROFILER_MEMORY_ENABLED`, `SPLUNK_CPU_PROFILER_COLLECTION_INTERVAL`, etc.

### Container health

The order-service container defines a health check on `/health`. Use `make health` or `docker compose ps` to verify.

## API Endpoints

### Health Check
```bash
GET /health
```

Returns service health status.

**Example:**
```bash
curl http://localhost:3000/health
```

### Get All Orders
```bash
GET /orders
```

Returns a list of all orders with optional filtering.

**Query Parameters:**
- `status` (optional) - Filter by order status (pending, paid, failed)
- `customerId` (optional) - Filter by customer ID

**Example:**
```bash
# Get all orders
curl http://localhost:3000/orders

# Get orders by status
curl http://localhost:3000/orders?status=paid

# Get orders by customer
curl http://localhost:3000/orders?customerId=customer-123

# Combined filters
curl http://localhost:3000/orders?status=pending&customerId=customer-123
```

### Create Order
```bash
POST /orders
Content-Type: application/json

{
  "customerId": "customer-123",
  "items": [
    {
      "productId": "prod-1",
      "name": "Product 1",
      "price": 29.99,
      "quantity": 2
    }
  ],
  "totalAmount": 59.98
}
```

**Example:**
```bash
curl -X POST http://localhost:3000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "customer-123",
    "items": [
      {"productId": "prod-1", "name": "Laptop", "price": 999.99, "quantity": 1},
      {"productId": "prod-2", "name": "Mouse", "price": 29.99, "quantity": 2}
    ]
  }'
```

### Get Order
```bash
GET /orders/:orderId
```

**Example:**
```bash
curl http://localhost:3000/orders/{orderId}
```

### Pay for Order
```bash
POST /orders/:orderId/pay
Content-Type: application/json

{
  "paymentMethod": "credit_card",
  "paymentDetails": {
    "last4": "4242"
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:3000/orders/{orderId}/pay \
  -H "Content-Type: application/json" \
  -d '{"paymentMethod": "credit_card"}'
```

### Simulate Order Failure
```bash
POST /orders/:orderId/fail?type=<failure-type>
Content-Type: application/json

{
  "reason": "Payment gateway unavailable"
}
```

**Failure Types:**
- `normal` (default) - Mark order as failed
- `timeout` - Simulate 5-second timeout
- `exception` - Throw an exception
- `memory` - Simulate memory-intensive operation

**Examples:**
```bash
# Normal failure
curl -X POST http://localhost:3000/orders/{orderId}/fail

# Timeout failure
curl -X POST "http://localhost:3000/orders/{orderId}/fail?type=timeout"

# Exception failure
curl -X POST "http://localhost:3000/orders/{orderId}/fail?type=exception"

# Memory failure
curl -X POST "http://localhost:3000/orders/{orderId}/fail?type=memory"
```

## AppDynamics (Optional)

AppDynamics runs in **dual mode** with Splunk OTel when `APPD_CONTROLLER_HOST` is set. If unset, the service runs with Splunk OTel only.

### Configuration

1. Copy `.env.example` to `.env` and set Splunk + optional AppDynamics variables:
```bash
cp .env.example .env
```

2. **Enable AppDynamics** by setting in `.env`:
```bash
APPD_CONTROLLER_HOST=your-controller.saas.appdynamics.com
APPD_ACCOUNT_NAME=your-account-name
APPD_ACCOUNT_ACCESS_KEY=your-access-key
APPD_APP_NAME=order-space
APPD_TIER_NAME=OrderService
APPD_NODE_NAME=OrderNode
agent_deployment_mode=dual
```

3. **Splunk-only**: Leave `APPD_CONTROLLER_HOST` empty (or omit it) in `.env`. The app uses `@splunk/otel` only.

### How It Works

- When `agent_deployment_mode=dual` and `APPD_CONTROLLER_HOST` is set, the AppDynamics agent loads first and starts Splunk OTel internally.
- Otherwise, Splunk OTel is started directly in `src/server.js`.
- All configuration is via environment variables and `.env` consumed by Compose.

## Testing Scenarios

Use these flows to generate traces, metrics, and (with profiling enabled) profiles:

1. **Normal flow**: Create order → Get order → Pay for order
2. **Errors**: Use `/fail` endpoint to generate errors
3. **Slow transactions**: Payment endpoint has random delay (500–1500 ms)
4. **Timeouts**: `?type=timeout` (5 s)
5. **Exceptions**: `?type=exception`
6. **Memory**: `?type=memory` (resource-heavy)

## Example Test Workflow

After `make up`: `make health` then `make ingest` (or use the curl/Python steps below).

```bash
# 1. Check health
make health
# or: curl http://localhost:3000/health

# 2. Create an order
ORDER_RESPONSE=$(curl -s -X POST http://localhost:3000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "customer-123",
    "items": [
      {"productId": "prod-1", "name": "Laptop", "price": 999.99, "quantity": 1}
    ]
  }')

# Extract order ID
ORDER_ID=$(echo $ORDER_RESPONSE | grep -o '"orderId":"[^"]*' | cut -d'"' -f4)

# 3. Get the order
curl http://localhost:3000/orders/$ORDER_ID

# 4. Pay for the order
curl -X POST http://localhost:3000/orders/$ORDER_ID/pay \
  -H "Content-Type: application/json" \
  -d '{"paymentMethod": "credit_card"}'

# 5. Simulate failure on another order
curl -X POST http://localhost:3000/orders/$ORDER_ID/fail
```

## Data Ingestion

Generate traffic for traces, metrics, and profiling against the running Compose stack. Use the Makefile (recommended) or the Python script from the host.

### Using the Makefile

```bash
make ingest              # 10 orders (default); override: COUNT=20 make ingest
make ingest-continuous   # run for 60s (default); override: DURATION=300 make ingest-continuous
make ingest-failures     # include failure scenarios
```

Variables (set in `.env` or pass on the command line): `URL`, `COUNT`, `DURATION`, `DELAY`.

### Using the Python script

Requires `requests` (e.g. `pip install -r requirements.txt` if present).

```bash
python3 ingest/ingest.py --count 10
python3 ingest/ingest.py --count 50 --failures
python3 ingest/ingest.py --duration 300
python3 ingest/ingest.py --url http://localhost:3000 --count 20
python3 ingest/ingest.py --count 30 --delay 1.0 --quiet
```

Options: `--url`, `--count`, `--duration`, `--failures`, `--delay`, `--quiet`. The script runs health check, creates orders, retrieves them, processes payments, and optionally simulates failures.

## License

Apache License 2.0

