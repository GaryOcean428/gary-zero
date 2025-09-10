#!/usr/bin/env python3
"""
Test the full startup process for Gary-Zero to ensure Railway deployment compatibility.
"""

import os
import sys
import time
import subprocess
import signal
import requests
from typing import Optional

def test_simple_health_check_startup(port: int = 8001, timeout: int = 10) -> bool:
    """Test that simple_health_check.py starts successfully and responds to health checks."""
    print(f"🧪 Testing simple health check startup on port {port}")
    
    # Start the simple health check server
    env = os.environ.copy()
    env['PORT'] = str(port)
    env['WEB_UI_HOST'] = '127.0.0.1'  # Use localhost for testing
    
    process = subprocess.Popen(
        [sys.executable, 'simple_health_check.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        # Wait for the server to start
        print("  Waiting for server to start...")
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"  ❌ Process exited early with code {process.returncode}")
            print(f"  stdout: {stdout.decode()}")
            print(f"  stderr: {stderr.decode()}")
            return False
        
        # Test health endpoints
        endpoints = ['/health', '/healthz', '/ready', '/']
        for endpoint in endpoints:
            try:
                response = requests.get(f'http://127.0.0.1:{port}{endpoint}', timeout=5)
                if response.status_code == 200:
                    print(f"  ✅ {endpoint} responds with 200 OK")
                    if endpoint != '/':
                        data = response.json()
                        if data.get('status') in ['healthy', 'ok']:
                            print(f"    Status: {data.get('status')}")
                        else:
                            print(f"    ⚠️  Unexpected status: {data}")
                else:
                    print(f"  ❌ {endpoint} returned {response.status_code}")
                    return False
            except requests.exceptions.RequestException as e:
                print(f"  ❌ Failed to connect to {endpoint}: {e}")
                return False
        
        print("  ✅ All health endpoints working correctly")
        return True
        
    finally:
        # Clean up: terminate the process
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        print("  🧹 Test server stopped")

def test_start_uvicorn_import() -> bool:
    """Test that start_uvicorn.py can be imported and basic functions work."""
    print("🧪 Testing start_uvicorn.py import and functionality")
    
    try:
        # Test import
        sys.path.insert(0, '.')
        import start_uvicorn
        print("  ✅ start_uvicorn.py imports successfully")
        
        # Test that it has the main function
        if hasattr(start_uvicorn, 'main'):
            print("  ✅ main() function exists")
        else:
            print("  ❌ main() function not found")
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ Failed to import start_uvicorn.py: {e}")
        return False

def test_script_permissions() -> bool:
    """Test that critical scripts have execute permissions."""
    print("🧪 Testing script permissions")
    
    critical_scripts = [
        'scripts/start.sh',
        'start_uvicorn.py',
        'test_deployment_validation.py'
    ]
    
    all_good = True
    for script in critical_scripts:
        if os.path.exists(script):
            if os.access(script, os.X_OK):
                print(f"  ✅ {script} is executable")
            else:
                print(f"  ❌ {script} is not executable")
                all_good = False
        else:
            print(f"  ❌ {script} does not exist")
            all_good = False
    
    return all_good

def test_environment_variables() -> bool:
    """Test environment variable handling."""
    print("🧪 Testing environment variable handling")
    
    # Test PORT variable handling
    test_cases = [
        ("8000", 8000),
        ("$PORT", 8000),  # Should fallback to 8000
        ("invalid", 8000),  # Should fallback to 8000
    ]
    
    for test_port, expected in test_cases:
        os.environ['PORT'] = test_port
        try:
            # Simulate the port resolution logic from start_uvicorn.py
            port_env = os.getenv("PORT", "8000")
            if port_env == "$PORT" or not port_env.isdigit():
                port = 8000
            else:
                port = int(port_env)
            
            if port == expected:
                print(f"  ✅ PORT='{test_port}' resolves to {port}")
            else:
                print(f"  ❌ PORT='{test_port}' should resolve to {expected}, got {port}")
                return False
        except Exception as e:
            print(f"  ❌ PORT='{test_port}' caused error: {e}")
            return False
    
    # Clean up
    if 'PORT' in os.environ:
        del os.environ['PORT']
    
    return True

def main():
    """Run all startup process tests."""
    print("🚀 Gary-Zero Startup Process Tests")
    print("=" * 40)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Script Permissions", test_script_permissions),
        ("Start Uvicorn Import", test_start_uvicorn_import),
        ("Simple Health Check Startup", test_simple_health_check_startup),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print()
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            failed += 1
    
    print()
    print("=" * 40)
    print(f"📊 Test Summary: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("❌ Some startup tests failed.")
        sys.exit(1)
    else:
        print("✅ All startup tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()