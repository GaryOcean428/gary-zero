"""This module runs the Flask web UI and initializes the application."""

import os
import socket
import struct
import threading
import time
from functools import wraps

from flask import Flask, Response, request
from werkzeug.security import check_password_hash, generate_password_hash

import initialize
from framework.helpers import dotenv, files, mcp_server, process, runtime
from framework.helpers.api import ApiHandler
from framework.helpers.auth_rate_limiter import auth_rate_limiter
from framework.helpers.dynamic_prompt_loader import dynamic_prompt_loader
from framework.helpers.extract_tools import load_classes_from_folder
from framework.helpers.files import get_abs_path
from framework.helpers.print_style import PrintStyle
from framework.security.db_auth import DatabaseAuth

# Set the new timezone to 'UTC'
os.environ["TZ"] = "UTC"
# Apply the timezone change
time.tzset()

# Track application startup time
_startup_time = time.time()

# initialize the internal Flask server
webapp = Flask("app", static_folder=get_abs_path("./webui"), static_url_path="/")
webapp.config["JSON_SORT_KEYS"] = False  # Disable key sorting in jsonify
webapp._startup_time = _startup_time  # Store startup time on app instance

lock = threading.Lock()

# Initialize database authentication system with secure fallback
try:
    db_auth = DatabaseAuth()
    PrintStyle().success("Database authentication initialized successfully")
except Exception as e:
    PrintStyle().error(f"Failed to initialize database authentication: {e}")
    # CRITICAL: Abort startup if using insecure default credentials
    auth_login = dotenv.get_dotenv_value("AUTH_LOGIN", "admin")
    auth_password = dotenv.get_dotenv_value("AUTH_PASSWORD", "admin")

    if auth_login == "admin" and auth_password == "admin":
        raise RuntimeError(
            "SECURITY CRITICAL: Default insecure credentials detected (admin/admin) and database authentication failed. "
            "Cannot start server with insecure credentials. Please set secure AUTH_LOGIN and AUTH_PASSWORD environment variables "
            "or fix database connection issues."
        )
    db_auth = None  # Will use fallback authentication


# Add request logging middleware for debugging
@webapp.before_request
def log_request_info():
    """Log request details for debugging."""
    # Only log for settings-related endpoints to avoid spam
    if "/settings" in request.path or request.path in [
        "/settings_get",
        "/settings_set",
    ]:
        PrintStyle().debug(f"Settings request: {request.method} {request.path}")
        PrintStyle().debug(f"Headers: {dict(request.headers)}")
        if request.is_json and request.data:
            try:
                PrintStyle().debug(f"JSON data: {request.get_json()}")
            except Exception as e:
                PrintStyle().debug(f"Invalid JSON data: {e}")


@webapp.after_request
def log_response_info(response):
    """Log response details for debugging."""
    # Only log for settings-related endpoints to avoid spam
    if "/settings" in request.path or request.path in [
        "/settings_get",
        "/settings_set",
    ]:
        PrintStyle().debug(
            f"Settings response: {response.status_code} {response.status}"
        )
        if response.status_code >= 400:
            PrintStyle().error(
                f"Settings error response: {response.get_data(as_text=True)[:200]}"
            )
    return response


def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Only add HSTS if using HTTPS
    if request.is_secure:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    # CSP configured for Alpine.js and external resources with blob: support for dynamic imports
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob: data: cdnjs.cloudflare.com cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com cdn.jsdelivr.net fonts.googleapis.com *.googleapis.com; "
        "font-src 'self' data: cdnjs.cloudflare.com cdn.jsdelivr.net fonts.gstatic.com *.gstatic.com; "
        "img-src 'self' data: blob: https:; "
        "connect-src 'self' ws: wss: http: https:; "
        "worker-src 'self' blob:; "
        "frame-src 'self'; "
        "object-src 'none'"
    )
    return response


webapp.after_request(add_security_headers)


# Custom error handlers
@webapp.errorhandler(404)
def handle_404(e):
    """Handle 404 errors with enhanced diagnostics."""
    from flask import jsonify

    # Log the 404 for debugging
    PrintStyle().error(f"404 Error: {request.method} {request.path} not found")

    # Check if it's an API request (JSON or starts with /api)
    is_api_request = (
        request.is_json
        or request.path.startswith("/api")
        or "application/json" in request.headers.get("Accept", "")
    )

    if is_api_request:
        return jsonify(
            {
                "error": "Not Found",
                "method": request.method,
                "path": request.path,
                "message": "The requested endpoint does not exist",
                "timestamp": time.time(),
                "available_endpoints": [
                    "/",
                    "/health",
                    "/ready",
                    "/privacy",
                    "/terms",
                    "/favicon.ico",
                ],
            }
        ), 404
    else:
        try:
            return files.read_file("./webui/404.html"), 404
        except Exception:
            return Response("Page not found", 404, mimetype="text/plain")


