#!/bin/bash
# Gary-Zero Quick Start Script
cd "$(dirname "$0")"
source .venv/bin/activate 2>/dev/null || {
    echo "Failed to activate virtual environment"
    exit 1
}
export PYTHONPATH="${PYTHONPATH:-}:."
echo "Starting Gary-Zero Web UI..."
python run_ui.py "$@"
