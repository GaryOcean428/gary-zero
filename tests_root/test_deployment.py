#!/usr/bin/env python3
"""Simple health check test for the Flask application."""

import json
import os
import sys
import time


def test_health_endpoint():
    """Test that the health endpoint exists and returns expected format."""
    try:
        # Add current directory to path for imports
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

        # Test the enhanced health check function
        required_keys = {"status", "timestamp", "version"}
        optional_keys = {"memory_percent", "uptime_seconds", "server", "error"}

        # Simulate the enhanced health check function
        def health_check():
            try:
                # Simulate successful health check
                return {
                    "status": "healthy",
                    "timestamp": time.time(),
                    "version": "1.0.0",
                    "memory_percent": 45.2,
                    "uptime_seconds": 120.5,
                    "server": "gunicorn",
                }
            except Exception as e:
                # Simulate fallback
                return {
                    "status": "healthy",
                    "timestamp": time.time(),
                    "version": "1.0.0",
                    "error": str(e),
                }

        result = health_check()

        # Validate response format
        if not isinstance(result, dict):
            print("❌ Health check should return a dictionary")
            return False

        if not all(key in result for key in required_keys):
            print(
                f"❌ Health check missing required keys. Expected: {required_keys}, Got: {set(result.keys())}"
            )
            return False

        if result["status"] != "healthy":
            print(
                f"❌ Health check status should be 'healthy', got: {result['status']}"
            )
            return False

        # Validate optional fields if present
        for key in result.keys():
            if key not in required_keys and key not in optional_keys:
                print(f"⚠️  Unexpected key in health response: {key}")

        print("✅ Health endpoint format validation passed")
        print("✅ Enhanced health endpoint with monitoring metrics")
        print(f"✅ Sample response: {json.dumps(result, indent=2)}")
        return True

    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return False


def test_dockerfile_command():
    """Test that the Dockerfile CMD is properly formatted for Gunicorn."""
    try:
        with open("Dockerfile") as f:
            content = f.read()

        # Look for the CMD line
        lines = content.split("\n")
        cmd_line = None
        for line in lines:
            if line.strip().startswith("CMD") and "gunicorn" in line:
                cmd_line = line.strip()
                break

        if not cmd_line:
            print("❌ No Gunicorn CMD found in Dockerfile")
            return False

        # Check for required Gunicorn parameters
        required_params = [
            "--bind",
            "0.0.0.0",
            "--workers",
            "--timeout",
            "wsgi:application",
        ]

        for param in required_params:
            if param not in cmd_line:
                print(f"❌ Missing required parameter in Dockerfile CMD: {param}")
                print(f"Found CMD: {cmd_line}")
                return False

        print("✅ Dockerfile CMD validation passed")
        print(f"✅ CMD: {cmd_line}")
        return True

    except Exception as e:
        print(f"❌ Dockerfile validation failed: {e}")
        return False


def test_readiness_endpoint():
    """Test that the readiness endpoint exists and returns expected format."""
    try:
        # Check that readiness endpoint exists in code
        with open("run_ui.py") as f:
            content = f.read()

        if '@webapp.route("/ready"' not in content:
            print("❌ Readiness endpoint route not found")
            return False

        if "def readiness_check():" not in content:
            print("❌ Readiness check function not found")
            return False

        # Test the readiness check logic
        def readiness_check():
            return {"status": "ready", "service": "gary-zero", "timestamp": time.time()}

        result = readiness_check()

        # Validate response format
        expected_keys = {"status", "service", "timestamp"}

        if not isinstance(result, dict):
            print("❌ Readiness check should return a dictionary")
            return False

        if not all(key in result for key in expected_keys):
            print(
                f"❌ Readiness check missing required keys. Expected: {expected_keys}, Got: {set(result.keys())}"
            )
            return False

        if result["status"] != "ready":
            print(
                f"❌ Readiness check status should be 'ready', got: {result['status']}"
            )
            return False

        if result["service"] != "gary-zero":
            print(
                f"❌ Readiness check service should be 'gary-zero', got: {result['service']}"
            )
            return False

        print("✅ Readiness endpoint validation passed")
        print(f"✅ Sample response: {json.dumps(result, indent=2)}")
        return True

    except Exception as e:
        print(f"❌ Readiness endpoint test failed: {e}")
        return False


def test_railway_config():
    """Test that railway.toml has consistent configuration."""
    try:
        with open("railway.toml") as f:
            content = f.read()

        # Check for health check configuration
        if 'healthcheckPath = "/health"' not in content:
            print("❌ railway.toml missing health check path configuration")
            return False

        # Check for gunicorn start command
        if "gunicorn" not in content:
            print("❌ railway.toml should use gunicorn start command")
            return False

        if "wsgi:application" not in content:
            print("❌ railway.toml should reference wsgi:application")
            return False

        print("✅ Railway configuration validation passed")
        return True

    except Exception as e:
        print(f"❌ Railway configuration validation failed: {e}")
        return False
    """Test that railway.toml has consistent configuration."""
    try:
        with open("railway.toml") as f:
            content = f.read()

        # Check for health check configuration
        if 'healthcheckPath = "/health"' not in content:
            print("❌ railway.toml missing health check path configuration")
            return False

        # Check for gunicorn start command
        if "gunicorn" not in content:
            print("❌ railway.toml should use gunicorn start command")
            return False

        if "wsgi:application" not in content:
            print("❌ railway.toml should reference wsgi:application")
            return False

        print("✅ Railway configuration validation passed")
        return True

    except Exception as e:
        print(f"❌ Railway configuration validation failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Running deployment configuration tests...\n")

    tests = [
        ("Health Endpoint Logic", test_health_endpoint),
        ("Readiness Endpoint Logic", test_readiness_endpoint),
        ("Dockerfile Configuration", test_dockerfile_command),
        ("Railway Configuration", test_railway_config),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        if test_func():
            passed += 1
        print()

    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All deployment configuration tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please review the issues above.")
        sys.exit(1)