@webapp.errorhandler(405)
def handle_405(e):
    """Handle 405 Method Not Allowed errors with detailed diagnostics."""
    from flask import jsonify

    # Log the 405 for debugging with enhanced information
    PrintStyle().error(f"405 Error: {request.method} {request.path} method not allowed")
    PrintStyle().error(f"Request headers: {dict(request.headers)}")
    PrintStyle().error(f"Request args: {dict(request.args)}")
    if request.method == "POST":
        PrintStyle().error(f"Form data: {dict(request.form)}")
        if request.is_json:
            try:
                PrintStyle().error(f"JSON data: {request.get_json()}")
            except Exception as json_err:
                PrintStyle().error(f"JSON parse error: {json_err}")

    # Get allowed methods for this endpoint
    allowed_methods = []
    if request.url_rule:
        allowed_methods = list(request.url_rule.methods - {"HEAD", "OPTIONS"})
    else:
        # Try to find matching routes
        for rule in webapp.url_map.iter_rules():
            if rule.rule == request.path or (
                hasattr(rule, "match") and rule.match(request.path)
            ):
                allowed_methods.extend(list(rule.methods - {"HEAD", "OPTIONS"}))
        allowed_methods = list(set(allowed_methods))

    # Check if it's an API request
    is_api_request = (
        request.is_json
        or request.path.startswith("/api")
        or "application/json" in request.headers.get("Accept", "")
    )

    error_response = {
        "error": "Method Not Allowed",
        "method": request.method,
        "path": request.path,
        "allowed_methods": allowed_methods,
        "message": f"The {request.method} method is not allowed for this endpoint",
        "timestamp": time.time(),
        "suggestion": "Check the allowed methods or use a different endpoint",
        "debug_info": {
            "user_agent": request.headers.get("User-Agent", "unknown"),
            "remote_addr": request.remote_addr,
            "referrer": request.headers.get("Referer", "none"),
            "content_type": request.headers.get("Content-Type", "none"),
        },
    }

    if is_api_request:
        return jsonify(error_response), 405
    else:
        return Response(
            f"""
        <h1>405 Method Not Allowed</h1>
        <p><strong>Method:</strong> {request.method}</p>
        <p><strong>Path:</strong> {request.path}</p>
        <p><strong>Allowed Methods:</strong> {", ".join(allowed_methods)}</p>
        <p><strong>Timestamp:</strong> {time.time()}</p>
        <p><strong>Suggestion:</strong> {error_response["suggestion"]}</p>
        <details>
            <summary>Debug Information</summary>
            <pre>{error_response["debug_info"]}</pre>
        </details>
        """,
            405,
            mimetype="text/html",
        )


@webapp.errorhandler(500)
def handle_500(e):
    """Handle 500 errors with custom page."""
    try:
        # Log the error for debugging
        PrintStyle().error(f"Server error: {str(e)}")
        return files.read_file("./webui/500.html"), 500
    except Exception:
        return Response("Internal server error", 500, mimetype="text/plain")


@webapp.errorhandler(Exception)
def handle_exception(e):
    """Handle all unhandled exceptions."""
    PrintStyle().error(f"Unhandled exception: {str(e)}")
    try:
        return files.read_file("./webui/500.html"), 500
    except Exception:
        return Response("Internal server error", 500, mimetype="text/plain")


# Add CORS preflight handling
@webapp.before_request
def handle_preflight():
    """Handle CORS preflight OPTIONS requests."""
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response


