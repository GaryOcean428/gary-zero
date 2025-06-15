#!/bin/sh
# Docker entrypoint script for gary-zero
# This script handles signal forwarding and environment variable expansion

set -e

# Default PORT if not set
PORT=${PORT:-50001}

# Execute the main application
exec python run_ui.py --port "$PORT" "$@"
