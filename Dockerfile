# Build arguments for metadata (passed by Docker Hub hooks)
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=dev
ARG DOCKER_TAG=latest

# Railway environment variables (available during build)
ARG RAILWAY_SERVICE_NAME
ARG RAILWAY_ENVIRONMENT
ARG RAILWAY_PROJECT_NAME
ARG RAILWAY_DEPLOYMENT_ID

# PORT configuration for Railway
ARG PORT=8000

# ========== Builder Stage ==========
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PYTHONPATH=/app \
    DEBIAN_FRONTEND=noninteractive

# Install build dependencies for Ubuntu/Debian
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpq-dev \
    pkg-config \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files first to leverage Docker cache
COPY requirements.txt ./

# Install Python dependencies with Railway-compatible cache optimization
RUN --mount=type=cache,id=s/eef92461-60f6-4937-a828-fd5cfd6440d7-pip,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# ========== Runtime Stage ==========
FROM python:3.11-slim

# Re-declare build arguments to use in this stage
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION
ARG DOCKER_TAG
ARG PORT

# Set metadata labels
LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.title="Gary Zero - Personal Development Agent" \
      org.opencontainers.image.description="Gary Zero - A general purpose AI agent framework" \
      org.opencontainers.image.vendor="Gary Zero Project" \
      org.opencontainers.image.source="https://github.com/GaryOcean428/agent-zero" \
      org.opencontainers.image.url="https://hub.docker.com/r/garyocean77/gary-zero" \
      org.opencontainers.image.documentation="https://github.com/GaryOcean428/agent-zero/blob/main/README.md" \
      maintainer="GaryOcean77"

# Set runtime environment variables (non-sensitive defaults)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=${PORT} \
    WEB_UI_PORT=50001 \
    WEB_UI_HOST=0.0.0.0 \
    USE_CLOUDFLARE=false \
    TOKENIZERS_PARALLELISM=true \
    PYDEVD_DISABLE_FILE_VALIDATION=1 \
    OLLAMA_BASE_URL=http://127.0.0.1:11434 \
    LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1 \
    OPEN_ROUTER_BASE_URL=https://openrouter.ai/api/v1 \
    SAMBANOVA_BASE_URL=https://fast-api.snova.ai/v1 \
    DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    libffi8 \
    libssl3 \
    libxml2 \
    libxslt1.1 \
    zlib1g \
    libjpeg62-turbo \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code - adjusted for actual project structure
COPY . .

# Handle .env file - use existing .env or example.env as fallback
RUN if [ ! -f /app/.env ] && [ -f /app/example.env ]; then \
        cp /app/example.env /app/.env; \
    fi

# Create necessary directories, volume mount point, and set up entrypoint script
RUN mkdir -p logs work_dir tmp memory tmp/scheduler /app/data && \
    echo '[]' > /app/tmp/scheduler/tasks.json && \
    chmod +x /app/docker-entrypoint.sh && \
    chmod +x /app/scripts/init_volumes.py

# Expose the configured port (Railway compatible)
EXPOSE $PORT

# Use entrypoint script for robust PORT handling
ENTRYPOINT ["/app/docker-entrypoint.sh"]
