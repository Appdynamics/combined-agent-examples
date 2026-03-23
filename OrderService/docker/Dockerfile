FROM node:23-alpine

# Install wget for health checks
RUN apk add --no-cache wget

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (npm install works even if lock file is slightly out of sync)
RUN npm install

# Copy application files
COPY . .

# Create logs directory
RUN mkdir -p logs && chmod 777 logs

# Expose port
EXPOSE 3000

# Set environment variables
ENV NODE_ENV=production
ENV PORT=3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:3000/health || exit 1

# Start the application (server lives in src/ when build context is repo root)
CMD ["node", "src/server.js"]

