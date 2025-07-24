#!/bin/bash

# ==============================================
# Gary-Zero Development Server (Warp 2.0 Compatible)
# ==============================================
# Starts Gary-Zero with proper port configuration for Warp 2.0

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values (Warp 2.0 port strategy)
DEFAULT_FRONTEND_PORT=5675
DEFAULT_BACKEND_PORT=8765
DEFAULT_MODE="frontend"

# Parse command line arguments
MODE="$DEFAULT_MODE"
PORT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --frontend)
            MODE="frontend"
            PORT="$DEFAULT_FRONTEND_PORT"
            shift
            ;;
        --backend)
            MODE="backend"
            PORT="$DEFAULT_BACKEND_PORT"
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --help|-h)
            echo "Gary-Zero Development Server (Warp 2.0 Compatible)"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --frontend     Start in frontend mode (port 5675)"
            echo "  --backend      Start in backend mode (port 8765)"
            echo "  --port PORT    Use specific port number"
            echo "  --help, -h     Show this help message"
            echo ""
            echo "Warp 2.0 Port Strategy:"
            echo "  Frontend: 5675-5699"
            echo "  Backend:  8765-8799"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Set default port if not specified
if [[ -z "$PORT" ]]; then
    if [[ "$MODE" == "frontend" ]]; then
        PORT="$DEFAULT_FRONTEND_PORT"
    else
        PORT="$DEFAULT_BACKEND_PORT"
    fi
fi

# Validate port ranges (Warp 2.0 strategy)
validate_port() {
    local port="$1"
    local mode="$2"
    
    if [[ "$mode" == "frontend" ]]; then
        if [[ $port -lt 5675 || $port -gt 5699 ]]; then
            echo -e "${YELLOW}Warning: Port $port is outside frontend range (5675-5699)${NC}"
        fi
    elif [[ "$mode" == "backend" ]]; then
        if [[ $port -lt 8765 || $port -gt 8799 ]]; then
            echo -e "${YELLOW}Warning: Port $port is outside backend range (8765-8799)${NC}"
        fi
    fi
}

# Check if port is available
check_port() {
    local port="$1"
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}Error: Port $port is already in use${NC}"
        echo "Try a different port or kill the process using: sudo lsof -ti:$port | xargs kill -9"
        exit 1
    fi
}

# Banner
echo -e "${BLUE}"
echo "=============================================="
echo "  Gary-Zero Development Server (Warp 2.0)"
echo "=============================================="
echo -e "${NC}"

echo -e "${GREEN}Mode:${NC} $MODE"
echo -e "${GREEN}Port:${NC} $PORT"

# Validate configuration
validate_port "$PORT" "$MODE"
check_port "$PORT"

# Check if .env exists
if [[ ! -f ".env" ]]; then
    if [[ -f ".env.example" ]]; then
        echo -e "${YELLOW}Creating .env from .env.example...${NC}"
        cp .env.example .env
    else
        echo -e "${RED}Error: No .env or .env.example file found${NC}"
        exit 1
    fi
fi

# Update port in .env
echo -e "${BLUE}Updating port configuration...${NC}"
if [[ "$MODE" == "frontend" ]]; then
    sed -i.bak "s/^WEB_UI_PORT=.*/WEB_UI_PORT=$PORT/" .env
else
    sed -i.bak "s/^PORT=.*/PORT=$PORT/" .env
fi

# Check for Python virtual environment
if [[ -d ".venv" ]]; then
    echo -e "${GREEN}Activating Python virtual environment...${NC}"
    source .venv/bin/activate
else
    echo -e "${YELLOW}No Python virtual environment found. Creating one...${NC}"
    python -m venv .venv
    source .venv/bin/activate
    
    if [[ -f "requirements.txt" ]]; then
        echo -e "${BLUE}Installing Python dependencies...${NC}"
        pip install -r requirements.txt
    fi
fi

# Install Node.js dependencies if needed
if [[ -f "package.json" ]] && [[ ! -d "node_modules" ]]; then
    echo -e "${BLUE}Installing Node.js dependencies...${NC}"
    npm install
fi

# Export environment variables for Railway compatibility
export PORT="$PORT"
export WEB_UI_PORT="$PORT"
export WEB_UI_HOST="0.0.0.0"

# Start the server
echo -e "${GREEN}Starting Gary-Zero server...${NC}"
echo -e "${BLUE}Access URL: http://localhost:$PORT${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Check if run_ui.py exists
if [[ -f "run_ui.py" ]]; then
    python run_ui.py --port "$PORT"
elif [[ -f "main.py" ]]; then
    python main.py --port "$PORT"
elif [[ -f "app.py" ]]; then
    python app.py --port "$PORT"
else
    echo -e "${RED}Error: No main Python file found (run_ui.py, main.py, or app.py)${NC}"
    exit 1
fi
