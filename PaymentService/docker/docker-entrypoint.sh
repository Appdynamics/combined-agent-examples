#!/bin/bash
# Docker entrypoint: run PaymentService with optional AppDynamics dual agent.
# When APPD_CONTROLLER_HOST is set and the agent jar exists, starts Java with
# -javaagent and dual mode (AppD + Splunk OTel). Agent path is fixed; override with APPD_AGENT_JAR.

set -e

PORT="${PORT:-8080}"
JAVA_OPTS="-Dserver.port=${PORT}"

# AppD agent path (version-independent default; override with APPD_AGENT_JAR)
if [ -z "${APPD_AGENT_JAR}" ]; then
  if [ -f /app/agents/javaagent.jar ]; then
    APPD_AGENT_JAR="/app/agents/javaagent.jar"
  else
    APPD_AGENT_JAR=$(find /app/agents -maxdepth 3 -path '*/ver*/javaagent.jar' -type f 2>/dev/null | head -1)
  fi
fi

if [ -n "${APPD_CONTROLLER_HOST}" ] && [ -n "${APPD_AGENT_JAR}" ] && [ -f "$APPD_AGENT_JAR" ]; then
  echo "[PaymentService] AppDynamics agent initialized (dual mode, Splunk OTel via agent)"
  echo "[PaymentService] Agent: $APPD_AGENT_JAR"

  # AppD looks for OTel agent in <agent-dir>/otel; symlink so agents/otel is used when present
  AGENT_DIR="$(dirname "$APPD_AGENT_JAR")"
  if [ ! -e "${AGENT_DIR}/otel" ] && [ -d /app/agents/otel ]; then
    ln -sf /app/agents/otel "${AGENT_DIR}/otel"
    echo "[PaymentService] Linked ${AGENT_DIR}/otel -> /app/agents/otel (OTel agent location)"
  fi

  APPD_ARGS=""
  APPD_ARGS="${APPD_ARGS} -Dappdynamics.controller.hostName=${APPD_CONTROLLER_HOST}"
  APPD_ARGS="${APPD_ARGS} -Dappdynamics.controller.port=${APPD_CONTROLLER_PORT:-443}"
  APPD_ARGS="${APPD_ARGS} -Dappdynamics.controller.ssl.enabled=${APPD_CONTROLLER_SSL:-true}"
  APPD_ARGS="${APPD_ARGS} -Dappdynamics.agent.accountName=${APPD_ACCOUNT_NAME}"
  APPD_ARGS="${APPD_ARGS} -Dappdynamics.agent.accountAccessKey=${APPD_ACCOUNT_ACCESS_KEY}"
  APPD_ARGS="${APPD_ARGS} -Dappdynamics.agent.applicationName=${APPD_APP_NAME}"
  APPD_ARGS="${APPD_ARGS} -Dappdynamics.agent.tierName=${APPD_TIER_NAME:-PaymentService}"
  APPD_ARGS="${APPD_ARGS} -Dappdynamics.agent.nodeName=${APPD_NODE_NAME:-PaymentNode}"

  # OTLP export target: PaymentService sends to collector; only the collector needs SPLUNK_* for Splunk
  OTEL_ENDPOINT="${OTEL_EXPORTER_OTLP_ENDPOINT:-http://otel-collector:4318}"
  OTEL_ARGS=""
  OTEL_ARGS="${OTEL_ARGS} -Dotel.service.name=PaymentService"
  OTEL_ARGS="${OTEL_ARGS} -Dotel.exporter.otlp.endpoint=${OTEL_ENDPOINT}"
  OTEL_ARGS="${OTEL_ARGS} -Dotel.resource.attributes=${OTEL_RESOURCE_ATTRIBUTES:-deployment.environment=payment-space,service.namespace=payment-space,service.name=PaymentService,service.version=1.0.0}"

  AGENT_DEPLOYMENT_MODE="${AGENT_DEPLOYMENT_MODE:-dual}"
  JAVA_AGENT="-javaagent:${APPD_AGENT_JAR}"
  JAVA_OPTS="${JAVA_AGENT} ${APPD_ARGS} ${OTEL_ARGS} -Dagent.deployment.mode=${AGENT_DEPLOYMENT_MODE} ${JAVA_OPTS}"

  echo "AppD Application: ${APPD_APP_NAME} Tier: ${APPD_TIER_NAME:-PaymentService} Node: ${APPD_NODE_NAME:-PaymentNode}"
  echo "[PaymentService] OTLP export target: ${OTEL_ENDPOINT} (OTel agent: agents/otel, linked under agent dir if needed)"
else
  if [ -n "${APPD_CONTROLLER_HOST}" ] && ( [ -z "${APPD_AGENT_JAR}" ] || [ ! -f "${APPD_AGENT_JAR}" ] ); then
    echo "[PaymentService] APPD_CONTROLLER_HOST is set but agent jar not found. Place javaagent.jar at agents/javaagent.jar or agents/ver*/javaagent.jar, or set APPD_AGENT_JAR in .env."
  fi
fi

echo "=============================================="
echo "PaymentService starting on port ${PORT}"
echo "=============================================="

exec java ${JAVA_OPTS} -jar /app/app.jar
