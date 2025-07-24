#!/bin/bash

# Qwen Coder CLI Installation Script
# This script installs the Qwen Coder CLI tool

set -e

echo "🔧 Installing Qwen Coder CLI..."

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "❌ pip is required but not installed. Please install Python and pip first."
    exit 1
fi

# Check if already installed
if command -v qwen-coder &> /dev/null; then
    echo "✅ Qwen Coder CLI is already installed:"
    qwen-coder --version 2>/dev/null || echo "Version check failed, but CLI is available"
    exit 0
fi

# Install the CLI
echo "📦 Installing qwen-coder-cli..."
pip install qwen-coder-cli

# Verify installation
if command -v qwen-coder &> /dev/null; then
    echo "✅ Qwen Coder CLI installed successfully"
    qwen-coder --version 2>/dev/null || echo "CLI installed successfully"
    echo ""
    echo "🔑 Make sure to configure your Qwen API key:"
    echo "   qwen-coder config set api_key YOUR_QWEN_API_KEY"
    echo ""
    echo "🌐 Get your API key from: https://dashscope.aliyun.com/"
    echo ""
    echo "📚 For more information, run: qwen-coder --help"
else
    echo "❌ Installation failed. Please install manually:"
    echo "   pip install qwen-coder-cli"
    exit 1
fi
