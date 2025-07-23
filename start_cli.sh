#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate 2>/dev/null || {
    echo "Failed to activate virtual environment"
    exit 1
}
export PYTHONPATH="${PYTHONPATH:-}:."
python run_cli.py "$@"
