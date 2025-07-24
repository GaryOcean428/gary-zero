#!/usr/bin/env python3
"""
Railway route validation test - checks for 405 Method Not Allowed fixes.
"""

import sys

import requests


def test_railway_routes(base_url):
    """Test Railway deployment routes for 405 fixes."""
    print(f"🚀 Testing Railway routes at: {base_url}")

    critical_tests = [
        # Health checks that Railway monitoring needs
        {
            "path": "/health",
            "method": "GET",
            "critical": True,
            "desc": "Health check endpoint",
        },
        {
            "path": "/ready",
            "method": "GET",
            "critical": True,
            "desc": "Readiness check endpoint",
        },
        # Root endpoint that often receives different HTTP methods
        {
            "path": "/",
            "method": "GET",
            "critical": True,
            "desc": "Main page GET request",
        },
        {
            "path": "/",
            "method": "POST",
            "critical": True,
            "desc": "Form submission to root",
        },
        # API endpoints that may receive various methods
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
        # CORS preflight requests (critical for browser apps)
        {
            "path": "/health",
            "method": "OPTIONS",
            "critical": False,
            "desc": "CORS preflight for health",
        },
        {
            "path": "/api",
            "method": "OPTIONS",
            "critical": False,
            "desc": "CORS preflight for API",
        },
        {
            "path": "/",
            "method": "OPTIONS",
            "critical": False,
            "desc": "CORS preflight for root",
        },
        # Error handling validation
        {
            "path": "/nonexistent",
            "method": "GET",
            "critical": False,
            "desc": "404 error handling",
        },
    ]

    results = {"passed": 0, "failed": 0, "critical_failed": 0, "method_not_allowed": 0}

    print(f"{'Test':<40} {'Method':<8} {'Status':<8} {'Result'}")
    print("-" * 70)

    for test in critical_tests:
        try:
            headers = {"User-Agent": "Railway-Route-Tester/1.0"}

            if test["method"] == "GET":
                response = requests.get(
                    f"{base_url}{test['path']}", headers=headers, timeout=10
                )
            elif test["method"] == "POST":
                response = requests.post(
                    f"{base_url}{test['path']}",
                    json={"message": "test", "source": "route_tester"},
                    headers=headers,
                    timeout=10,
                )
            elif test["method"] == "OPTIONS":
                response = requests.options(
                    f"{base_url}{test['path']}", headers=headers, timeout=10
                )

            # Evaluate the response
            if response.status_code == 405:
                # This is the error we're trying to fix!
                print(
                    f"{'❌ ' + test['desc']:<40} {test['method']:<8} {response.status_code:<8} METHOD NOT ALLOWED"
                )
                results["method_not_allowed"] += 1
                results["failed"] += 1
                if test["critical"]:
                    results["critical_failed"] += 1

                # Try to show error details
                try:
                    error_data = response.json()
                    if "allowed_methods" in error_data:
                        print(f"    Allowed methods: {error_data['allowed_methods']}")
                except:
                    pass

            elif response.status_code < 400:
                # Success
                print(
                    f"{'✅ ' + test['desc']:<40} {test['method']:<8} {response.status_code:<8} OK"
                )
                results["passed"] += 1

            elif response.status_code == 404 and test["path"] == "/nonexistent":
                # Expected 404
                print(
                    f"{'✅ ' + test['desc']:<40} {test['method']:<8} {response.status_code:<8} OK (expected)"
                )
                results["passed"] += 1

            elif response.status_code in [401, 403]:
                # Authentication required - not a routing issue
                print(
                    f"{'🔐 ' + test['desc']:<40} {test['method']:<8} {response.status_code:<8} AUTH REQUIRED"
                )
                results["passed"] += 1

            elif response.status_code >= 500:
                # Server error
                print(
                    f"{'⚠️ ' + test['desc']:<40} {test['method']:<8} {response.status_code:<8} SERVER ERROR"
                )
                results["failed"] += 1
                if test["critical"]:
                    results["critical_failed"] += 1

            else:
                # Other client error
                print(
                    f"{'⚠️ ' + test['desc']:<40} {test['method']:<8} {response.status_code:<8} CLIENT ERROR"
                )
                results["failed"] += 1

        except requests.exceptions.ConnectionError:
            print(
                f"{'❌ ' + test['desc']:<40} {test['method']:<8} {'CONN':<8} CONNECTION FAILED"
            )
            results["failed"] += 1
            if test["critical"]:
                results["critical_failed"] += 1

        except requests.exceptions.Timeout:
            print(
                f"{'❌ ' + test['desc']:<40} {test['method']:<8} {'TIMEOUT':<8} REQUEST TIMEOUT"
            )
            results["failed"] += 1
            if test["critical"]:
                results["critical_failed"] += 1

        except Exception as e:
            print(
                f"{'❌ ' + test['desc']:<40} {test['method']:<8} {'ERROR':<8} {str(e)[:20]}"
            )
            results["failed"] += 1
            if test["critical"]:
                results["critical_failed"] += 1

    return results


