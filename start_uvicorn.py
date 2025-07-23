#!/usr/bin/env python3
"""
Startup script for uvicorn with proper PORT environment variable resolution.
This script ensures the PORT variable is properly resolved as an integer for Railway deployment.
"""

import os
import sys


def main():
    """Start uvicorn with properly resolved PORT environment variable."""
    print("🚀 Gary-Zero Railway Deployment Starting...")
    
    # Import configuration helper
    from framework.helpers.config_loader import get_config_loader
    
    # Get configuration with validation
    print("🔍 Loading and validating configuration...")
    config_loader = get_config_loader()
    config_loader.log_startup_config()
    
    # Validate configuration
    validation = config_loader.validate_railway_config()
    if not validation["valid"]:
        print("❌ Configuration validation failed:")
        for issue in validation["issues"]:
            print(f"   - {issue}")
        print("Continuing with fallback configuration...")
    
    # Quick template validation
    try:
        print("🎨 Validating template rendering...")
        from framework.helpers.template_helper import render_index_html
        rendered = render_index_html()
        
        # Quick check for common placeholders
        if "{{" in rendered and "}}" in rendered:
            print("⚠️  Template placeholders may not be fully resolved")
        else:
            print("✅ Template rendering looks good")
    except Exception as e:
        print(f"⚠️  Template validation warning: {e}")
    
    # Get validated port and host
    port = config_loader.get_port()
    host = config_loader.get_host()
    
    # Get PORT from environment with Railway-compatible fallback
    port_env = os.getenv("PORT", "8000")

    # Handle case where PORT is literal '$PORT' string (not resolved)
    if port_env == "$PORT" or not port_env.isdigit():
        port = 8000
        print(f"⚠️  PORT environment variable not properly resolved (got '{port_env}'), using fallback: {port}")
    else:
        port = int(port_env)

    host = os.getenv("WEB_UI_HOST", "0.0.0.0")

    # Build uvicorn command with resolved port number
    # Use asyncio instead of uvloop for broader compatibility
    cmd = [
        "uvicorn",
        "main:app",
        "--host", host,
        "--port", str(port),
        "--workers", "4",
        "--loop", "asyncio"
    ]

    print(f"🚀 Starting uvicorn on {host}:{port}")
    print(f"🔧 Command: {' '.join(cmd)}")

    # Execute uvicorn with resolved arguments
    try:
        os.execvp("uvicorn", cmd)
    except FileNotFoundError:
        print("Error: uvicorn not found. Make sure it's installed.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error starting uvicorn: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
