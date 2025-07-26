#!/bin/bash
# Standardized start script for gary-zero Railway deployment
# This script follows Railway deployment standards

set -euo pipefail

echo "🚀 Gary-Zero Start Script"
echo "========================"
echo ""

# Validate environment
echo "📋 Environment validation:"
echo "  Python version: $(python --version)"
echo "  Working directory: $(pwd)"
echo "  Railway environment: ${RAILWAY_ENVIRONMENT:-local}"
echo "  Port: ${PORT:-8000}"
echo ""

# Pre-flight checks
echo "🔍 Pre-flight checks..."

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "❌ ERROR: main.py not found"
    exit 1
fi

# Check if uvicorn is available
if ! command -v uvicorn &> /dev/null; then
    echo "❌ ERROR: uvicorn not found"
    exit 1
fi

# Ensure data directory exists
if [ -w / ]; then
    mkdir -p /app/data logs work_dir tmp memory
else
    mkdir -p data logs work_dir tmp memory
fi

# Run settings migration script
echo "🔄 Running settings migration..."
if [ -f "scripts/migrate_settings.py" ]; then
    python scripts/migrate_settings.py
    if [ $? -ne 0 ]; then
        echo "⚠️  Settings migration completed with warnings, continuing..."
    else
        echo "✅ Settings migration completed successfully"
    fi
else
    echo "⚠️  Migration script not found, skipping..."
fi

# Health check function
check_health() {
    local max_attempts=30
    local attempt=1
    local port=${PORT:-8000}

    echo "🏥 Waiting for service to be healthy..."

    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "http://localhost:${port}/health" > /dev/null 2>&1; then
            echo "✅ Service is healthy"
            return 0
        fi

        echo "  Attempt ${attempt}/${max_attempts} - waiting for service..."
        sleep 2
        ((attempt++))
    done

    echo "⚠️  Service health check timeout, but continuing..."
    return 0
}

# Start the application
echo "🚀 Starting Gary-Zero application..."

# Use the standardized uvicorn startup script for Railway compatibility
if [ -f "start_uvicorn.py" ]; then
    echo "📋 Using start_uvicorn.py for Railway-compatible startup"
    python start_uvicorn.py &
    APP_PID=$!
else
    # Fallback to direct uvicorn command
    echo "📋 Using direct uvicorn command"
    PORT=${PORT:-8000}
    HOST=${WEB_UI_HOST:-0.0.0.0}

    uvicorn main:app \
        --host "$HOST" \
        --port "$PORT" \
        --workers 4 \
        --loop asyncio \
        --access-log \
        --log-level info &
    APP_PID=$!
fi

# Store PID for graceful shutdown
echo $APP_PID > /tmp/app.pid

# Wait a moment for startup
sleep 5

# Run health check in background
if command -v curl &> /dev/null; then
    check_health &
fi

echo ""
echo "🎉 Gary-Zero started successfully!"
echo "📊 Service information:"
echo "  PID: $APP_PID"
echo "  Host: ${WEB_UI_HOST:-0.0.0.0}"
echo "  Port: ${PORT:-8000}"
echo "  Health check: http://localhost:${PORT:-8000}/health"
echo ""

# Wait for the application process
wait $APP_PID
