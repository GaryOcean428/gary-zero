"""
FastAPI main application for Gary-Zero AI Agent Framework.

This module provides an asynchronous FastAPI application with WebSocket support,
security features, and Railway cloud optimization.
"""

import os
import time
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, Optional

import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from framework.helpers import dotenv, git

# Set timezone and configure logging
os.environ["TZ"] = "UTC"
time.tzset()

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Track application startup time
_startup_time = time.time()

# Security scheme
security = HTTPBearer()

# Pydantic models for request/response validation
class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = "healthy"
    timestamp: float = Field(default_factory=time.time)
    version: str = "0.9.0"
    environment: str = Field(default_factory=lambda: os.getenv("RAILWAY_ENVIRONMENT", "local"))
    memory_usage: Optional[str] = None
    cpu_usage: Optional[str] = None
    uptime_seconds: Optional[float] = None

class MessageRequest(BaseModel):
    """WebSocket message request model."""
    message: str = Field(..., min_length=1, max_length=10000)
    agent_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class MessageResponse(BaseModel):
    """WebSocket message response model."""
    status: str
    response: str
    agent_id: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)

class ConnectionManager:
    """Manages WebSocket connections for real-time agent communication."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected WebSocket clients."""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")

# Initialize connection manager
manager = ConnectionManager()

async def initialize_agent_systems():
    """Initialize agent systems on startup."""
    logger.info(f'🚀 Gary-Zero starting on Railway: {os.getenv("RAILWAY_ENVIRONMENT", "local")}')
    
    # Initialize OpenAI Agents SDK integration
    try:
        from framework.helpers.sdk_integration import initialize_sdk_integration, get_sdk_status
        
        # Initialize SDK components
        init_results = initialize_sdk_integration({
            "enable_tracing": True,
            "strict_mode": False  # Start with permissive guardrails
        })
        
        # Log initialization results
        if init_results.get("errors"):
            logger.warning(f"SDK initialization had errors: {init_results['errors']}")
        else:
            logger.info("OpenAI Agents SDK integration initialized successfully")
        
        # Get and log status
        status = get_sdk_status()
        logger.info(f"SDK integration status: {status['overall_status']}")
        
    except Exception as e:
        logger.warning(f"Could not initialize SDK integration: {e}")
        logger.info("Continuing with traditional Gary-Zero functionality")
    
    # Initialize AI Action Visualization System
    try:
        from framework.helpers.ai_visualization_init import initialize_ai_visualization
        await initialize_ai_visualization()
        logger.info("🎯 AI Action Visualization System initialized successfully")
    except Exception as e:
        logger.warning(f"Could not initialize AI visualization system: {e}")
        logger.info("Continuing without AI action visualization")
    
    # TODO: Initialize other agent systems here
    # This will be connected to the existing agent initialization logic

async def cleanup_agent_systems():
    """Cleanup agent systems on shutdown."""
    logger.info('🛑 Gary-Zero cleanup starting')
    
    # Cleanup AI Action Visualization System
    try:
        from framework.helpers.ai_visualization_init import shutdown_ai_visualization
        await shutdown_ai_visualization()
        logger.info("🎯 AI Action Visualization System shutdown complete")
    except Exception as e:
        logger.warning(f"Error during AI visualization cleanup: {e}")
    
    # TODO: Add other cleanup logic here

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown procedures."""
    # Startup
    await initialize_agent_systems()
    yield
    # Shutdown
    await cleanup_agent_systems()
    logger.info('🛑 Gary-Zero shutdown complete')

# Add API bridge integration
from api_bridge_simple import create_api_bridge, add_enhanced_endpoints

# Import Gemini Live API router
from api.gemini_live_api import router as gemini_live_router

# Create FastAPI application with lifecycle management
app = FastAPI(
    title="Gary-Zero AI Agent Framework",
    description="Autonomous AI Agent Framework with Multi-Agent Cooperation",
    version="0.9.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("RAILWAY_ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("RAILWAY_ENVIRONMENT") != "production" else None
)

# Include API routers
app.include_router(gemini_live_router)

# Add middleware for Railway optimization
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware configuration for Railway
allowed_origins = [
    f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}" if os.getenv('RAILWAY_PUBLIC_DOMAIN') else None,
    os.getenv("FRONTEND_URL", "*"),
    "http://localhost:3000",  # Development frontend
    "http://localhost:5173",  # Vite development server
]
# Filter out None values
allowed_origins = [origin for origin in allowed_origins if origin is not None]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialize API bridge for backward compatibility
try:
    create_api_bridge(app)
    logger.info("API bridge initialized successfully")
except Exception as e:
    logger.warning(f"Could not initialize API bridge: {e}")
    logger.info("Continuing with FastAPI-only functionality")

# Mount webui static files for non-root paths first
app.mount("/public", StaticFiles(directory="webui/public"), name="public")
app.mount("/css", StaticFiles(directory="webui/css"), name="css")
app.mount("/js", StaticFiles(directory="webui/js"), name="js")

# Add enhanced API endpoints
add_enhanced_endpoints(app)

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key for protected endpoints."""
    valid_api_key = dotenv.get_dotenv_value("API_KEY")
    if not valid_api_key or credentials.credentials != valid_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return credentials.credentials

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for Railway monitoring.
    
    Returns system metrics and application status.
    """
    try:
        # Get system metrics
        memory_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent()
        uptime = time.time() - _startup_time
        
        return HealthResponse(
            memory_usage=f"{memory_percent:.1f}%",
            cpu_usage=f"{cpu_percent:.1f}%",
            uptime_seconds=uptime
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="degraded",
            memory_usage="unknown",
            cpu_usage="unknown"
        )

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint for Railway deployment verification."""
    return {
        "status": "ready",
        "service": "gary-zero",
        "timestamp": time.time()
    }

