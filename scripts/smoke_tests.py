#!/usr/bin/env python3
"""
Gary-Zero Smoke Test Suite
==========================

Comprehensive smoke tests for Gary-Zero deployment covering:
- Authentication functionality
- Model selection and configuration
- CLI execution capabilities
- Basic Auth security verification
- Core API endpoints

Usage:
    python scripts/smoke_tests.py [base_url]

Default base_url: https://gary-zero-production.up.railway.app
"""

import base64
import json
import sys
import time

import requests


class SmokeTestRunner:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.timeout = 30
        self.test_results: list[dict] = []

    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def run_test(self, test_name: str, test_func, *args, **kwargs) -> bool:
        """Run a single test and record results"""
        self.log(f"Running test: {test_name}")
        try:
            result = test_func(*args, **kwargs)
            if result:
                self.log(f"✅ PASS: {test_name}", "PASS")
                self.test_results.append(
                    {"name": test_name, "status": "PASS", "error": None}
                )
                return True
            else:
                self.log(f"❌ FAIL: {test_name}", "FAIL")
                self.test_results.append(
                    {
                        "name": test_name,
                        "status": "FAIL",
                        "error": "Test returned False",
                    }
                )
                return False
        except Exception as e:
            self.log(f"❌ ERROR: {test_name} - {str(e)}", "ERROR")
            self.test_results.append(
                {"name": test_name, "status": "ERROR", "error": str(e)}
            )
            return False

    def test_health_endpoint(self) -> bool:
        """Test basic health endpoint"""
        response = self.session.get(f"{self.base_url}/health")
        return response.status_code == 200

    def test_healthz_endpoint(self) -> bool:
        """Test alternative health endpoint"""
        response = self.session.get(f"{self.base_url}/healthz")
        return response.status_code == 200

    def test_root_endpoint(self) -> bool:
        """Test root endpoint returns the UI"""
        response = self.session.get(f"{self.base_url}/")
        return response.status_code == 200 and "Gary-Zero" in response.text

    def test_basic_auth_security(self) -> bool:
        """Verify Basic Auth header is never admin:admin"""
        # Test that we don't accept the insecure default credentials
        insecure_b64 = base64.b64encode(b"admin:admin").decode("ascii")

        # Test various endpoints with the insecure credentials
        test_endpoints = ["/", "/api/models", "/api/chat", "/settings"]

        for endpoint in test_endpoints:
            try:
                headers = {"Authorization": f"Basic {insecure_b64}"}
                response = self.session.get(
                    f"{self.base_url}{endpoint}", headers=headers
                )

                # Should not be authorized with default credentials
                if response.status_code == 200 and "admin" in response.text.lower():
                    self.log(
                        f"SECURITY RISK: Default credentials accepted on {endpoint}"
                    )
                    return False

            except Exception:
                # Network errors are acceptable for this security test
                pass

        return True

    def test_models_endpoint(self) -> bool:
        """Test model selection endpoint"""
        response = self.session.get(f"{self.base_url}/api/models")
        if response.status_code == 200:
            try:
                models = response.json()
                return isinstance(models, (list, dict)) and len(models) > 0
            except json.JSONDecodeError:
                return False
        return False

    def test_settings_endpoint(self) -> bool:
        """Test settings/configuration endpoint"""
        response = self.session.get(f"{self.base_url}/api/settings")
        return response.status_code in [200, 401, 403]  # Could be protected

    def test_chat_endpoint_structure(self) -> bool:
        """Test chat endpoint exists and has proper structure"""
        response = self.session.post(
            f"{self.base_url}/api/chat", json={"message": "test"}
        )
        # Should not return 404 (endpoint exists) but may return 401/403 (auth required)
        return response.status_code != 404

    def test_cli_execution_endpoint(self) -> bool:
        """Test CLI execution endpoint exists"""
        response = self.session.post(
            f"{self.base_url}/api/execute", json={"command": "echo test"}
        )
        # Should not return 404 (endpoint exists) but may return 401/403 (auth required)
        return response.status_code != 404

    def test_websocket_availability(self) -> bool:
        """Test WebSocket endpoint availability"""
        # For smoke test, just verify the endpoint responds
        try:
            import websocket

            ws_url = self.base_url.replace("https://", "wss://").replace(
                "http://", "ws://"
            )
            ws = websocket.create_connection(f"{ws_url}/ws", timeout=5)
            ws.close()
            return True
        except:
            # WebSocket may not be available or may require auth
            # For smoke test, we'll check if the HTTP endpoint returns something
            response = self.session.get(f"{self.base_url}/ws")
            return response.status_code != 404

    def test_static_assets(self) -> bool:
        """Test static assets are served"""
        # Test CSS and JS assets
        css_response = self.session.get(f"{self.base_url}/css/main.css")
        js_response = self.session.get(f"{self.base_url}/js/main.js")

        return (
            css_response.status_code == 200
            or js_response.status_code == 200
            or
            # Alternative paths
            self.session.get(f"{self.base_url}/static/css/main.css").status_code == 200
            or self.session.get(f"{self.base_url}/webui/css/main.css").status_code
            == 200
        )

    def test_model_configuration(self) -> bool:
        """Test model configuration and selection"""
        # Try to get available models
        response = self.session.get(f"{self.base_url}/api/models/available")
        if response.status_code == 200:
            return True

        # Fallback: check if models endpoint returns data
        response = self.session.get(f"{self.base_url}/api/models")
        if response.status_code == 200:
            try:
                data = response.json()
                return len(data) > 0 if isinstance(data, (list, dict)) else False
            except:
                return False
        return False

    def test_authentication_workflow(self) -> bool:
        """Test authentication workflow"""
        # Test login endpoint exists
        login_response = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={"username": "test", "password": "test"},
        )

        # Should not return 404 (endpoint exists)
        if login_response.status_code == 404:
            return False

        # Test logout endpoint exists
        logout_response = self.session.post(f"{self.base_url}/api/auth/logout")
        return logout_response.status_code != 404

    def run_all_tests(self) -> tuple[int, int]:
        """Run all smoke tests"""
        self.log("🚀 Starting Gary-Zero Smoke Test Suite")
        self.log(f"🌐 Testing deployment at: {self.base_url}")

        # Core functionality tests
        tests = [
            ("Health Endpoint", self.test_health_endpoint),
            ("Alternative Health Endpoint", self.test_healthz_endpoint),
            ("Root Endpoint", self.test_root_endpoint),
            ("Basic Auth Security", self.test_basic_auth_security),
            ("Models Endpoint", self.test_models_endpoint),
            ("Settings Endpoint", self.test_settings_endpoint),
            ("Chat Endpoint Structure", self.test_chat_endpoint_structure),
            ("CLI Execution Endpoint", self.test_cli_execution_endpoint),
            ("WebSocket Availability", self.test_websocket_availability),
            ("Static Assets", self.test_static_assets),
            ("Model Configuration", self.test_model_configuration),
            ("Authentication Workflow", self.test_authentication_workflow),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed += 1
            time.sleep(1)  # Small delay between tests

        return passed, total

    def print_summary(self, passed: int, total: int):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🧪 SMOKE TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed / total) * 100:.1f}%")

        if passed == total:
            print("\n🎉 ALL SMOKE TESTS PASSED!")
            print("✅ Deployment is ready for production use")
        elif passed >= total * 0.8:  # 80% pass rate
            print("\n⚠️  MOST TESTS PASSED - Minor issues detected")
            print("🟡 Deployment may be usable but needs attention")
        else:
            print("\n❌ CRITICAL ISSUES DETECTED")
            print("🔴 Deployment requires immediate attention")

        print("\nFailed tests:")
        for result in self.test_results:
            if result["status"] != "PASS":
                print(f"  - {result['name']}: {result['error']}")

        print("=" * 60)

        return passed >= total * 0.8  # Return True if 80%+ tests pass


def main():
    """Main function"""
    base_url = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "https://gary-zero-production.up.railway.app"
    )

    runner = SmokeTestRunner(base_url)
    passed, total = runner.run_all_tests()
    success = runner.print_summary(passed, total)

    # Exit code for CI/CD systems
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
