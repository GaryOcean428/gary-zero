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

# initialize the internal Flask server
webapp = Flask("app", static_folder=get_abs_path("./webui"), static_url_path="/")
webapp.config["JSON_SORT_KEYS"] = False  # Disable key sorting in jsonify

lock = threading.Lock()

# Set up basic authentication for UI and API but not MCP
basic_auth = BasicAuth(webapp)


def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    # Only add HSTS if using HTTPS
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    # Basic CSP - can be made more restrictive based on needs
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; font-src 'self' cdnjs.cloudflare.com; connect-src 'self'"
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


# handle default address, load index
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
    return files.read_file(
        "./webui/index.html",
        version_no=gitinfo["version"],
        version_time=gitinfo["commit_time"],
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
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }


# handle favicon requests
@webapp.route("/favicon.ico", methods=["GET"])
def serve_favicon():
    """Serve the favicon file."""
    try:
        # Try to serve the SVG favicon as ICO (browsers will handle it)
        favicon_path = get_abs_path("./webui/public/favicon.svg")
        if os.path.exists(favicon_path):
            # Read the file directly and serve with proper headers
            with open(favicon_path, 'rb') as f:
                content = f.read()
            
            # Return SVG with proper content type and caching headers
            response = Response(content, mimetype='image/svg+xml')
            response.headers['Cache-Control'] = 'public, max-age=3600'
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
