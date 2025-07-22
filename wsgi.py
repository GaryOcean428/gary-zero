"""WSGI entry point for production deployment with Gunicorn."""

import atexit
import os
import signal
import sys
import time

from framework.helpers import dotenv, runtime
from framework.helpers.print_style import PrintStyle

# Add the application directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Graceful shutdown handling
def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    PrintStyle().print(f"🛑 Received signal {sig}, shutting down gracefully...")

    # Perform cleanup here if needed
    # For example, close database connections, save state, etc.

    PrintStyle().print("✅ Graceful shutdown completed")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)  # Railway sends SIGTERM
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C

def cleanup_on_exit():
    """Cleanup function called on normal exit."""
    PrintStyle().print("🧹 Performing cleanup on exit...")

# Register cleanup function
atexit.register(cleanup_on_exit)

def create_app():
    """Create and configure the WSGI application for production deployment."""
    start_time = time.time()
    PrintStyle().print("🚀 Starting production application...")

    try:
        # Initialize runtime and environment first
        runtime.initialize()
        dotenv.load_dotenv()

        # Import after initialization to avoid circular imports
        from a2wsgi import ASGIMiddleware
        from flask import request
        from werkzeug.middleware.dispatcher import DispatcherMiddleware

        from framework.helpers import mcp_server
        from framework.helpers.api import ApiHandler
        from framework.helpers.extract_tools import load_classes_from_folder
        from run_ui import init_a0, lock, requires_api_key, requires_auth, requires_loopback, webapp

        PrintStyle().print("📦 Registering API handlers...")

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

        # Initialize and register API handlers
        try:
            handlers = load_classes_from_folder("framework/api", "*.py", ApiHandler)
            for handler in handlers:
                register_api_handler(webapp, handler)
            PrintStyle().debug(f"✅ Registered {len(handlers)} API handlers")
        except Exception as e:
            PrintStyle().warning(f"Failed to load some API handlers: {e}")

        # Create the dispatcher middleware with MCP support
        try:
            app = DispatcherMiddleware(
                webapp,
                {
                    "/mcp": ASGIMiddleware(app=mcp_server.DynamicMcpProxy.get_instance()),
                },
            )
            PrintStyle().debug("✅ Registered middleware for MCP")
        except Exception as e:
            PrintStyle().warning(f"MCP middleware failed, using webapp only: {e}")
            app = webapp

        # Initialize application components
        PrintStyle().print("🔧 Initializing application components...")
        try:
            init_a0()
            PrintStyle().print("✅ Application components initialized")
        except Exception as e:
            PrintStyle().error(f"Component initialization failed: {e}")
            # Continue anyway - health check should still work

        startup_time = time.time() - start_time
        PrintStyle().print(f"🎉 Production application ready in {startup_time:.2f}s")

        # Add startup metrics to the app
        app._startup_time = start_time
        app._startup_duration = startup_time

        return app

    except Exception as e:
        error_message = str(e)  # Capture error message for use in nested function
        PrintStyle().error(f"❌ Application startup failed: {e}")
        # Return a minimal app with health check for debugging
        from flask import Flask, jsonify

        emergency_app = Flask(__name__)

        @emergency_app.route('/health', methods=['GET'])
        def emergency_health():
            return jsonify({
                "status": "error",
                "error": error_message,
                "timestamp": time.time(),
                "startup_failed": True
            })

        @emergency_app.route('/ready', methods=['GET'])
        def emergency_ready():
            return jsonify({
                "status": "error",
                "error": error_message,
                "timestamp": time.time(),
                "startup_failed": True
            })

        PrintStyle().print("⚠️  Emergency mode: basic health check only")
        return emergency_app

# Create the application instance for Gunicorn
application = create_app()

# Alias for different WSGI server conventions
app = application