@app.get("/metrics")
async def metrics():
    """
    Metrics endpoint for Railway monitoring.
    
    Returns detailed application metrics.
    """
    try:
        gitinfo = git.get_git_info()
    except Exception:
        gitinfo = {"version": "unknown", "commit_time": "unknown"}
    
    return {
        "active_websocket_connections": len(manager.active_connections),
        "uptime_seconds": time.time() - _startup_time,
        "memory_usage_percent": psutil.virtual_memory().percent,
        "cpu_usage_percent": psutil.cpu_percent(),
        "version": gitinfo.get("version", "unknown"),
        "commit_time": gitinfo.get("commit_time", "unknown"),
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "local")
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time agent communication.
    
    Handles bidirectional communication between clients and AI agents.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse message using Pydantic model
                message_data = MessageRequest.model_validate_json(data)
                
                # TODO: Process agent message - connect to existing agent logic
                response = await process_agent_message(message_data)
                
                # Send response back to client
                await websocket.send_json(response.model_dump())
                
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                error_response = MessageResponse(
                    status="error",
                    response=f"Error processing message: {str(e)}"
                )
                await websocket.send_json(error_response.model_dump())
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.websocket("/a2a/stream")
async def a2a_stream_endpoint(websocket: WebSocket, agent_id: str, session_id: str, session_token: str = None):
    """
    A2A WebSocket endpoint for real-time agent-to-agent streaming communication.
    
    Enables persistent bidirectional communication between A2A-compliant agents.
    """
    from framework.api.a2a_stream import handle_websocket_connection
    await handle_websocket_connection(websocket, agent_id, session_id, session_token)

async def process_agent_message(message: MessageRequest) -> MessageResponse:
    """
    Process incoming agent messages.
    
    TODO: Connect this to the existing agent processing logic.
    """
    # Placeholder for agent message processing
    # This will be connected to the existing agent system
    
    return MessageResponse(
        status="success",
        response=f"Received message: {message.message}",
        agent_id=message.agent_id
    )

# Error handler for 404 errors
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors with JSON response."""
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
    )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Serve index.html at root without blocking other routes
@app.get("/")
async def serve_ui():
    """Serve the web UI index.html at root."""
    from fastapi.responses import FileResponse
    return FileResponse("webui/index.html", media_type="text/html")

# Serve critical webui root files
@app.get("/index.css")
async def serve_index_css():
    """Serve index.css from webui root."""
    from fastapi.responses import FileResponse
    return FileResponse("webui/index.css", media_type="text/css")

@app.get("/index.js")
async def serve_index_js():
    """Serve index.js from webui root."""
    from fastapi.responses import FileResponse
    return FileResponse("webui/index.js", media_type="application/javascript")

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("WEB_UI_HOST", "0.0.0.0")
    
    logger.info(f"Starting Gary-Zero FastAPI server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,  # Disable reload in production
        loop="uvloop" if os.name != "nt" else "asyncio",  # Use uvloop on Unix systems
        workers=1  # Start with single worker, Railway will handle scaling
    )