def is_loopback_address(address):
    """Check if the given address is a loopback address."""
    loopback_checker = {
        socket.AF_INET: lambda x: struct.unpack("!I", socket.inet_aton(x))[0]
        >> (32 - 8)
        == 127,
        socket.AF_INET6: lambda x: x == "::1",
    }
    address_type = "hostname"
    try:
        socket.inet_pton(socket.AF_INET6, address)
        address_type = "ipv6"
    except OSError:
        try:
            socket.inet_pton(socket.AF_INET, address)
            address_type = "ipv4"
        except OSError:
            address_type = "hostname"

    if address_type == "ipv4":
        return loopback_checker[socket.AF_INET](address)
    elif address_type == "ipv6":
        return loopback_checker[socket.AF_INET6](address)
    else:
        for family in (socket.AF_INET, socket.AF_INET6):
            try:
                r = socket.getaddrinfo(address, None, family, socket.SOCK_STREAM)
            except socket.gaierror:
                return False
            for family, _, _, _, sockaddr in r:
                if not loopback_checker[family](sockaddr[0]):
                    return False
        return True


def requires_api_key(f):
    @wraps(f)
    async def decorated(*args, **kwargs):
        valid_api_key = dotenv.get_dotenv_value("API_KEY")
        if api_key := request.headers.get("X-API-KEY"):
            if api_key != valid_api_key:
                return Response("API key required", 401)
        elif request.json and request.json.get("api_key"):
            api_key = request.json.get("api_key")
            if api_key != valid_api_key:
                return Response("API key required", 401)
        else:
            return Response("API key required", 401)
        return await f(*args, **kwargs)

    return decorated


# allow only loopback addresses
def requires_loopback(f):
    """Decorator to ensure a request is from a loopback address."""

    @wraps(f)
    async def decorated(*args, **kwargs):
        if not is_loopback_address(request.remote_addr):
            return Response(
                "Access denied.",
                403,
                {},
            )
        return await f(*args, **kwargs)

    return decorated


# require authentication for handlers
def requires_auth(f):
    """Decorator to require basic authentication for a route."""

    @wraps(f)
    async def decorated(*args, **kwargs):
        # Check rate limiting first
        client_ip = request.remote_addr or "unknown"
        if not auth_rate_limiter.is_auth_allowed(client_ip):
            PrintStyle().warning(f"Authentication rate limit exceeded for {client_ip}")
            return Response(
                "Too many authentication attempts. Please try again later.",
                429,
                {"WWW-Authenticate": 'Basic realm="Rate Limited"'},
            )
        
        auth = request.authorization
        success, user_data = False, None

        if auth:
            if db_auth:
                # Use database-backed authentication
                success, user_data = db_auth.authenticate_user(
                    auth.username, auth.password, ip_address=request.remote_addr
                )
                # Rate limit success logging to prevent spam
                if success and auth_rate_limiter.should_log_success(client_ip):
                    PrintStyle().success(f"User '{auth.username}' authenticated via database from {request.remote_addr}")
            else:
                # Fallback to environment-based authentication with security checks
                user = dotenv.get_dotenv_value("AUTH_LOGIN")
                password = dotenv.get_dotenv_value("AUTH_PASSWORD")

                # Critical: Block insecure default credentials
                if user == "admin" and password == "admin":
                    PrintStyle().error("SECURITY VIOLATION: Attempt to use insecure default credentials admin/admin")
                    return Response(
                        "SECURITY ERROR: Default credentials are not allowed. Please contact administrator.",
                        403,
                        {"WWW-Authenticate": 'Basic realm="Secure Authentication Required"'},
                    )

                if user and password:
                    # Use secure password comparison
                    if auth.username == user and check_password_hash(generate_password_hash(password), auth.password):
                        success = True
                        # Rate limit success logging to prevent spam
                        if auth_rate_limiter.should_log_success(client_ip):
                            PrintStyle().success(f"User '{auth.username}' authenticated via fallback method from {request.remote_addr}")
                    else:
                        PrintStyle().warning(f"Authentication failed for '{auth.username}' via fallback method from {request.remote_addr}")

        if not auth or not success:
            return Response(
                "Could not verify your access level for that URL.\n"
                "You have to login with proper credentials",
                401,
                {"WWW-Authenticate": 'Basic realm="Login Required"'},
            )

        return await f(*args, **kwargs)

    return decorated


@webapp.route("/", methods=["GET", "POST", "OPTIONS"])
@requires_auth
async def serve_index():
    """Serve the main index.html file and handle form submissions."""
    # Handle OPTIONS request for CORS
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        return response

    if request.method == "POST":
        # Handle form submissions or API requests to root
        PrintStyle().debug(f"POST request to root: {request.form}")

        # Check if it's JSON data
        if request.is_json:
            data = request.get_json()
            return {
                "status": "success",
                "message": "JSON data received",
                "data": data,
                "timestamp": time.time(),
            }
        else:
            # Handle form data
            form_data = dict(request.form)
            return {
                "status": "success",
                "message": "Form submission received",
                "data": form_data,
                "timestamp": time.time(),
            }

    # GET request - serve the main page
    from framework.helpers.template_helper import render_index_html

    return render_index_html()


