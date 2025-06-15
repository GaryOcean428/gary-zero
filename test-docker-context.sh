#!/bin/bash
# Test what files Docker sees in the build context

echo "Creating test Dockerfile..."
cat > Dockerfile.test << 'EOF'
FROM alpine:latest
WORKDIR /test
COPY . .
RUN echo "=== Files in context ===" && \
    find . -name "docker*" -type f | head -20 && \
    echo "=== Checking docker-entrypoint.sh ===" && \
    ls -la docker-entrypoint.sh 2>&1 || echo "Not found"
EOF

echo "Building test image..."
docker build -f Dockerfile.test -t context-test:latest . --no-cache

echo "Cleaning up..."
rm -f Dockerfile.test