def test_specific_405_scenarios(base_url):
    """Test specific scenarios that commonly cause 405 errors."""
    print("\n🎯 Testing specific 405 scenarios...")

    scenarios = [
        {
            "name": "PUT method to root",
            "method": "PUT",
            "path": "/",
            "should_be_405": True,  # This should return 405 with proper error message
        },
        {
            "name": "DELETE method to API",
            "method": "DELETE",
            "path": "/api",
            "should_be_405": True,
        },
        {
            "name": "PATCH method to health",
            "method": "PATCH",
            "path": "/health",
            "should_be_405": True,
        },
    ]

    for scenario in scenarios:
        try:
            response = requests.request(
                method=scenario["method"],
                url=f"{base_url}{scenario['path']}",
                timeout=10,
            )

            if scenario["should_be_405"] and response.status_code == 405:
                print(f"✅ {scenario['name']}: Correctly returned 405")

                # Check if we get proper error details
                try:
                    error_data = response.json()
                    if "allowed_methods" in error_data and "message" in error_data:
                        print("   ✅ Enhanced error details provided")
                    else:
                        print("   ⚠️ Basic 405 response (could be enhanced)")
                except:
                    print("   ⚠️ Non-JSON 405 response")

            elif scenario["should_be_405"]:
                print(f"⚠️ {scenario['name']}: Expected 405, got {response.status_code}")
            else:
                print(f"✅ {scenario['name']}: Status {response.status_code}")

        except Exception as e:
            print(f"❌ {scenario['name']}: Error - {e}")


def main():
    """Main test function."""
    if len(sys.argv) < 2:
        print("Usage: python test_railway_routes.py <BASE_URL>")
        print(
            "Example: python test_railway_routes.py https://gary-zero-production.up.railway.app"
        )
        print("         python test_railway_routes.py http://localhost:8000")
        sys.exit(1)

    base_url = sys.argv[1].rstrip("/")

    print("🧪 Railway Route Testing for 405 Method Not Allowed Fixes")
    print("=" * 70)
    print("Testing critical routes to ensure they handle multiple HTTP methods...")
    print()

    # Test main routes
    results = test_railway_routes(base_url)

    # Test specific 405 scenarios
    test_specific_405_scenarios(base_url)

    print("\n" + "=" * 70)
    print("📊 Test Summary:")
    print(f"   Total Tests: {results['passed'] + results['failed']}")
    print(f"   Passed: {results['passed']}")
    print(f"   Failed: {results['failed']}")
    print(f"   Critical Failures: {results['critical_failed']}")
    print(f"   405 Method Not Allowed: {results['method_not_allowed']}")

    if results["method_not_allowed"] == 0:
        print("\n✅ SUCCESS: No 405 Method Not Allowed errors detected!")
        print("   Railway deployment should work correctly.")
    elif results["critical_failed"] == 0:
        print(
            "\n⚠️ PARTIAL SUCCESS: Some non-critical 405 errors, but core functionality works."
        )
    else:
        print(
            f"\n❌ FAILURE: {results['critical_failed']} critical endpoints returning 405 errors."
        )
        print("   This will cause Railway deployment issues.")

    # Return appropriate exit code
    return 0 if results["critical_failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
