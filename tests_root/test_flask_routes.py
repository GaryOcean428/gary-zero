#!/usr/bin/env python3
"""
Enhanced Flask route testing script for local development and validation.
Tests all critical routes with different HTTP methods to identify 405 issues.
"""

import sys
from urllib.parse import urljoin

import requests


def test_route(base_url, path, method, data=None, headers=None):
    """Test a single route with the specified method."""
    url = urljoin(base_url, path)

    if headers is None:
        headers = {"User-Agent": "Route-Tester/1.0"}

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            if data:
                if isinstance(data, dict):
                    response = requests.post(
                        url, json=data, headers=headers, timeout=10
                    )
                else:
                    response = requests.post(
                        url, data=data, headers=headers, timeout=10
                    )
            else:
                response = requests.post(url, headers=headers, timeout=10)
        elif method == "OPTIONS":
            response = requests.options(url, headers=headers, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data or {}, headers=headers, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        elif method == "PATCH":
            response = requests.patch(url, json=data or {}, headers=headers, timeout=10)
        else:
            return {"error": f"Unsupported method: {method}", "status": "ERROR"}

        return {
            "status": response.status_code,
            "headers": dict(response.headers),
            "content": response.text[:500] if response.text else "",
            "success": response.status_code < 400,
            "is_405": response.status_code == 405,
        }

    except requests.exceptions.ConnectionError:
        return {"error": "Connection refused", "status": "CONN"}
    except requests.exceptions.Timeout:
        return {"error": "Request timeout", "status": "TIMEOUT"}
    except Exception as e:
        return {"error": str(e), "status": "ERROR"}


def test_flask_routes(base_url):
    """Test Flask routes comprehensively."""
    print("🧪 Comprehensive Flask Route Testing")
    print(f"🎯 Testing server: {base_url}")
    print("=" * 80)

    # Critical routes that should work
    critical_tests = [
        # Health and readiness checks (Railway monitoring)
        {
            "path": "/health",
            "method": "GET",
            "critical": True,
            "desc": "Health check endpoint",
        },
        {
            "path": "/health",
            "method": "OPTIONS",
            "critical": True,
            "desc": "Health CORS preflight",
        },
        {
            "path": "/ready",
            "method": "GET",
            "critical": True,
            "desc": "Readiness check endpoint",
        },
        {
            "path": "/ready",
            "method": "OPTIONS",
            "critical": True,
            "desc": "Ready CORS preflight",
        },
        # Root endpoint (main application)
        {"path": "/", "method": "GET", "critical": True, "desc": "Main page GET"},
        {
            "path": "/",
            "method": "POST",
            "critical": True,
            "desc": "Form submission to root",
        },
        {
            "path": "/",
            "method": "OPTIONS",
            "critical": True,
            "desc": "Root CORS preflight",
        },
        # API endpoint
        {
            "path": "/api",
            "method": "GET",
            "critical": False,
            "desc": "API endpoint GET",
        },
        {
            "path": "/api",
            "method": "POST",
            "critical": False,
            "desc": "API endpoint POST",
        },
        {
            "path": "/api",
            "method": "OPTIONS",
            "critical": False,
            "desc": "API CORS preflight",
        },
        # Static content
        {
            "path": "/privacy",
            "method": "GET",
            "critical": False,
            "desc": "Privacy policy",
        },
        {
            "path": "/privacy",
            "method": "OPTIONS",
            "critical": False,
            "desc": "Privacy CORS preflight",
        },
        {
            "path": "/terms",
            "method": "GET",
            "critical": False,
            "desc": "Terms of service",
        },
        {
            "path": "/terms",
            "method": "OPTIONS",
            "critical": False,
            "desc": "Terms CORS preflight",
        },
        {"path": "/favicon.ico", "method": "GET", "critical": False, "desc": "Favicon"},
        {
            "path": "/favicon.ico",
            "method": "OPTIONS",
            "critical": False,
            "desc": "Favicon CORS preflight",
        },
        # Debug endpoint
        {
            "path": "/debug/routes",
            "method": "GET",
            "critical": False,
            "desc": "Route debugging",
        },
        {
            "path": "/debug/routes",
            "method": "OPTIONS",
            "critical": False,
            "desc": "Debug CORS preflight",
        },
        # Error handling tests
        {
            "path": "/nonexistent",
            "method": "GET",
            "critical": False,
            "desc": "404 error handling",
        },
    ]

    results = {"passed": 0, "failed": 0, "critical_failed": 0, "method_not_allowed": 0}

    print(f"{'Test Description':<35} {'Method':<8} {'Status':<8} {'Result'}")
    print("-" * 80)

    for test in critical_tests:
        result = test_route(base_url, test["path"], test["method"])

        if result.get("status") == "CONN":
            status_display = "CONN"
            icon = "❌"
            success = False
        elif result.get("status") == "ERROR":
            status_display = "ERROR"
            icon = "❌"
            success = False
        elif result.get("is_405"):
            status_display = "405"
            icon = "🚫"
            success = False
            results["method_not_allowed"] += 1
        elif result.get("success"):
            status_display = str(result["status"])
            icon = "✅"
            success = True
        else:
            status_display = str(result["status"])
            icon = "⚠️"
            success = (
                result["status"] in [404] and not test["critical"]
            )  # 404 is ok for nonexistent routes

        print(f"{test['desc']:<35} {test['method']:<8} {status_display:<8} {icon}")

        if success or (result.get("status") == 404 and test["path"] == "/nonexistent"):
            results["passed"] += 1
        else:
            results["failed"] += 1
            if test["critical"]:
                results["critical_failed"] += 1

    # Test methods that should return 405
    print("\n🚫 Testing 405 Method Not Allowed scenarios...")
    method_405_tests = [
        {"path": "/", "method": "PUT", "desc": "PUT method to root"},
        {"path": "/", "method": "DELETE", "desc": "DELETE method to root"},
        {"path": "/health", "method": "POST", "desc": "POST method to health"},
        {"path": "/api", "method": "DELETE", "desc": "DELETE method to API"},
        {"path": "/ready", "method": "PATCH", "desc": "PATCH method to ready"},
    ]

    for test in method_405_tests:
        result = test_route(base_url, test["path"], test["method"])

        if result.get("is_405"):
            print(f"✅ {test['desc']}: Correctly returned 405")
            results["passed"] += 1
        elif result.get("status") == "CONN":
            print(f"❌ {test['desc']}: Connection failed")
            results["failed"] += 1
        else:
            print(f"⚠️  {test['desc']}: Expected 405, got {result.get('status')}")
            results["failed"] += 1

    return results


def test_with_auth(base_url):
    """Test routes that might require authentication."""
    print("\n🔐 Testing authenticated endpoints...")

    # Test with basic auth (if configured)
    auth_tests = [
        {"path": "/", "method": "GET", "desc": "Root with auth"},
        {"path": "/api", "method": "GET", "desc": "API with auth"},
        {"path": "/debug/routes", "method": "GET", "desc": "Debug with auth"},
    ]

    # Try without auth first
    for test in auth_tests:
        result = test_route(base_url, test["path"], test["method"])

        if result.get("status") == 401:
            print(f"🔒 {test['desc']}: Correctly requires authentication")
        elif result.get("status") == "CONN":
            print(f"❌ {test['desc']}: Connection failed")
            break
        else:
            print(
                f"📖 {test['desc']}: Accessible without auth (status: {result.get('status')})"
            )


def main():
    """Main test function."""
    if len(sys.argv) < 2:
        print("Usage: python test_flask_routes.py <BASE_URL>")
        print("Examples:")
        print("  python test_flask_routes.py http://localhost:5000")
        print(
            "  python test_flask_routes.py https://gary-zero-production.up.railway.app"
        )
        sys.exit(1)

    base_url = sys.argv[1]

    # Test basic connectivity first
    print("🔍 Testing server connectivity...")
    try:
        import requests

        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Server is responding (status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {base_url}")
        print("Make sure the server is running and accessible.")
        sys.exit(1)
    except Exception as e:
        print(f"⚠️  Connection issue: {e}")

    # Run comprehensive tests
    results = test_flask_routes(base_url)

    # Test authentication if server is accessible
    test_with_auth(base_url)

    # Summary
    print("\n" + "=" * 80)
    print("📊 Test Summary:")
    print(f"   Total Tests: {results['passed'] + results['failed']}")
    print(f"   Passed: {results['passed']}")
    print(f"   Failed: {results['failed']}")
    print(f"   Critical Failures: {results['critical_failed']}")
    print(f"   405 Method Not Allowed: {results['method_not_allowed']}")

    if results["method_not_allowed"] == 0:
        print("\n✅ SUCCESS: No 405 Method Not Allowed errors detected!")
        print("   Railway deployment should work correctly.")
        exit_code = 0 if results["critical_failed"] == 0 else 1
    else:
        print(f"\n🚫 ISSUE: {results['method_not_allowed']} 405 errors found!")
        print("   These need to be fixed for proper Railway deployment.")
        exit_code = 1

    if results["critical_failed"] > 0:
        print(f"\n❌ CRITICAL: {results['critical_failed']} critical route failures!")
        print("   These must be fixed before deployment.")
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
