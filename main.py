"""
FastAPI main application for Gary-Zero AI Agent Framework.

This module provides an asynchronous FastAPI application with WebSocket support,
security features, and Railway cloud optimization.
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any

import psutil
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from framework.helpers import dotenv, git

# Set timezone and configure logging
os.environ["TZ"] = "UTC"
time.tzset()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

_startup_time = time.time()
security = HTTPBearer()

# --- Pydantic Models ---
class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: float = Field(default_factory=time.time)
    version: str = "0.9.0"
    environment: str = Field(default_factory=lambda: os.getenv("RAILWAY_ENVIRONMENT", "local"))
    memory_usage: str | None = None
    cpu_usage: str | None = None
    uptime_seconds: float | None = None

class MessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    agent_id: str | None = None
    context: dict[str, Any] | None = None

class MessageResponse(BaseModel):
    status: str
    response: str
    agent_id: str | None = None
    timestamp: float = Field(default_factory=time.time)

# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")

manager = ConnectionManager()

# --- Startup/Shutdown (Lifespan) ---
async def initialize_agent_systems():
    logger.info(f'🚀 Gary-Zero starting on Railway: {os.getenv("RAILWAY_ENVIRONMENT", "local")}')
    # SDK init
    try:
        from framework.helpers.sdk_integration import get_sdk_status, initialize_sdk_integration
        init_results = initialize_sdk_integration({
            "enable_tracing": True,
            "strict_mode": False
        })
        if init_results.get("errors"):
            logger.warning(f"SDK errors: {init_results['errors']}")
        else:
            logger.info("OpenAI Agents SDK integration initialized")
        status = get_sdk_status()
        logger.info(f"SDK status: {status['overall_status']}")
    except Exception as e:
        logger.warning(f"SDK integration error: {e}")

    # Visualization system
    try:
        from framework.helpers.ai_visualization_init import initialize_ai_visualization
        await initialize_ai_visualization()
        logger.info("🎯 AI Action Visualization System initialized")
    except Exception as e:
        logger.warning(f"AI visualization error: {e}")

    # Unified logging & monitoring
    try:
        from framework.logging.unified_logger import get_unified_logger
        from framework.performance.monitor import get_performance_monitor
        unified_logger = get_unified_logger()
        logger.info("📝 Unified logging system initialized")
        performance_monitor = get_performance_monitor()
        await performance_monitor.start()
        logger.info("📊 Performance monitoring system started")
        from framework.logging.unified_logger import EventType, LogEvent, LogLevel
        await unified_logger.log_event(LogEvent(
            event_type=EventType.SYSTEM_EVENT,
            level=LogLevel.INFO,
            message="Gary-Zero FastAPI application started",
            metadata={
                "environment": os.getenv("RAILWAY_ENVIRONMENT", "local"),
                "version": "0.9.0",
                "startup_time": time.time() - _startup_time
            }
        ))
    except Exception as e:
        logger.warning(f"Unified monitoring error: {e}")

async def cleanup_agent_systems():
    logger.info('🛑 Gary-Zero cleanup starting')
    # Visualization cleanup
    try:
        from framework.helpers.ai_visualization_init import shutdown_ai_visualization
        await shutdown_ai_visualization()
        logger.info("🎯 AI Action Visualization System shutdown complete")
    except Exception as e:
        logger.warning(f"AI visualization cleanup error: {e}")
    # Monitoring cleanup
    try:
        from framework.logging.unified_logger import (
            EventType, LogEvent, LogLevel, get_unified_logger,
        )
        from framework.performance.monitor import get_performance_monitor
        unified_logger = get_unified_logger()
        await unified_logger.log_event(LogEvent(
            event_type=EventType.SYSTEM_EVENT,
            level=LogLevel.INFO,
            message="Gary-Zero FastAPI application shutting down",
            metadata={
                "uptime_seconds": time.time() - _startup_time,
                "total_events_logged": unified_logger.get_statistics().get("total_events", 0)
            }
        ))
        performance_monitor = get_performance_monitor()
        await performance_monitor.stop()
        logger.info("📊 Performance monitoring stopped")
    except Exception as e:
        logger.warning(f"Unified monitoring cleanup error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_agent_systems()
    yield
    await cleanup_agent_systems()
    logger.info('🛑 Gary-Zero shutdown complete')

# --- App Initialization ---
from api.gemini_live_api import router as gemini_live_router
from api_bridge_simple import add_enhanced_endpoints, create_api_bridge

app = FastAPI(
    title="Gary-Zero AI Agent Framework",
    description="Autonomous AI Agent Framework with Multi-Agent Cooperation",
    version="0.9.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("RAILWAY_ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("RAILWAY_ENVIRONMENT") != "production" else None
)

# Routers
app.include_router(gemini_live_router)
try:
    from framework.api.monitoring import router as monitoring_router
    app.include_router(monitoring_router)
    logger.info("Unified monitoring API initialized")
except Exception as e:
    logger.warning(f"Monitoring API error: {e}")

# --- Middleware ---
app.add_middleware(GZipMiddleware, minimum_size=1000)
allowed_origins = [
    f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}" if os.getenv('RAILWAY_PUBLIC_DOMAIN') else None,
    os.getenv("FRONTEND_URL", "*"),
    "http://localhost:3000",
    "http://localhost:5173",
]
allowed_origins = [origin for origin in allowed_origins if origin is not None]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# API bridge (backward compatibility)
try:
    create_api_bridge(app)
    logger.info("API bridge initialized")
except Exception as e:
    logger.warning(f"API bridge error: {e}")

# --- Static Files ---
app.mount("/public", StaticFiles(directory="webui/public"), name="public")
app.mount("/css", StaticFiles(directory="webui/css"), name="css")
app.mount("/js", StaticFiles(directory="webui/js"), name="js")
add_enhanced_endpoints(app)

# --- Security ---
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    valid_api_key = dotenv.get_dotenv_value("API_KEY")
    if not valid_api_key or credentials.credentials != valid_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return credentials.credentials

# --- Endpoints ---
@app.get("/health", response_model=HealthResponse)
async def health_check():
    try:
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
    return {
        "status": "ready",
        "service": "gary-zero",
        "timestamp": time.time()
    }

@app.get("/metrics")
async def metrics():
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
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = MessageRequest.model_validate_json(data)
                response = await process_agent_message(message_data)
                await websocket.send_json(response.model_dump())
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
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
    from framework.api.a2a_stream import handle_websocket_connection
    await handle_websocket_connection(websocket, agent_id, session_id, session_token)

async def process_agent_message(message: MessageRequest) -> MessageResponse:
    # TODO: Integrate agent system logic here
    return MessageResponse(
        status="success",
        response=f"Received message: {message.message}",
        agent_id=message.agent_id
    )

# --- Error Handlers ---
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"detail": "Endpoint not found"})

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# --- Root & Static Asset Endpoints ---
@app.get("/")
async def serve_ui():
    return FileResponse("webui/index.html", media_type="text/html")

@app.get("/ui")
async def serve_ui_rendered():
    from framework.helpers.template_helper import render_index_html
    rendered_html = render_index_html()
    return HTMLResponse(content=rendered_html, media_type="text/html")

@app.get("/index.css")
async def serve_index_css():
    return FileResponse("webui/index.css", media_type="text/css")

@app.get("/index.js")
async def serve_index_js():
    return FileResponse("webui/index.js", media_type="application/javascript")

# --- Uvicorn Entrypoint ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("WEB_UI_HOST", "0.0.0.0")
    logger.info(f"Starting Gary-Zero FastAPI server on {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        loop="uvloop" if os.name != "nt" else "asyncio",
        workers=1
    )