# handle privacy policy page
@webapp.route("/privacy", methods=["GET", "OPTIONS"])
def serve_privacy():
    """Serve the privacy policy page."""
    # Handle OPTIONS request for CORS
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add("Access-Control-Allow-Methods", "GET,OPTIONS")
        return response

    from framework.helpers.template_helper import render_template

    return render_template("./webui/privacy.html")


# handle terms of service page
@webapp.route("/terms", methods=["GET", "OPTIONS"])
def serve_terms():
    """Serve the terms of service page."""
    # Handle OPTIONS request for CORS
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add("Access-Control-Allow-Methods", "GET,OPTIONS")
        return response

    from framework.helpers.template_helper import render_template

    return render_template("./webui/terms.html")


# health check endpoint
@webapp.route("/health", methods=["GET", "OPTIONS"])
def health_check():
    """Health check endpoint for monitoring."""
    # Handle OPTIONS request for CORS
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add("Access-Control-Allow-Methods", "GET,OPTIONS")
        return response

    import psutil

    try:
        # Get basic system metrics
        memory_percent = psutil.virtual_memory().percent
        startup_time = getattr(webapp, "_startup_time", None)
        uptime = time.time() - startup_time if startup_time else 0

        # Check environment configuration
        langchain_stream_disabled = (
            dotenv.get_dotenv_value("LANGCHAIN_ANTHROPIC_STREAM_USAGE", "true").lower()
            == "false"
        )
        enable_dev_features = (
            dotenv.get_dotenv_value("ENABLE_DEV_FEATURES", "true").lower() == "true"
        )
        node_env = dotenv.get_dotenv_value("NODE_ENV", "development")

        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "memory_percent": memory_percent,
            "uptime_seconds": uptime,
            "server": "gunicorn"
            if "gunicorn" in os.environ.get("SERVER_SOFTWARE", "")
            else "development",
            "environment": {
                "node_env": node_env,
                "langchain_stream_disabled": langchain_stream_disabled,
                "dev_features_enabled": enable_dev_features,
                "production_mode": node_env == "production" or not enable_dev_features,
            },
        }
    except Exception as e:
        # Fallback to basic health check if psutil fails
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "error": str(e),
            "environment": {
                "node_env": dotenv.get_dotenv_value("NODE_ENV", "development"),
                "langchain_stream_disabled": dotenv.get_dotenv_value(
                    "LANGCHAIN_ANTHROPIC_STREAM_USAGE", "true"
                ).lower()
                == "false",
            },
        }


# readiness check endpoint for Railway
@webapp.route("/ready", methods=["GET", "OPTIONS"])
def readiness_check():
    """Readiness check endpoint for Railway deployment verification."""
    # Handle OPTIONS request for CORS
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add("Access-Control-Allow-Methods", "GET,OPTIONS")
        return response

    return {"status": "ready", "service": "gary-zero", "timestamp": time.time()}


# Railway health check endpoint
@webapp.route("/healthz", methods=["GET", "OPTIONS"])
def health_check_railway():
    """Railway-specific health check endpoint (GET /healthz)."""
    # Handle OPTIONS request for CORS
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add("Access-Control-Allow-Methods", "GET,OPTIONS")
        return response

    import psutil

    try:
        # Get basic system metrics
        memory_percent = psutil.virtual_memory().percent
        startup_time = getattr(webapp, "_startup_time", None)
        uptime = time.time() - startup_time if startup_time else 0

        # Check environment configuration
        langchain_stream_disabled = (
            dotenv.get_dotenv_value("LANGCHAIN_ANTHROPIC_STREAM_USAGE", "true").lower()
            == "false"
        )
        enable_dev_features = (
            dotenv.get_dotenv_value("ENABLE_DEV_FEATURES", "true").lower() == "true"
        )
        node_env = dotenv.get_dotenv_value("NODE_ENV", "development")

        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "memory_percent": memory_percent,
            "uptime_seconds": uptime,
            "server": "gunicorn"
            if "gunicorn" in os.environ.get("SERVER_SOFTWARE", "")
            else "development",
            "service": "gary-zero",
            "environment": {
                "node_env": node_env,
                "langchain_stream_disabled": langchain_stream_disabled,
                "dev_features_enabled": enable_dev_features,
                "production_mode": node_env == "production" or not enable_dev_features,
                "railway_environment": os.environ.get("RAILWAY_ENVIRONMENT", "local"),
            },
        }
    except Exception as e:
        PrintStyle().error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e), "timestamp": time.time()}, 500


