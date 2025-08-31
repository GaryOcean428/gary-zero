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
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from framework.helpers import dotenv, git

# Set timezone and configure logging
os.environ["TZ"] = "UTC"
time.tzset()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

_startup_time = time.time()
security = HTTPBearer()


# --- Pydantic Models ---
class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: float = Field(default_factory=time.time)
    version: str = "0.9.0"
    environment: str = Field(
        default_factory=lambda: os.getenv("RAILWAY_ENVIRONMENT", "local")
    )
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
        logger.info(
            f"WebSocket connected. Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(
            f"WebSocket disconnected. Total connections: {len(self.active_connections)}"
        )

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
    logger.info(
        f"🚀 Gary-Zero starting on Railway: {os.getenv('RAILWAY_ENVIRONMENT', 'local')}"
    )
    # SDK init
    try:
        from framework.helpers.sdk_integration import (
            get_sdk_status,
            initialize_sdk_integration,
        )

        init_results = initialize_sdk_integration(
            {"enable_tracing": True, "strict_mode": False}
        )
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

        await unified_logger.log_event(
            LogEvent(
                event_type=EventType.SYSTEM_EVENT,
                level=LogLevel.INFO,
                message="Gary-Zero FastAPI application started",
                metadata={
                    "environment": os.getenv("RAILWAY_ENVIRONMENT", "local"),
                    "version": "0.9.0",
                    "startup_time": time.time() - _startup_time,
                },
            )
        )
    except Exception as e:
        logger.warning(f"Unified monitoring error: {e}")


async def cleanup_agent_systems():
    logger.info("🛑 Gary-Zero cleanup starting")
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
            EventType,
            LogEvent,
            LogLevel,
            get_unified_logger,
        )
        from framework.performance.monitor import get_performance_monitor

        unified_logger = get_unified_logger()
        await unified_logger.log_event(
            LogEvent(
                event_type=EventType.SYSTEM_EVENT,
                level=LogLevel.INFO,
                message="Gary-Zero FastAPI application shutting down",
                metadata={
                    "uptime_seconds": time.time() - _startup_time,
                    "total_events_logged": unified_logger.get_statistics().get(
                        "total_events", 0
                    ),
                },
            )
        )
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
    logger.info("🛑 Gary-Zero shutdown complete")


# --- App Initialization ---
from api.error_report import router as error_report_router
from api.gemini_live_api import router as gemini_live_router
from api_bridge_simple import add_enhanced_endpoints, create_api_bridge

app = FastAPI(
    title="Gary-Zero AI Agent Framework",
    description="Autonomous AI Agent Framework with Multi-Agent Cooperation",
    version="0.9.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("RAILWAY_ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("RAILWAY_ENVIRONMENT") != "production" else None,
)

# Routers
app.include_router(gemini_live_router)
app.include_router(error_report_router)
try:
    from framework.api.monitoring import router as monitoring_router

    app.include_router(monitoring_router)
    logger.info("Unified monitoring API initialized")
except Exception as e:
    logger.warning(f"Monitoring API error: {e}")

# --- Middleware ---
app.add_middleware(GZipMiddleware, minimum_size=1000)
allowed_origins = [
    (
        f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}"
        if os.getenv("RAILWAY_PUBLIC_DOMAIN")
        else None
    ),
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
    allow_headers=["*"],
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )
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
            uptime_seconds=uptime,
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="degraded", memory_usage="unknown", cpu_usage="unknown"
        )


@app.options("/health")
async def health_check_options():
    """Handle CORS preflight for health endpoint."""
    return JSONResponse(
        status_code=200,
        content={"message": "CORS preflight successful"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )


@app.get("/ready")
async def readiness_check():
    return {"status": "ready", "service": "gary-zero", "timestamp": time.time()}


@app.get("/healthz")
async def health_check_railway():
    """Railway-specific health check endpoint."""
    try:
        memory_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent()
        uptime = time.time() - _startup_time
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "0.9.0",
            "environment": os.getenv("RAILWAY_ENVIRONMENT", "local"),
            "memory_usage": f"{memory_percent:.1f}%",
            "cpu_usage": f"{cpu_percent:.1f}%",
            "uptime_seconds": uptime,
            "service": "gary-zero",
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "degraded",
            "timestamp": time.time(),
            "error": str(e),
            "service": "gary-zero",
        }


