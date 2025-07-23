#!/usr/bin/env python3
"""
Diagnostic script to determine which application (Flask vs FastAPI) is causing 405 errors.
"""

import os
import sys
import importlib.util
from pathlib import Path

def analyze_deployment_config():
    """Analyze the current deployment configuration."""
    print("🔍 Railway Deployment Configuration Analysis")
    print("=" * 60)
    
    # Check Procfile
    procfile_path = Path("Procfile")
    if procfile_path.exists():
        with open(procfile_path) as f:
            procfile_content = f.read().strip()
        print(f"📝 Procfile command: {procfile_content}")
        
        if "uvicorn" in procfile_content and "main:app" in procfile_content:
            print("🚀 Deployment type: FastAPI with uvicorn")
            app_type = "fastapi"
            app_module = "main"
        elif "gunicorn" in procfile_content and "wsgi" in procfile_content:
            print("🌶️  Deployment type: Flask with gunicorn")
            app_type = "flask"
            app_module = "wsgi"
        else:
            print(f"❓ Unknown deployment type: {procfile_content}")
            app_type = "unknown"
            app_module = None
    else:
        print("❌ No Procfile found")
        app_type = "none"
        app_module = None
    
    return app_type, app_module

def check_fastapi_routes():
    """Check FastAPI routes in main.py."""
    print(f"\n🔍 Analyzing FastAPI routes (main.py)...")
    
    try:
        # Read main.py to analyze routes
        with open("main.py") as f:
            content = f.read()
        
        # Count route definitions
        get_routes = content.count("@app.get(")
        post_routes = content.count("@app.post(")
        options_routes = content.count("@app.options(")
        websocket_routes = content.count("@app.websocket(")
        error_handlers = content.count("@app.exception_handler(")
        
        print(f"  GET routes: {get_routes}")
        print(f"  POST routes: {post_routes}")
        print(f"  OPTIONS routes: {options_routes}")
        print(f"  WebSocket routes: {websocket_routes}")
        print(f"  Error handlers: {error_handlers}")
        
        # Check for specific endpoints
        critical_endpoints = [
            ('/', 'root endpoint'),
            ('/health', 'health check'),
            ('/ready', 'readiness check'),
            ('/api', 'API endpoint'),
        ]
        
        print(f"\n  Critical endpoint coverage:")
        for endpoint, desc in critical_endpoints:
            has_get = f'@app.get("{endpoint}")' in content
            has_post = f'@app.post("{endpoint}")' in content
            has_options = f'@app.options("{endpoint}")' in content
            
            methods = []
            if has_get: methods.append("GET")
            if has_post: methods.append("POST") 
            if has_options: methods.append("OPTIONS")
            
            status = "✅" if methods else "❌"
            print(f"    {endpoint} ({desc}): {status} {', '.join(methods)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing FastAPI: {e}")
        return False

def check_flask_routes():
    """Check Flask routes in run_ui.py."""
    print(f"\n🔍 Analyzing Flask routes (run_ui.py)...")
    
    try:
        # Read run_ui.py to analyze routes
        with open("run_ui.py") as f:
            content = f.read()
        
        # Count route definitions  
        route_count = content.count("@webapp.route(")
        error_handlers = content.count("@webapp.errorhandler(")
        
        print(f"  Total routes: {route_count}")
        print(f"  Error handlers: {error_handlers}")
        
        # Check for specific endpoints
        critical_endpoints = [
            ('/', 'root endpoint'),
            ('/health', 'health check'),
            ('/ready', 'readiness check'),
            ('/api', 'API endpoint'),
        ]
        
        print(f"\n  Critical endpoint coverage:")
        for endpoint, desc in critical_endpoints:
            route_pattern = f'@webapp.route("{endpoint}"'
            has_route = route_pattern in content
            
            if has_route:
                # Extract methods from the route definition
                import re
                pattern = rf'@webapp\.route\("{re.escape(endpoint)}"[^)]*methods=\[([^\]]+)\]'
                matches = re.search(pattern, content)
                if matches:
                    methods_str = matches.group(1)
                    methods = [m.strip().strip('"\'') for m in methods_str.split(',')]
                else:
                    methods = ['GET']  # Default Flask method
                
                status = "✅"
                method_info = ', '.join(methods)
            else:
                status = "❌"
                method_info = "Not found"
            
            print(f"    {endpoint} ({desc}): {status} {method_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing Flask: {e}")
        return False

