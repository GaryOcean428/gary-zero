#!/usr/bin/env python3
"""
Basic health check and validation tests for Gary-Zero improvements.
This tests the core functionality without requiring full Flask setup.
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path.cwd()  # Use current working directory
sys.path.insert(0, str(project_root))


def test_legal_pages_exist():
    """Test that legal pages exist and have content."""
    webui_path = project_root / "webui"

    # Check privacy policy
    privacy_path = webui_path / "privacy.html"
    assert privacy_path.exists(), "Privacy policy page does not exist"

    privacy_content = privacy_path.read_text()
    assert "Privacy Policy" in privacy_content, "Privacy policy missing title"
    assert "Gary-Zero" in privacy_content, "Privacy policy missing app name"
    assert "data" in privacy_content.lower(), (
        "Privacy policy missing data handling info"
    )

    # Check terms of service
    terms_path = webui_path / "terms.html"
    assert terms_path.exists(), "Terms of service page does not exist"

    terms_content = terms_path.read_text()
    assert "Terms of Service" in terms_content, "Terms missing title"
    assert "open-source" in terms_content, "Terms missing open-source reference"

    print("✅ Legal pages test passed")


def test_error_pages_exist():
    """Test that custom error pages exist."""
    webui_path = project_root / "webui"

    # Check 404 page
    error_404_path = webui_path / "404.html"
    assert error_404_path.exists(), "404 error page does not exist"

    error_404_content = error_404_path.read_text()
    assert "404" in error_404_content, "404 page missing error code"
    assert "Page Not Found" in error_404_content, "404 page missing title"

    # Check 500 page
    error_500_path = webui_path / "500.html"
    assert error_500_path.exists(), "500 error page does not exist"

    error_500_content = error_500_path.read_text()
    assert "500" in error_500_content, "500 page missing error code"
    assert "Internal Server Error" in error_500_content, "500 page missing title"

    print("✅ Error pages test passed")


def test_enhanced_ux_script_exists():
    """Test that enhanced UX script exists and has core functionality."""
    ux_script_path = project_root / "webui" / "js" / "enhanced-ux.js"
    assert ux_script_path.exists(), "Enhanced UX script does not exist"

    ux_content = ux_script_path.read_text()
    assert "ToastManager" in ux_content, "ToastManager class missing"
    assert "InputValidator" in ux_content, "InputValidator class missing"
    assert "LoadingManager" in ux_content, "LoadingManager class missing"
    assert "AlpineErrorBoundary" in ux_content, "AlpineErrorBoundary class missing"

    print("✅ Enhanced UX script test passed")


def test_index_html_enhancements():
    """Test that index.html has accessibility and UX enhancements."""
    index_path = project_root / "webui" / "index.html"
    assert index_path.exists(), "Index.html does not exist"

    index_content = index_path.read_text()
    assert "enhanced-ux.js" in index_content, "Enhanced UX script not included"
    assert "aria-label" in index_content, "Missing accessibility attributes"
    assert "sr-only" in index_content, "Missing screen reader only class"
    assert "char-count" in index_content, "Missing character count feature"

    print("✅ Index.html enhancements test passed")


def test_api_improvements():
    """Test that API improvements are in place."""
    api_path = project_root / "framework" / "helpers" / "api.py"
    assert api_path.exists(), "API helper does not exist"

    api_content = api_path.read_text()
    assert "import time" in api_content, "Time import missing for timestamps"
    assert "timestamp" in api_content, "Timestamp not added to error responses"
    assert "application/json" in api_content, "JSON mimetype not set for errors"

    print("✅ API improvements test passed")


def test_security_headers():
    """Test that security headers are implemented."""
    run_ui_path = project_root / "run_ui.py"
    assert run_ui_path.exists(), "run_ui.py does not exist"

    run_ui_content = run_ui_path.read_text()
    assert "add_security_headers" in run_ui_content, "Security headers function missing"
    assert "X-Frame-Options" in run_ui_content, "X-Frame-Options header missing"
    assert "X-Content-Type-Options" in run_ui_content, (
        "X-Content-Type-Options header missing"
    )
    assert "Content-Security-Policy" in run_ui_content, "CSP header missing"

    print("✅ Security headers test passed")


def test_health_endpoint():
    """Test that health endpoint is implemented."""
    run_ui_path = project_root / "run_ui.py"
    run_ui_content = run_ui_path.read_text()

    assert "/health" in run_ui_content, "Health endpoint route missing"
    assert "health_check" in run_ui_content, "Health check function missing"
    assert "healthy" in run_ui_content, "Health status missing"

    print("✅ Health endpoint test passed")


def test_eslint_config():
    """Test that ESLint configuration is improved."""
    eslint_path = project_root / "eslint.config.js"
    assert eslint_path.exists(), "ESLint config does not exist"

    eslint_content = eslint_path.read_text()
    assert "transformers@" in eslint_content, "Third-party library ignores missing"
    assert "ace:" in eslint_content, "Ace editor global missing"
    assert "structuredClone" in eslint_content, "Modern browser APIs missing"

    print("✅ ESLint configuration test passed")


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_legal_pages_exist,
        test_error_pages_exist,
        test_enhanced_ux_script_exists,
        test_index_html_enhancements,
        test_api_improvements,
        test_security_headers,
        test_health_endpoint,
        test_eslint_config,
    ]

    failed_tests = []

    print("🧪 Running Gary-Zero improvement tests...\n")

    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed_tests.append(test.__name__)

    print("\n📊 Test Results:")
    print(f"✅ Passed: {len(tests) - len(failed_tests)}/{len(tests)}")
    if failed_tests:
        print(f"❌ Failed: {len(failed_tests)}")
        print("Failed tests:", ", ".join(failed_tests))
        return False
    else:
        print("🎉 All tests passed!")
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