@app.options("/ready")
async def readiness_check_options():
    """Handle CORS preflight for ready endpoint."""
    return JSONResponse(
        status_code=200,
        content={"message": "CORS preflight successful"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )


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
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "local"),
    }


@app.options("/metrics")
async def metrics_options():
    """Handle CORS preflight for metrics endpoint."""
    return JSONResponse(
        status_code=200,
        content={"message": "CORS preflight successful"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )


# Add a debug endpoint for production troubleshooting
@app.get("/debug/routes")
async def debug_routes():
    """Debug endpoint to list all registered routes."""
    routes = []
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            routes.append(
                {
                    "path": route.path,
                    "methods": (
                        list(route.methods - {"HEAD", "OPTIONS"})
                        if route.methods
                        else []
                    ),
                    "name": getattr(route, "name", "unnamed"),
                }
            )

    return {"total_routes": len(routes), "routes": routes, "timestamp": time.time()}


@app.options("/debug/routes")
async def debug_routes_options():
    """Handle CORS preflight for debug routes endpoint."""
    return JSONResponse(
        status_code=200,
        content={"message": "CORS preflight successful"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )


# Add API endpoint that accepts both GET and POST
@app.get("/api")
async def api_get():
    """API root endpoint for GET requests."""
    return {
        "message": "Gary-Zero API",
        "version": "0.9.0",
        "status": "running",
        "timestamp": time.time(),
        "methods": ["GET", "POST"],
    }


@app.post("/api")
async def api_post(request: Request):
    """API root endpoint for POST requests."""
    logger.info("API POST request received")

    # Handle different content types
    content_type = request.headers.get("content-type", "")

    try:
        if "application/json" in content_type:
            # JSON request
            json_data = await request.json()
            logger.info(f"API POST JSON: {str(json_data)[:100]}...")

            # Try to parse as MessageRequest for compatibility
            try:
                message_request = MessageRequest(**json_data)
                response = await process_agent_message(message_request)
                return response
            except Exception:
                # Handle as generic JSON
                return {
                    "status": "success",
                    "response": "API JSON data received",
                    "data": json_data,
                    "timestamp": time.time(),
                }
        else:
            # Form data or other types
            form_data = await request.form()
            form_dict = dict(form_data)
            logger.info(f"API POST form: {str(form_dict)[:100]}...")

            return {
                "status": "success",
                "response": "API form data received",
                "data": form_dict,
                "timestamp": time.time(),
            }
    except Exception as e:
        logger.error(f"Error processing API POST: {e}")
        return {
            "status": "error",
            "response": f"Error processing API request: {str(e)}",
            "timestamp": time.time(),
        }


@app.options("/api")
async def api_options():
    """Handle CORS preflight for API endpoint."""
    return JSONResponse(
        status_code=200,
        content={"message": "CORS preflight successful"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )


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
                    status="error", response=f"Error processing message: {str(e)}"
                )
                await websocket.send_json(error_response.model_dump())
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.websocket("/a2a/stream")
async def a2a_stream_endpoint(
    websocket: WebSocket, agent_id: str, session_id: str, session_token: str = None
):
    from framework.api.a2a_stream import handle_websocket_connection

    await handle_websocket_connection(websocket, agent_id, session_id, session_token)


async def process_agent_message(message: MessageRequest) -> MessageResponse:
    # TODO: Integrate agent system logic here
    return MessageResponse(
        status="success",
        response=f"Received message: {message.message}",
        agent_id=message.agent_id,
    )


# --- Error Handlers ---
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Enhanced 404 error handler with detailed diagnostics."""
    logger.error(f"404 Error: {request.method} {request.url.path} not found")

    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "method": request.method,
            "path": str(request.url.path),
            "message": "The requested endpoint does not exist",
            "timestamp": time.time(),
            "available_endpoints": [
                "/health",
                "/ready",
                "/metrics",
                "/",
                "/ui",
                "/docs",
                "/redoc",
                "/ws",
                "/index.css",
                "/index.js",
            ],
        },
    )


@app.exception_handler(405)
async def method_not_allowed_handler(request, exc):
    """Enhanced 405 error handler with detailed diagnostics."""
    logger.error(f"405 Error: {request.method} {request.url.path} method not allowed")

    # Try to get allowed methods for this path
    allowed_methods = []
    for route in app.routes:
        if hasattr(route, "path_regex") and hasattr(route, "methods"):
            if route.path_regex.match(str(request.url.path)):
                allowed_methods.extend(
                    [m for m in route.methods if m not in ["HEAD", "OPTIONS"]]
                )

    return JSONResponse(
        status_code=405,
        content={
            "error": "Method Not Allowed",
            "method": request.method,
            "path": str(request.url.path),
            "allowed_methods": (
                list(set(allowed_methods)) if allowed_methods else ["GET"]
            ),
            "message": f"The {request.method} method is not allowed for this endpoint",
            "timestamp": time.time(),
            "suggestion": "Check the allowed methods or use a different endpoint",
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# --- Root & Static Asset Endpoints ---
@app.get("/")
async def serve_ui():
    return FileResponse("webui/index.html", media_type="text/html")


@app.post("/")
async def serve_ui_post(request: Request):
    """Handle POST requests to root endpoint (common for form submissions)."""
    logger.info("POST request to root endpoint")

    # Handle different content types
    content_type = request.headers.get("content-type", "")

    try:
        if "application/json" in content_type:
            # JSON request
            json_data = await request.json()
            logger.info(f"POST JSON data: {str(json_data)[:100]}...")
            return {
                "status": "success",
                "message": "JSON data received",
                "data": json_data,
                "timestamp": time.time(),
            }
        elif "application/x-www-form-urlencoded" in content_type:
            # Form data
            form_data = await request.form()
            form_dict = dict(form_data)
            logger.info(f"POST form data: {str(form_dict)[:100]}...")
            return {
                "status": "success",
                "message": "Form submission received",
                "data": form_dict,
                "timestamp": time.time(),
            }
        elif "multipart/form-data" in content_type:
            # Multipart form (file uploads)
            form_data = await request.form()
            form_dict = {}
            for key, value in form_data.items():
                if hasattr(value, "filename"):
                    # File upload
                    form_dict[key] = f"FILE: {value.filename}"
                else:
                    form_dict[key] = str(value)
            logger.info(f"POST multipart data: {str(form_dict)[:100]}...")
            return {
                "status": "success",
                "message": "Multipart form submission received",
                "data": form_dict,
                "timestamp": time.time(),
            }
        else:
            # Raw body or unknown content type
            body = await request.body()
            logger.info(
                f"POST raw body (content-type: {content_type}): {str(body)[:100]}..."
            )
            return {
                "status": "success",
                "message": "Raw POST data received",
                "content_type": content_type,
                "data_length": len(body),
                "timestamp": time.time(),
            }
    except Exception as e:
        logger.error(f"Error processing POST request: {e}")
        return {
            "status": "error",
            "message": f"Error processing request: {str(e)}",
            "timestamp": time.time(),
        }


@app.options("/")
async def serve_ui_options():
    """Handle CORS preflight for root endpoint."""
    return JSONResponse(
        status_code=200,
        content={"message": "CORS preflight successful"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )


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


# Catch-all route for unmatched paths to prevent 404/405 issues
@app.api_route(
    "/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
)
async def catch_all(request: Request, path: str):
    """Catch-all route to handle unregistered paths with appropriate responses."""
    method = request.method
    full_path = f"/{path}"

    logger.warning(f"Unmatched route accessed: {method} {full_path}")

    # Handle OPTIONS requests for CORS
    if method == "OPTIONS":
        return JSONResponse(
            status_code=200,
            content={"message": "CORS preflight successful"},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            },
        )

    # For other methods, return 404 with helpful information
    return JSONResponse(
        status_code=404,
        content={
            "error": "Route not found",
            "method": method,
            "path": full_path,
            "message": f"The endpoint {full_path} does not exist",
            "timestamp": time.time(),
            "suggestion": "Check available routes at /debug/routes",
            "available_endpoints": [
                "/",
                "/health",
                "/ready",
                "/metrics",
                "/api",
                "/ui",
                "/docs",
                "/redoc",
                "/ws",
                "/index.css",
                "/index.js",
            ],
        },
    )


# --- Uvicorn Entrypoint ---
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("WEB_UI_HOST", "0.0.0.0")
    logger.info(f"Starting Gary-Zero FastAPI server on {host}:{port}")

    # Use asyncio loop for better compatibility
    loop = "asyncio"
    try:
        import uvloop

        loop = "uvloop"
        logger.info("Using uvloop for better performance")
    except ImportError:
        logger.info("uvloop not available, using asyncio")

    uvicorn.run("main:app", host=host, port=port, reload=False, loop=loop, workers=1)
