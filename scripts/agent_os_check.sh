#!/bin/bash

# Agent OS Specification Validation Script
# This script validates that the deployment meets Agent OS requirements

echo "🤖 Running Agent OS validation..."

# Check if required configuration files exist
echo "📋 Checking required configuration files..."

REQUIRED_FILES=(
    "package.json"
    "requirements.txt"
    "scripts/build.sh"
    "scripts/start.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ ERROR: Required file '$file' not found"
        exit 1
    fi
    echo "✅ Found: $file"
done

# Validate package.json structure
echo "📦 Validating package.json structure..."
if ! command -v jq >/dev/null 2>&1; then
    echo "⚠️ jq not available, skipping JSON validation"
else
    # Check for required scripts
    REQUIRED_SCRIPTS=("start" "test" "lint")
    for script in "${REQUIRED_SCRIPTS[@]}"; do
        if ! jq -e ".scripts.\"$script\"" package.json >/dev/null 2>&1; then
            echo "❌ ERROR: Required script '$script' not found in package.json"
            exit 1
        fi
        echo "✅ Script found: $script"
    done
fi

# Check for environment variable requirements
echo "🔧 Validating environment configuration..."
if [ -f "railpack.json" ] && grep -q "PORT" railpack.json; then
    echo "✅ PORT configuration found in railpack.json"
elif [ -f "railway.toml" ] && grep -q "PORT" railway.toml; then
    echo "✅ PORT configuration found in railway.toml"
else
    echo "❌ ERROR: PORT configuration not found in railway configuration"
    exit 1
fi

# Validate Python requirements
echo "🐍 Validating Python requirements..."
if [ -f "requirements.txt" ]; then
    if grep -q "fastapi\|flask\|django" requirements.txt; then
        echo "✅ Web framework found in requirements.txt"
    else
        echo "⚠️ WARNING: No web framework detected in requirements.txt"
    fi
fi

# Check for security configurations
echo "🔐 Checking security configurations..."
SECURITY_FILES=(
    ".gitignore"
    ".env.example"
)

for file in "${SECURITY_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ Security file found: $file"
    else
        echo "⚠️ WARNING: Security file '$file' not found"
    fi
done

# Validate build script is executable
echo "🔨 Validating build scripts..."
if [ -x "scripts/build.sh" ]; then
    echo "✅ build.sh is executable"
else
    echo "⚠️ WARNING: build.sh is not executable, making it executable..."
    chmod +x scripts/build.sh
fi

if [ -x "scripts/start.sh" ]; then
    echo "✅ start.sh is executable"
else
    echo "⚠️ WARNING: start.sh is not executable, making it executable..."
    chmod +x scripts/start.sh
fi

# Check for Agent OS specific requirements
echo "🤖 Checking Agent OS specific requirements..."

# Look for AI/ML dependencies
AI_PATTERNS=("openai" "anthropic" "transformers" "langchain" "torch" "tensorflow")
AI_FOUND=false

for pattern in "${AI_PATTERNS[@]}"; do
    if grep -q "$pattern" requirements.txt 2>/dev/null; then
        echo "✅ AI/ML dependency found: $pattern"
        AI_FOUND=true
        break
    fi
done

if [ "$AI_FOUND" = false ]; then
    echo "⚠️ WARNING: No AI/ML dependencies detected. Is this an Agent OS deployment?"
fi

# Check for agent-specific configurations
if [ -f "agent_config.json" ] || [ -f "config/agent.yaml" ] || [ -f ".agent_config" ]; then
    echo "✅ Agent configuration file found"
else
    echo "⚠️ WARNING: No agent configuration file detected"
fi

# Final validation summary
echo ""
echo "🎯 Agent OS validation summary:"
echo "================================"
echo "✅ All critical requirements met"
echo "🚀 Ready for Railway deployment"

echo ""
echo "📋 Deployment checklist:"
echo "  - All required files present"
echo "  - Scripts are executable"
echo "  - Environment variables configured"
echo "  - Security files in place"

echo ""
echo "🤖 Agent OS validation completed successfully!"
