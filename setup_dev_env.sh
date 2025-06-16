#!/bin/bash
# Setup development environment for Zero project

# Exit on error
set -e

echo "Setting up development environment for Zero project..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install development dependencies
echo "Installing development dependencies..."
pip install -r requirements-dev.txt

# Install the package in development mode
echo "Installing Zero in development mode..."
pip install -e .

echo ""
echo "Development environment setup complete!"
echo "To activate the virtual environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To run tests:"
echo "  pytest python/tests/"
echo ""
echo "To run the application:"
echo "  python run_ui.py  # For UI mode"
echo "  python run_cli.py  # For CLI mode"
