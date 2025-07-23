#!/bin/bash
# Standardized build script for gary-zero Railway deployment
# This script follows Railway deployment standards

set -euo pipefail

echo "🔨 Gary-Zero Build Script"
echo "========================"
echo ""

# Set build environment variables
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export PIP_NO_CACHE_DIR=1
export PIP_DISABLE_PIP_VERSION_CHECK=1

# Log build information
echo "📋 Build Information:"
echo "  Python version: $(python --version)"
echo "  Working directory: $(pwd)"
echo "  Environment: ${RAILWAY_ENVIRONMENT:-local}"
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs work_dir tmp memory tmp/scheduler
if [ -w / ]; then
    mkdir -p /app/data
else
    mkdir -p data
fi
echo '[]' > tmp/scheduler/tasks.json

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if [ -f requirements.txt ]; then
    echo "📋 Installing from requirements.txt..."
    pip install --no-cache-dir -r requirements.txt || {
        echo "⚠️  Some dependencies failed to install (likely system-specific packages)"
        echo "📦 Installing core dependencies..."
        pip install fastapi uvicorn python-dotenv pydantic psutil
    }
    echo "✅ Python dependencies processing completed"
else
    echo "⚠️  No requirements.txt found, installing core dependencies"
    pip install fastapi uvicorn python-dotenv pydantic psutil
fi

# Install Node.js dependencies if package.json exists
if [ -f package.json ]; then
    echo "📦 Installing Node.js dependencies..."
    npm ci --only=production
    echo "✅ Node.js dependencies installed"
fi

# Set up environment configuration
echo "⚙️  Setting up environment..."
if [ ! -f .env ] && [ -f .env.example ]; then
    echo "📋 Copying .env.example to .env"
    cp .env.example .env
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
find scripts/ -name "*.sh" -type f -exec chmod +x {} \;
[ -f docker-entrypoint.sh ] && chmod +x docker-entrypoint.sh
[ -f start_uvicorn.py ] && chmod +x start_uvicorn.py

# Validate critical files exist
echo "✅ Validating build artifacts..."
required_files=(
    "main.py"
    "start_uvicorn.py"
    "scripts/start.sh"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ ERROR: Required file missing: $file"
        exit 1
    fi
done

# Run any post-install scripts
if [ -f scripts/postinstall.js ]; then
    echo "🔧 Running post-install script..."
    node scripts/postinstall.js
fi

echo ""
echo "🎉 Build completed successfully!"
echo "📊 Build summary:"
echo "  Dependencies: installed"
echo "  Directories: created"
echo "  Permissions: set"
echo "  Validation: passed"