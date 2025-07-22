#!/bin/bash

# Google Gemini CLI Installation Script
# This script installs the Google Gemini CLI tool

set -e

echo "🔧 Installing Google Gemini CLI..."

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "❌ pip is required but not installed. Please install Python and pip first."
    exit 1
fi

# Check if already installed
if command -v gemini &> /dev/null; then
    echo "✅ Google Gemini CLI is already installed:"
    gemini --version 2>/dev/null || echo "Version check failed, but CLI is available"
    exit 0
fi

# Install the CLI
echo "📦 Installing google-generativeai[cli]..."
pip install google-generativeai[cli]

# Verify installation
if command -v gemini &> /dev/null; then
    echo "✅ Google Gemini CLI installed successfully"
    gemini --version 2>/dev/null || echo "CLI installed successfully"
    echo ""
    echo "🔑 Make sure to configure your Google AI API key:"
    echo "   gemini config set api_key YOUR_GOOGLE_AI_API_KEY"
    echo ""
    echo "🌐 Get your API key from: https://ai.google.dev/"
    echo ""
    echo "📚 For more information, run: gemini --help"
else
    echo "❌ Installation failed. Please install manually:"
    echo "   pip install google-generativeai[cli]"
    exit 1
fi