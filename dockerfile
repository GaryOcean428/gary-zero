# Build arguments for metadata (passed by Docker Hub hooks)
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=dev
ARG DOCKER_TAG=latest

# ========== Builder Stage ==========
FROM python:3.11-alpine AS builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PYTHONPATH=/app

# Install build dependencies for Alpine
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    curl \
    git \
    linux-headers \
    # Additional common dependencies for Python packages
    zlib-dev \
    jpeg-dev \
    libxml2-dev \
    libxslt-dev \
    postgresql-dev

# Set working directory
WORKDIR /app

# Copy dependency files first to leverage Docker cache
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ========== Runtime Stage ==========
FROM python:3.11-alpine

# Re-declare build arguments to use in this stage
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION
ARG DOCKER_TAG

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
    WEB_UI_PORT=50001 \
    WEB_UI_HOST=0.0.0.0 \
    USE_CLOUDFLARE=false \
    TOKENIZERS_PARALLELISM=true \
    PYDEVD_DISABLE_FILE_VALIDATION=1 \
    OLLAMA_BASE_URL=http://127.0.0.1:11434 \
    LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1 \
    OPEN_ROUTER_BASE_URL=https://openrouter.ai/api/v1 \
    SAMBANOVA_BASE_URL=https://fast-api.snova.ai/v1

# Install runtime dependencies
RUN apk add --no-cache \
    curl \
    git \
    libffi \
    openssl \
    # Runtime libraries for compiled Python packages
    zlib \
    libjpeg \
    libxml2 \
    libxslt \
    libpq

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

# Create necessary directories and handle entrypoint script
RUN mkdir -p logs work_dir tmp memory tmp/scheduler && \
    echo '[]' > /app/tmp/scheduler/tasks.json && \
    if [ -f /app/docker-entrypoint.sh ]; then chmod +x /app/docker-entrypoint.sh; fi

# Create non-root user for security
RUN addgroup -g 1001 appgroup && \
    adduser -D -u 1001 -G appgroup appuser && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose the web UI port
EXPOSE 50001

# Set the entrypoint and command
# If docker-entrypoint.sh exists, use it; otherwise run directly
ENTRYPOINT ["/bin/sh", "-c", "if [ -f /app/docker-entrypoint.sh ]; then exec /app/docker-entrypoint.sh \"$@\"; else exec \"$@\"; fi", "--"]
CMD ["python", "run_ui.py", "--port", "50001"]
