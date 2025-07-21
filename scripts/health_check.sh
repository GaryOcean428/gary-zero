#!/bin/bash
# Quick health check script for Gary-Zero Railway deployment

echo "🏥 Gary-Zero Health Check"
echo "========================="
echo ""

# Get the Railway public URL from environment or use provided argument
if [ -n "$1" ]; then
    BASE_URL="$1"
elif [ -n "$RAILWAY_PUBLIC_DOMAIN" ]; then
    BASE_URL="https://$RAILWAY_PUBLIC_DOMAIN"
else
    echo "Usage: $0 <gary-zero-url>"
    echo "Example: $0 https://gary-zero-production.up.railway.app"
    exit 1
fi

echo "🌐 Testing: $BASE_URL"
echo ""

# Test health endpoint
echo "1. Health Check (/health):"
echo "--------------------------"
curl -s -w "\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" \
     "$BASE_URL/health" | jq . 2>/dev/null || echo "Failed to parse JSON"

echo ""
echo "2. Readiness Check (/ready):"
echo "----------------------------"
curl -s -w "\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" \
     "$BASE_URL/ready" | jq . 2>/dev/null || echo "Failed to parse JSON"

# Test diagnostics if credentials are provided
if [ -n "$AUTH_LOGIN" ] && [ -n "$AUTH_PASSWORD" ]; then
    echo ""
    echo "3. Diagnostics Check (/diagnostics):"
    echo "------------------------------------"
    curl -s -u "$AUTH_LOGIN:$AUTH_PASSWORD" \
         -H "Content-Type: application/json" \
         -d '{"test": "searchxng"}' \
         -w "\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" \
         "$BASE_URL/diagnostics" | jq . 2>/dev/null || echo "Failed to parse JSON"
else
    echo ""
    echo "ℹ️  Skipping diagnostics test (set AUTH_LOGIN and AUTH_PASSWORD to test)"
fi

echo ""
echo "✅ Health check complete!"