# Directory structure health check endpoint
@webapp.route("/health/directories", methods=["GET", "OPTIONS"])
def health_check_directories():
    """Check the health of persistent volume directory structure."""
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add("Access-Control-Allow-Methods", "GET,OPTIONS")
        return response

    try:
        from framework.helpers.files import get_data_path
        
        # Required directories
        required_dirs = ["settings", "memory", "knowledge", "prompts", "logs", "work_dir", "reports", "scheduler", "tmp"]
        directory_status = {}
        all_healthy = True
        
        base_data_path = get_data_path()
        
        for dir_name in required_dirs:
            dir_path = os.path.join(base_data_path, dir_name)
            exists = os.path.exists(dir_path) and os.path.isdir(dir_path)
            directory_status[dir_name] = {
                "exists": exists,
                "path": dir_path,
                "writable": os.access(dir_path, os.W_OK) if exists else False
            }
            if not exists:
                all_healthy = False
        
        # Check for specific files
        required_files = {
            "settings/config.json": os.path.join(base_data_path, "settings", "config.json"),
            "memory/context.json": os.path.join(base_data_path, "memory", "context.json"),
            "knowledge/index.json": os.path.join(base_data_path, "knowledge", "index.json"),
            "scheduler/tasks.json": os.path.join(base_data_path, "scheduler", "tasks.json"),
        }
        
        file_status = {}
        for file_key, file_path in required_files.items():
            exists = os.path.exists(file_path) and os.path.isfile(file_path)
            file_status[file_key] = {
                "exists": exists,
                "path": file_path,
                "size": os.path.getsize(file_path) if exists else 0
            }
        
        # Check authentication rate limiter stats
        auth_stats = auth_rate_limiter.get_stats()
        
        status_code = 200 if all_healthy else 503
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": time.time(),
            "base_data_path": base_data_path,
            "directories": directory_status,
            "files": file_status,
            "authentication": {
                "rate_limiter_active": True,
                "current_stats": auth_stats
            }
        }, status_code
    except Exception as e:
        # Fallback to basic health check if psutil fails
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "error": str(e),
            "service": "gary-zero",
            "environment": {
                "node_env": dotenv.get_dotenv_value("NODE_ENV", "development"),
                "langchain_stream_disabled": dotenv.get_dotenv_value(
                    "LANGCHAIN_ANTHROPIC_STREAM_USAGE", "true"
                ).lower()
                == "false",
                "railway_environment": os.environ.get("RAILWAY_ENVIRONMENT", "local"),
            },
        }


# Dynamic prompts and agents endpoint
@webapp.route("/api/prompts", methods=["GET", "OPTIONS"])
def api_prompts():
    """Get information about dynamic prompts and agents."""
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add("Access-Control-Allow-Methods", "GET,OPTIONS")
        return response

    try:
        stats = dynamic_prompt_loader.get_stats()
        agents = dynamic_prompt_loader.list_agents()
        
        return {
            "status": "success",
            "timestamp": time.time(),
            "prompt_stats": stats,
            "agents": agents
        }
    except Exception as e:
        PrintStyle().error(f"Prompts API failed: {str(e)}")
        return {"status": "error", "error": str(e), "timestamp": time.time()}, 500


@webapp.route("/api/agents/<agent_id>/prompt", methods=["GET", "OPTIONS"])
def api_agent_prompt(agent_id):
    """Get a specific agent's prompt."""
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add("Access-Control-Allow-Methods", "GET,OPTIONS")
        return response

    try:
        prompt_data = dynamic_prompt_loader.get_agent_prompt(agent_id)
        if prompt_data:
            return {
                "status": "success",
                "agent_id": agent_id,
                "prompt": prompt_data,
                "timestamp": time.time()
            }
        else:
            return {
                "status": "not_found",
                "agent_id": agent_id,
                "message": "Agent prompt not found",
                "timestamp": time.time()
            }, 404
    except Exception as e:
        PrintStyle().error(f"Agent prompt API failed: {str(e)}")
        return {"status": "error", "error": str(e), "timestamp": time.time()}, 500


