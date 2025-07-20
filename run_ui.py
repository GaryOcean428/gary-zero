"""This module runs the Flask web UI and initializes the application."""

import os
import socket
import struct
import threading
import time
from functools import wraps

from flask import Flask, Response, request
from flask_basicauth import BasicAuth

import initialize
from framework.helpers import dotenv, files, git, mcp_server, process, runtime
from framework.helpers.api import ApiHandler
from framework.helpers.extract_tools import load_classes_from_folder
from framework.helpers.files import get_abs_path
from framework.helpers.print_style import PrintStyle

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

# Set up basic authentication for UI and API but not MCP
basic_auth = BasicAuth(webapp)

# Add request logging middleware for debugging
@webapp.before_request
def log_request_info():
    """Log request details for debugging."""
    # Only log for settings-related endpoints to avoid spam
    if '/settings' in request.path or request.path in ['/settings_get', '/settings_set']:
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
    if '/settings' in request.path or request.path in ['/settings_get', '/settings_set']:
        PrintStyle().debug(f"Settings response: {response.status_code} {response.status}")
        if response.status_code >= 400:
            PrintStyle().error(f"Settings error response: {response.get_data(as_text=True)[:200]}")
    return response


def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Only add HSTS if using HTTPS
    if request.is_secure:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # CSP configured for Alpine.js and external resources
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdnjs.cloudflare.com cdn.jsdelivr.net; "
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
    """Handle 404 errors with custom page."""
    try:
        return files.read_file("./webui/404.html"), 404
    except Exception:
        return Response("Page not found", 404, mimetype="text/plain")


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


def is_loopback_address(address):
    """Check if the given address is a loopback address."""
    loopback_checker = {
        socket.AF_INET: lambda x: struct.unpack("!I", socket.inet_aton(x))[0] >> (32 - 8) == 127,
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
        user = dotenv.get_dotenv_value("AUTH_LOGIN")
        password = dotenv.get_dotenv_value("AUTH_PASSWORD")
        if user and password:
            auth = request.authorization
            if not auth or not (auth.username == user and auth.password == password):
                return Response(
                    "Could not verify your access level for that URL.\n"
                    "You have to login with proper credentials",
                    401,
                    {"WWW-Authenticate": 'Basic realm="Login Required"'},
                )
        return await f(*args, **kwargs)

    return decorated


@webapp.route("/", methods=["GET"])
@requires_auth
async def serve_index():
    """Serve the main index.html file."""
    gitinfo = None
    try:
        gitinfo = git.get_git_info()
    except Exception:
        gitinfo = {
            "version": "unknown",
            "commit_time": "unknown",
        }
    
    # Get environment-based feature flags for client-side configuration
    enable_dev_features = dotenv.get_dotenv_value("ENABLE_DEV_FEATURES", "true").lower() == "true"
    vscode_integration_enabled = dotenv.get_dotenv_value("VSCODE_INTEGRATION_ENABLED", "true").lower() == "true"
    chat_auto_resize_enabled = dotenv.get_dotenv_value("CHAT_AUTO_RESIZE_ENABLED", "true").lower() == "true"
    
    # Create JavaScript configuration snippet to inject into the page
    js_config = f"""
    <script>
        // Environment-based feature flags
        window.ENABLE_DEV_FEATURES = {str(enable_dev_features).lower()};
        window.VSCODE_INTEGRATION_ENABLED = {str(vscode_integration_enabled).lower()};
        window.CHAT_AUTO_RESIZE_ENABLED = {str(chat_auto_resize_enabled).lower()};
        console.log('🔧 Feature flags loaded:', {{
            ENABLE_DEV_FEATURES: {str(enable_dev_features).lower()},
            VSCODE_INTEGRATION_ENABLED: {str(vscode_integration_enabled).lower()},
            CHAT_AUTO_RESIZE_ENABLED: {str(chat_auto_resize_enabled).lower()}
        }});
    </script>
    """
    
    return files.read_file(
        "./webui/index.html",
        version_no=gitinfo["version"],
        version_time=gitinfo["commit_time"],
        feature_flags_config=js_config,
    )


# handle privacy policy page
@webapp.route("/privacy", methods=["GET"])
def serve_privacy():
    """Serve the privacy policy page."""
    return files.read_file("./webui/privacy.html")


# handle terms of service page
@webapp.route("/terms", methods=["GET"])
def serve_terms():
    """Serve the terms of service page."""
    return files.read_file("./webui/terms.html")


# health check endpoint
@webapp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring."""
    import psutil
    try:
        # Get basic system metrics
        memory_percent = psutil.virtual_memory().percent
        startup_time = getattr(webapp, '_startup_time', None)
        uptime = time.time() - startup_time if startup_time else 0
        
        # Check environment configuration
        langchain_stream_disabled = dotenv.get_dotenv_value("LANGCHAIN_ANTHROPIC_STREAM_USAGE", "true").lower() == "false"
        enable_dev_features = dotenv.get_dotenv_value("ENABLE_DEV_FEATURES", "true").lower() == "true"
        node_env = dotenv.get_dotenv_value("NODE_ENV", "development")
        
        return {
            "status": "healthy", 
            "timestamp": time.time(), 
            "version": "1.0.0",
            "memory_percent": memory_percent,
            "uptime_seconds": uptime,
            "server": "gunicorn" if "gunicorn" in os.environ.get("SERVER_SOFTWARE", "") else "development",
            "environment": {
                "node_env": node_env,
                "langchain_stream_disabled": langchain_stream_disabled,
                "dev_features_enabled": enable_dev_features,
                "production_mode": node_env == "production" or not enable_dev_features
            }
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
                "langchain_stream_disabled": dotenv.get_dotenv_value("LANGCHAIN_ANTHROPIC_STREAM_USAGE", "true").lower() == "false"
            }
        }


# readiness check endpoint for Railway
@webapp.route("/ready", methods=["GET"])
def readiness_check():
    """Readiness check endpoint for Railway deployment verification."""
    return {"status": "ready", "service": "gary-zero", "timestamp": time.time()}


# handle favicon requests
@webapp.route("/favicon.ico", methods=["GET"])
def serve_favicon():
    """Serve the favicon file."""
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
    host = runtime.get_arg("host") or dotenv.get_dotenv_value("WEB_UI_HOST") or "localhost"
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
