#!/bin/sh
set -e

# Export PORT with fallback to 8000 for Railway compatibility
export PORT=${PORT:-8000}

echo "🚀 Starting gunicorn on port $PORT"
echo "🔍 Environment: RAILWAY_ENVIRONMENT=${RAILWAY_ENVIRONMENT:-unknown}"

# Debug environment variables for troubleshooting
echo "🔧 DEBUG: PORT=$PORT, RAILWAY_ENVIRONMENT=$RAILWAY_ENVIRONMENT"
echo "🔧 DEBUG: Railway env vars:"
env | grep -E "(PORT|RAILWAY)" | sort || echo "No Railway environment variables found"

# Wait for application to become ready
sleep 2

# Start gunicorn with robust configuration
exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --preload wsgi:application
