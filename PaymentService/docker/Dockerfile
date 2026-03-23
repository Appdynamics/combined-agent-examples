# Build stage - Maven image includes Java + Maven (multi-arch: Mac ARM64 + Intel, Linux)
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /app

COPY pom.xml .
RUN mvn -B dependency:go-offline -DskipTests

COPY src ./src
RUN mvn -B package -DskipTests

# Runtime stage - multi-arch (amd64 + arm64)
FROM eclipse-temurin:17-jre-jammy

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=build /app/target/payment-service-*.jar app.jar
COPY docker/docker-entrypoint.sh /app/scripts/docker-entrypoint.sh
RUN chmod +x /app/scripts/docker-entrypoint.sh

# Optional: mount agents over /app/agents for AppDynamics dual agent
RUN mkdir -p /app/agents

# Default port; override with PORT env at runtime
ENV PORT=8080
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD sh -c "curl -sf http://localhost:$${PORT:-8080}/health || exit 1"

ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
