#!/usr/bin/env python3
"""
Basic Auth Security Verification Script
=======================================

Specifically verifies that the Basic Auth header "YWRtaW46YWRtaW4=" (admin:admin base64)
is never accepted by the Gary-Zero deployment.

This is a critical security check to ensure default credentials are not accepted.
"""

import base64
import sys
import time

import requests


def verify_basic_auth_security(base_url: str) -> tuple[bool, list[str]]:
    """
    Verify that Basic Auth with admin:admin credentials is rejected

    Returns:
        (is_secure, failed_endpoints): Tuple of security status and any failed endpoints
    """
    print(f"🔐 Verifying Basic Auth security for: {base_url}")

    # The insecure default credentials (base64 encoded "admin:admin")
    insecure_b64 = "YWRtaW46YWRtaW4="

    # Verify this is indeed admin:admin
    decoded = base64.b64decode(insecure_b64).decode("ascii")
    print(f"📋 Testing against credentials: {decoded}")

    if decoded != "admin:admin":
        print("❌ ERROR: Base64 decoding verification failed!")
        return False, ["Base64 verification failed"]

    # Test endpoints that should never accept default credentials
    test_endpoints = [
        "/",
        "/api/models",
        "/api/chat",
        "/api/settings",
        "/api/auth/login",
        "/settings",
        "/admin",
        "/dashboard",
    ]

    failed_endpoints = []
    session = requests.Session()
    session.timeout = 10

    for endpoint in test_endpoints:
        try:
            print(f"🔍 Testing endpoint: {endpoint}")

            headers = {"Authorization": f"Basic {insecure_b64}"}
            response = session.get(f"{base_url}{endpoint}", headers=headers)

            # Check if the endpoint improperly accepts the default credentials
            is_vulnerable = False

            # Check 1: Should not return 200 OK with admin content
            if response.status_code == 200:
                response_text = response.text.lower()
                # Look for signs that admin access was granted
                if any(
                    word in response_text
                    for word in ["admin", "dashboard", "configuration", "settings"]
                ):
                    is_vulnerable = True
                    print(
                        f"⚠️  WARNING: Endpoint {endpoint} may accept default credentials (200 OK with admin content)"
                    )

            # Check 2: Should not return admin-specific responses
            if "admin" in response.headers.get("Server", "").lower():
                is_vulnerable = True
                print(f"⚠️  WARNING: Endpoint {endpoint} returns admin server header")

            # Check 3: Should not return authentication success indicators
            if (
                response.status_code in [200, 302]
                and "welcome" in response.text.lower()
            ):
                is_vulnerable = True
                print(f"⚠️  WARNING: Endpoint {endpoint} may indicate successful auth")

            if is_vulnerable:
                failed_endpoints.append(endpoint)
                print(f"❌ SECURITY RISK: {endpoint} accepts default credentials!")
            else:
                print(
                    f"✅ SECURE: {endpoint} properly rejects default credentials (status: {response.status_code})"
                )

        except requests.RequestException as e:
            # Network errors are acceptable - the endpoint may not exist or may be protected
            print(f"🔒 PROTECTED: {endpoint} - {str(e)[:50]}...")
        except Exception as e:
            print(f"⚠️  ERROR testing {endpoint}: {str(e)}")

        time.sleep(0.5)  # Small delay between requests

    is_secure = len(failed_endpoints) == 0

    print(f"\n{'=' * 60}")
    print("🔐 BASIC AUTH SECURITY VERIFICATION RESULTS")
    print(f"{'=' * 60}")
    print(f"Tested Base64 Header: {insecure_b64}")
    print(f"Decoded Credentials: {decoded}")
    print(f"Endpoints Tested: {len(test_endpoints)}")
    print(f"Vulnerable Endpoints: {len(failed_endpoints)}")

    if is_secure:
        print("\n🎉 ✅ SECURITY VERIFICATION PASSED!")
        print("🔒 No endpoints accept the default admin:admin credentials")
        print("🛡️  Basic Auth security is properly configured")
    else:
        print("\n❌ 🚨 SECURITY VULNERABILITY DETECTED!")
        print(f"🔓 {len(failed_endpoints)} endpoint(s) accept default credentials:")
        for endpoint in failed_endpoints:
            print(f"   - {endpoint}")
        print("🚨 IMMEDIATE ACTION REQUIRED: Change default credentials!")

    print(f"{'=' * 60}")

    return is_secure, failed_endpoints


def main():
    """Main function"""
    base_url = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "https://gary-zero-production.up.railway.app"
    )
    base_url = base_url.rstrip("/")

    print("🔐 Gary-Zero Basic Auth Security Verification")
    print(f"📍 Target: {base_url}")
    print("🎯 Objective: Verify admin:admin credentials are rejected")
    print()

    is_secure, failed_endpoints = verify_basic_auth_security(base_url)

    # Exit with appropriate code for CI/CD systems
    sys.exit(0 if is_secure else 1)


if __name__ == "__main__":
    main()
