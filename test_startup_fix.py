#!/usr/bin/env python3
"""
Test script to validate the startup fix for the restart loop issue.

This script tests:
1. Configuration loading and validation
2. Main application imports
3. Uvicorn startup process
4. Health endpoint accessibility
"""

import os
import subprocess
import sys
import time
from pathlib import Path

def test_imports():
    """Test that all critical modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        import main
        print("✅ main.py imports successfully")
    except ImportError as e:
        print(f"❌ main.py import failed: {e}")
        return False
    
    try:
        from framework.helpers.config_loader import get_config_loader
        print("✅ config_loader imports successfully")
    except ImportError as e:
        print(f"❌ config_loader import failed: {e}")
        return False
    
    try:
        import uvicorn
        print("✅ uvicorn is available")
    except ImportError as e:
        print(f"❌ uvicorn import failed: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration loading and validation."""
    print("\n🧪 Testing configuration...")
    
    # Set required environment variables
    os.environ['PORT'] = '8003'
    os.environ['WEB_UI_HOST'] = '0.0.0.0'
    
    try:
        from framework.helpers.config_loader import get_config_loader
        config = get_config_loader()
        
        # Test configuration validation
        validation = config.validate_railway_config()
        if validation["valid"]:
            print("✅ Configuration validation passed")
        else:
            print(f"❌ Configuration validation failed: {validation['issues']}")
            return False
        
        # Test specific methods
        port = config.get_port()
        host = config.get_host()
        print(f"✅ Port: {port}, Host: {host}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_startup_script():
    """Test that the startup script exists and has correct syntax."""
    print("\n🧪 Testing startup script...")
    
    script_path = Path("scripts/start.sh")
    if not script_path.exists():
        print("❌ scripts/start.sh does not exist")
        return False
    
    if not script_path.is_file():
        print("❌ scripts/start.sh is not a file")
        return False
    
    # Check if executable
    if not os.access(script_path, os.X_OK):
        print("❌ scripts/start.sh is not executable")
        return False
    
    # Test bash syntax
    result = subprocess.run(['bash', '-n', str(script_path)], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Bash syntax error in start.sh: {result.stderr}")
        return False
    
    print("✅ scripts/start.sh exists, is executable, and has valid syntax")
    return True

def test_uvicorn_startup():
    """Test that uvicorn can start the application."""
    print("\n🧪 Testing uvicorn startup (10-second test)...")
    
    # Set environment variables
    os.environ['PORT'] = '8004'
    os.environ['WEB_UI_HOST'] = '0.0.0.0'
    
    try:
        # Start uvicorn process
        process = subprocess.Popen([
            'python', 'start_uvicorn.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for startup (max 10 seconds)
        for i in range(10):
            time.sleep(1)
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                print(f"❌ Process exited early: {stderr}")
                return False
        
        # If we get here, process is still running
        print("✅ Uvicorn started successfully and stayed running")
        
        # Clean shutdown
        process.terminate()
        process.wait(timeout=5)
        return True
        
    except Exception as e:
        print(f"❌ Uvicorn startup test failed: {e}")
        return False

def test_health_endpoint():
    """Test that the health endpoint is accessible during startup."""
    print("\n🧪 Testing health endpoint...")
    
    # Set environment variables
    os.environ['PORT'] = '8005'
    os.environ['WEB_UI_HOST'] = '0.0.0.0'
    
    try:
        # Start uvicorn process
        process = subprocess.Popen([
            'python', 'start_uvicorn.py'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for startup
        time.sleep(8)
        
        # Test health endpoint
        result = subprocess.run([
            'curl', '-f', '-s', 'http://localhost:8005/health'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Health endpoint is accessible and returns 200 OK")
            print(f"   Response: {result.stdout[:100]}...")
            success = True
        else:
            print(f"❌ Health endpoint failed: {result.stderr}")
            success = False
        
        # Clean shutdown
        process.terminate()
        process.wait(timeout=5)
        return success
        
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        try:
            process.terminate()
        except:
            pass
        return False

def main():
    """Run all tests."""
    print("🚀 Gary-Zero Startup Fix Validation")
    print("=" * 40)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Startup Script", test_startup_script),
        ("Uvicorn Startup", test_uvicorn_startup),
        ("Health Endpoint", test_health_endpoint)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} test PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} test FAILED with exception: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Startup fix is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())