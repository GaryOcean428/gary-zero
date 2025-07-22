#!/bin/bash

# OpenAI Codex CLI Installation Script
# This script installs the OpenAI Codex CLI tool

set -e

echo "🔧 Installing OpenAI Codex CLI..."

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm is required but not installed. Please install Node.js and npm first."
    exit 1
fi

# Check if already installed
if command -v codex &> /dev/null; then
    echo "✅ OpenAI Codex CLI is already installed:"
    codex --version
    exit 0
fi

# Install the CLI
echo "📦 Installing @openai/codex-cli globally..."
npm install -g @openai/codex-cli

# Verify installation
if command -v codex &> /dev/null; then
    echo "✅ OpenAI Codex CLI installed successfully:"
    codex --version
    echo ""
    echo "🔑 Make sure to configure your OpenAI API key:"
    echo "   codex config set api-key YOUR_API_KEY"
    echo ""
    echo "📚 For more information, run: codex --help"
else
    echo "❌ Installation failed. Please install manually:"
    echo "   npm install -g @openai/codex-cli"
    exit 1
fi