# API endpoints for compatibility
@webapp.route("/api", methods=["GET", "POST", "OPTIONS"])
@requires_auth
async def api_endpoint():
    """API endpoint that handles both GET and POST requests."""
    # Handle OPTIONS request for CORS
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        return response

    if request.method == "POST":
        PrintStyle().debug(f"API POST request: {request.form or request.get_json()}")

        if request.is_json:
            data = request.get_json()
            message = data.get("message", "")
            return {
                "status": "success",
                "response": f"Received message: {message}",
                "timestamp": time.time(),
            }
        else:
            # Handle form data
            return {
                "status": "success",
                "response": "API form submission received",
                "data": dict(request.form),
                "timestamp": time.time(),
            }
    else:
        # GET request
        return {
            "message": "Gary-Zero Flask API",
            "version": "1.0.0",
            "status": "running",
            "timestamp": time.time(),
            "methods": ["GET", "POST"],
        }


# Error reporting endpoint for frontend error boundary
@webapp.route("/api/error_report", methods=["POST", "OPTIONS"])
@requires_auth
async def error_report():
    """Handle error reports from the frontend error boundary."""
    # Handle OPTIONS request for CORS
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add("Access-Control-Allow-Methods", "POST,OPTIONS")
        return response

    try:
        # Get error data from request
        if request.is_json:
            error_data = request.get_json()
        else:
            error_data = dict(request.form)

        # Log error data for debugging and monitoring
        PrintStyle().error(f"Frontend Error Report: {error_data}")

        # Extract key information for structured logging
        error_type = error_data.get("type", "unknown")
        error_message = error_data.get("message", "No message")
        error_url = error_data.get("url", "unknown")
        timestamp = error_data.get("timestamp", time.time())

        # Enhanced logging with context
        PrintStyle().error(f"Error Type: {error_type}")
        PrintStyle().error(f"Error Message: {error_message}")
        PrintStyle().error(f"Error URL: {error_url}")
        PrintStyle().error(f"Timestamp: {timestamp}")

        # Store or forward to external logging service if needed
        # This could be extended to send to services like Sentry, LogRocket, etc.

        return {
            "status": "success",
            "message": "Error report received and logged",
            "timestamp": time.time(),
            "error_id": f"err_{int(time.time())}",
        }

    except Exception as e:
        PrintStyle().error(f"Failed to process error report: {str(e)}")
        return {
            "status": "error",
            "message": "Failed to process error report",
            "error": str(e),
            "timestamp": time.time(),
        }, 500


# Debug endpoint for route inspection
@webapp.route("/debug/routes", methods=["GET", "OPTIONS"])
@requires_auth
async def debug_routes():
    """Debug endpoint to list all registered Flask routes."""
    # Handle OPTIONS request for CORS
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add("Access-Control-Allow-Methods", "GET,OPTIONS")
        return response

    routes = []
    for rule in webapp.url_map.iter_rules():
        routes.append(
            {
                "endpoint": rule.endpoint,
                "methods": list(rule.methods - {"HEAD", "OPTIONS"}),
                "rule": rule.rule,
            }
        )

    return {"total_routes": len(routes), "routes": routes, "timestamp": time.time()}


# Credential rotation endpoint for Railway production
@webapp.route("/api/rotate_credentials", methods=["POST", "OPTIONS"])
@requires_auth
async def rotate_credentials():
    """Rotate credentials immediately for security."""
    # Handle OPTIONS request for CORS
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add("Access-Control-Allow-Methods", "POST,OPTIONS")
        return response
    
    try:
        if db_auth:
            # Use database-backed credential rotation
            auth_user = request.authorization.username if request.authorization else "admin"
            new_password = db_auth.rotate_credentials(auth_user)
            
            if new_password:
                return {
                    "status": "success",
                    "message": "Credentials rotated successfully",
                    "new_password": new_password,
                    "timestamp": time.time(),
                    "warning": "Please update your AUTH_PASSWORD environment variable with the new password"
                }
            else:
                return {
                    "status": "error", 
                    "message": "Failed to rotate credentials",
                    "timestamp": time.time()
                }, 500
        else:
            return {
                "status": "error",
                "message": "Database authentication not available - cannot rotate credentials",
                "timestamp": time.time()
            }, 503
            
    except Exception as e:
        PrintStyle().error(f"Credential rotation failed: {str(e)}")
        return {
            "status": "error",
            "message": "Credential rotation failed",
            "error": str(e),
            "timestamp": time.time()
        }, 500


