#!/bin/bash

# Claude Code CLI Installation Script
# This script installs the Claude Code CLI tool

set -e

echo "🔧 Installing Claude Code CLI..."

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm is required but not installed. Please install Node.js and npm first."
    exit 1
fi

# Check if already installed
if command -v claude-code &> /dev/null; then
    echo "✅ Claude Code CLI is already installed:"
    claude-code --version
    exit 0
fi

# Install the CLI
echo "📦 Installing @anthropic/claude-code-cli globally..."
npm install -g @anthropic/claude-code-cli

# Verify installation
if command -v claude-code &> /dev/null; then
    echo "✅ Claude Code CLI installed successfully:"
    claude-code --version
    echo ""
    echo "🔑 Make sure to configure your Anthropic API key:"
    echo "   claude-code auth login"
    echo ""
    echo "📚 For more information, run: claude-code --help"
else
    echo "❌ Installation failed. Please install manually:"
    echo "   npm install -g @anthropic/claude-code-cli"
    exit 1
fi
