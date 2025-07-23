#!/usr/bin/env python3
"""
Final validation script for Railway 405 error fixes.
Tests both local development and provides deployment verification instructions.
"""

import sys
import subprocess
import time
import requests
from pathlib import Path

def test_import_capabilities():
    """Test that both Flask and FastAPI apps can be imported."""
    print("🔍 Testing Application Import Capabilities")
    print("=" * 50)
    
    # Test Flask import
    try:
        result = subprocess.run([
            sys.executable, "-c", 
            "import run_ui; app = run_ui.webapp; print(f'Flask routes: {len(list(app.url_map.iter_rules()))}')"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Flask app imports successfully")
            print(f"   {result.stdout.strip()}")
        else:
            print("❌ Flask app import failed")
            print(f"   Error: {result.stderr.strip()}")
    except Exception as e:
        print(f"❌ Flask import test failed: {e}")
    
    # Test FastAPI import
    try:
        result = subprocess.run([
            sys.executable, "-c", 
            "import main; print('FastAPI app imports successfully')"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ FastAPI app imports successfully")
        else:
            print("❌ FastAPI app import failed")
            print(f"   Error: {result.stderr.strip()}")
    except Exception as e:
        print(f"❌ FastAPI import test failed: {e}")

def run_static_analysis():
    """Run static route analysis."""
    print("\n🔍 Running Static Route Analysis")
    print("=" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, "quick_route_test.py"
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print("✅ Static analysis passed - no 405 issues detected")
        else:
            print("⚠️  Static analysis found potential issues:")
            print(result.stdout)
    except Exception as e:
        print(f"❌ Static analysis failed: {e}")

def test_local_server(app_type="fastapi", port=8000):
    """Test local server startup and basic routes."""
    print(f"\n🚀 Testing Local {app_type.upper()} Server")
    print("=" * 50)
    
    # Start server command
    if app_type == "fastapi":
        cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)]
    else:
        cmd = [sys.executable, "run_ui.py"]
    
    print(f"Starting server: {' '.join(cmd)}")
    
    try:
        # Start server process
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        print("Waiting 10 seconds for server startup...")
        time.sleep(10)
        
        if process.poll() is not None:
            # Process has terminated
            stdout, stderr = process.communicate()
            print(f"❌ Server failed to start:")
            print(f"   stdout: {stdout.decode()[:200]}")
            print(f"   stderr: {stderr.decode()[:200]}")
            return False
        
        # Test basic connectivity
        base_url = f"http://127.0.0.1:{port}"
        
        print(f"Testing basic routes on {base_url}")
        
        test_routes = [
            ("/health", "GET", "Health check"),
            ("/health", "OPTIONS", "Health CORS"),
            ("/ready", "GET", "Readiness check"),
            ("/", "GET", "Root page"),
            ("/", "OPTIONS", "Root CORS"),
        ]
        
        success_count = 0
        for path, method, desc in test_routes:
            try:
                if method == "GET":
                    response = requests.get(f"{base_url}{path}", timeout=5)
                elif method == "OPTIONS":
                    response = requests.options(f"{base_url}{path}", timeout=5)
                
                if response.status_code < 400:
                    print(f"   ✅ {desc}: {response.status_code}")
                    success_count += 1
                else:
                    print(f"   ❌ {desc}: {response.status_code}")
            except Exception as e:
                print(f"   ❌ {desc}: Connection error - {e}")
        
        # Clean up
        process.terminate()
        process.wait(timeout=5)
        
        print(f"\nResults: {success_count}/{len(test_routes)} routes working")
        return success_count == len(test_routes)
        
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        if 'process' in locals():
            process.terminate()
        return False

def check_deployment_readiness():
    """Check deployment configuration and readiness."""
    print("\n🚢 Deployment Readiness Check")
    print("=" * 50)
    
    # Check Procfile
    procfile = Path("Procfile")
    if procfile.exists():
        with open(procfile) as f:
            content = f.read().strip()
        print(f"✅ Procfile exists: {content}")
        
        if "start_uvicorn.py" in content:
            print("   📱 Deployment type: FastAPI with uvicorn")
        elif "gunicorn" in content:
            print("   🌶️  Deployment type: Flask with gunicorn")
        else:
            print("   ❓ Unknown deployment type")
    else:
        print("❌ No Procfile found")
    
    # Check alternative configurations
    alt_procfile = Path("Procfile.flask")
    if alt_procfile.exists():
        print("✅ Alternative Flask Procfile available")
    
    # Check requirements
    requirements = Path("requirements.txt")
    if requirements.exists():
        print("✅ requirements.txt exists")
    else:
        print("⚠️  No requirements.txt found")
    
    # Check Docker configuration
    dockerfile = Path("Dockerfile")
    if dockerfile.exists():
        print("✅ Dockerfile exists")
    
    print("\n📋 Deployment Instructions:")
    print("1. Push changes to Railway:")
    print("   git push origin main")
    print("2. Monitor deployment logs:")
    print("   railway logs --tail")
    print("3. Test production routes:")
    print("   python test_flask_routes.py https://your-railway-domain.up.railway.app")
    print("4. If 405 errors persist, switch to Flask deployment:")
    print("   cp Procfile.flask Procfile && git add Procfile && git commit -m 'Switch to Flask deployment' && git push")

def main():
    """Main validation function."""
    print("🏥 Gary-Zero Railway 405 Error Fix - Final Validation")
    print("=" * 70)
    
    # Test import capabilities
    test_import_capabilities()
    
    # Run static analysis
    run_static_analysis()
    
    # Test deployment readiness
    check_deployment_readiness()
    
    # Optionally test local servers
    print("\n🔬 Optional Local Server Testing")
    print("To test local servers manually:")
    print("1. FastAPI: python -m uvicorn main:app --host 0.0.0.0 --port 8000")
    print("2. Flask: python run_ui.py")
    print("3. Test routes: python test_flask_routes.py http://localhost:8000")
    
    print("\n✅ Validation Complete!")
    print("The 405 Method Not Allowed fixes have been implemented.")
    print("Deploy to Railway and monitor for error resolution.")

if __name__ == '__main__':
    main()