# handle favicon requests
@webapp.route("/favicon.ico", methods=["GET", "OPTIONS"])
def serve_favicon():
    """Serve the favicon file."""
    # Handle OPTIONS request for CORS
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add("Access-Control-Allow-Methods", "GET,OPTIONS")
        return response

    try:
        # Try to serve the SVG favicon as ICO (browsers will handle it)
        favicon_path = get_abs_path("./webui/public/favicon.svg")
        if os.path.exists(favicon_path):
            # Read the file directly and serve with proper headers
            with open(favicon_path, "rb") as f:
                content = f.read()

            # Return SVG with proper content type and caching headers
            response = Response(content, mimetype="image/svg+xml")
            response.headers["Cache-Control"] = "public, max-age=3600"
            return response
        else:
            # Return a 204 No Content if favicon doesn't exist
            return Response("", 204)
    except Exception:
        # Return a 204 No Content on any error
        return Response("", 204)


def run():
    """Run the Flask server."""
    PrintStyle().print("Initializing framework...")

    # Initialize dynamic prompt loader
    try:
        dynamic_prompt_loader.start_watching()
        PrintStyle().success("Dynamic prompt loader initialized")
    except Exception as e:
        PrintStyle().error(f"Failed to initialize dynamic prompt loader: {e}")

    # Suppress only request logs but keep the startup messages
    from a2wsgi import ASGIMiddleware
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    from werkzeug.serving import WSGIRequestHandler, make_server

    PrintStyle().print("Starting server...")

    class NoRequestLoggingWSGIRequestHandler(WSGIRequestHandler):
        def log_request(self, code="-", size="-"):
            pass  # Override to suppress request logging

    # Get configuration from environment
    port = runtime.get_web_ui_port()
    host = (
        runtime.get_arg("host") or dotenv.get_dotenv_value("WEB_UI_HOST") or "0.0.0.0"
    )
    server = None

    def register_api_handler(app, handler: type[ApiHandler]):
        """Register an API handler with the Flask app."""
        name = handler.__module__.split(".")[-1]
        instance = handler(app, lock)

        if handler.requires_loopback():

            @requires_loopback
            async def handle_request():
                return await instance.handle_request(request=request)

        elif handler.requires_auth():

            @requires_auth
            async def handle_request():
                return await instance.handle_request(request=request)

        elif handler.requires_api_key():

            @requires_api_key
            async def handle_request():
                return await instance.handle_request(request=request)

        else:
            # Fallback to requires_auth
            @requires_auth
            async def handle_request():
                return await instance.handle_request(request=request)

        app.add_url_rule(
            f"/{name}",
            f"/{name}",
            handle_request,
            methods=["POST", "GET"],
        )

    # initialize and register API handlers
    handlers = load_classes_from_folder("framework/api", "*.py", ApiHandler)
    for handler in handlers:
        register_api_handler(webapp, handler)

    # add the webapp and mcp to the app
    app = DispatcherMiddleware(
        webapp,
        {
            "/mcp": ASGIMiddleware(app=mcp_server.DynamicMcpProxy.get_instance()),  # type: ignore
        },
    )
    PrintStyle().debug("Registered middleware for MCP and MCP token")

    PrintStyle().debug(f"Starting server at {host}:{port}...")

    server = make_server(
        host=host,
        port=port,
        app=app,
        request_handler=NoRequestLoggingWSGIRequestHandler,
        threaded=True,
    )
    process.set_server(server)
    server.log_startup()

    # Start init_a0 in a background thread when server starts
    # threading.Thread(target=init_a0, daemon=True).start()
    init_a0()

    # run the server
    server.serve_forever()


def init_a0():
    """Initialize all application components."""
    # initialize contexts and MCP
    init_chats_task = initialize.initialize_chats()
    init_mcp_task = initialize.initialize_mcp()  # Store the DeferredTask
    # start job loop
    initialize.initialize_job_loop()

    # only wait for init chats, otherwise they would seem to dissapear for a while on restart
    init_chats_task.result_sync()
    init_mcp_task.result_sync()  # Wait for MCP initialization to complete


# run the internal server
if __name__ == "__main__":
    runtime.initialize()
    dotenv.load_dotenv()
    run()