def check_cors_handling():
    """Check CORS handling in both applications."""
    print(f"\n🌐 CORS Configuration Analysis...")
    
    # Check FastAPI CORS
    try:
        with open("main.py") as f:
            fastapi_content = f.read()
        
        has_cors_middleware = "CORSMiddleware" in fastapi_content
        has_cors_headers = "Access-Control-Allow" in fastapi_content
        has_options_handling = "@app.options(" in fastapi_content
        
        print(f"  FastAPI CORS:")
        print(f"    CORSMiddleware: {'✅' if has_cors_middleware else '❌'}")
        print(f"    CORS headers: {'✅' if has_cors_headers else '❌'}")
        print(f"    OPTIONS handling: {'✅' if has_options_handling else '❌'}")
        
    except Exception as e:
        print(f"    FastAPI CORS check failed: {e}")
    
    # Check Flask CORS
    try:
        with open("run_ui.py") as f:
            flask_content = f.read()
        
        has_preflight_handler = "handle_preflight" in flask_content
        has_cors_headers = "Access-Control-Allow" in flask_content
        has_options_methods = 'methods=["GET", "POST", "OPTIONS"]' in flask_content or 'methods=["GET", "OPTIONS"]' in flask_content
        
        print(f"  Flask CORS:")
        print(f"    Preflight handler: {'✅' if has_preflight_handler else '❌'}")
        print(f"    CORS headers: {'✅' if has_cors_headers else '❌'}")
        print(f"    OPTIONS in routes: {'✅' if has_options_methods else '❌'}")
        
    except Exception as e:
        print(f"    Flask CORS check failed: {e}")

def recommend_fixes():
    """Provide recommendations based on analysis."""
    print(f"\n💡 Recommendations:")
    
    app_type, app_module = analyze_deployment_config()
    
    if app_type == "fastapi":
        print(f"  Current deployment: FastAPI")
        print(f"  ✅ FastAPI should handle methods and CORS properly")
        print(f"  🔍 If 405 errors persist, check:")
        print(f"     - Form actions in HTML templates")
        print(f"     - JavaScript fetch() requests")
        print(f"     - Request Content-Type headers")
        print(f"     - Authentication requirements")
        
    elif app_type == "flask":
        print(f"  Current deployment: Flask")
        print(f"  ✅ Flask routes have been enhanced with OPTIONS support")
        print(f"  🔍 If 405 errors persist, check:")
        print(f"     - Authentication decorators (@requires_auth)")
        print(f"     - Form submission handling")
        print(f"     - CORS preflight timing")
        
    else:
        print(f"  ❓ Unknown deployment configuration")
        print(f"  🔧 Consider:")
        print(f"     - Using Procfile.flask for Flask deployment")
        print(f"     - Keeping current FastAPI configuration")
        print(f"     - Testing both locally before deployment")
    
    print(f"\n🧪 Testing commands:")
    print(f"  FastAPI: python -m uvicorn main:app --host 0.0.0.0 --port 8000")
    print(f"  Flask: python run_ui.py")
    print(f"  Test routes: python test_flask_routes.py http://localhost:8000")

def main():
    """Main diagnostic function."""
    print("🏥 Gary-Zero Railway 405 Error Diagnostic")
    print("=" * 60)
    
    app_type, app_module = analyze_deployment_config()
    
    # Analyze both applications
    fastapi_ok = check_fastapi_routes()
    flask_ok = check_flask_routes()
    
    # Check CORS
    check_cors_handling()
    
    # Provide recommendations
    recommend_fixes()
    
    print(f"\n📋 Summary:")
    print(f"  Deployment type: {app_type}")
    print(f"  FastAPI analysis: {'✅' if fastapi_ok else '❌'}")
    print(f"  Flask analysis: {'✅' if flask_ok else '❌'}")
    
    if app_type == "fastapi" and fastapi_ok:
        print(f"  🎯 Focus: Test FastAPI deployment and form submissions")
    elif app_type == "flask" and flask_ok:
        print(f"  🎯 Focus: Test Flask deployment and authentication")
    else:
        print(f"  🎯 Focus: Fix deployment configuration first")

if __name__ == '__main__':
    main()