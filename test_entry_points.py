#!/usr/bin/env python3
"""
Test script to verify all entry points handle template substitution correctly.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_flask_route():
    """Test Flask route template rendering."""
    print("🧪 Testing Flask route (run_ui.py)...")
    try:
        from run_ui import webapp

        # Create test client
        with webapp.test_client() as client:
            # Mock authentication for testing
            with webapp.test_request_context():
                from run_ui import serve_index

                html = serve_index()

                # Check for placeholders
                if "{{" in html and "}}" in html:
                    print("❌ Flask route has unresolved placeholders")
                    return False

                if "Version " not in html:
                    print("❌ Flask route missing version information")
                    return False

                print("✅ Flask route template rendering works")
                return True

    except Exception as e:
        print(f"❌ Flask route test failed: {e}")
        return False


def test_fastapi_route():
    """Test FastAPI route template rendering."""
    print("🧪 Testing FastAPI route (main.py)...")
    try:
        # This would require more setup for full testing
        # For now, just check that the route function works
        import asyncio

        from main import serve_ui

        async def test_serve_ui():
            response = await serve_ui()
            return response.body.decode("utf-8")

        html = asyncio.run(test_serve_ui())

        # Check for placeholders
        if "{{" in html and "}}" in html:
            print("❌ FastAPI route has unresolved placeholders")
            return False

        if "Version " not in html:
            print("❌ FastAPI route missing version information")
            return False

        print("✅ FastAPI route template rendering works")
        return True

    except Exception as e:
        print(f"❌ FastAPI route test failed: {e}")
        return False


def test_template_helper_directly():
    """Test template helper directly."""
    print("🧪 Testing template helper directly...")
    try:
        from framework.helpers.template_helper import render_index_html

        html = render_index_html()

        # Check for placeholders
        placeholders = []
        if "{{version_no}}" in html:
            placeholders.append("{{version_no}}")
        if "{{version_time}}" in html:
            placeholders.append("{{version_time}}")
        if "{{feature_flags_config}}" in html:
            placeholders.append("{{feature_flags_config}}")

        if placeholders:
            print(f"❌ Template helper has unresolved placeholders: {placeholders}")
            return False

        if "Version " not in html:
            print("❌ Template helper missing version information")
            return False

        if "<script>" not in html:
            print("❌ Template helper missing JavaScript injection")
            return False

        print("✅ Template helper works correctly")
        return True

    except Exception as e:
        print(f"❌ Template helper test failed: {e}")
        return False


def test_configuration_loader():
    """Test configuration loader."""
    print("🧪 Testing configuration loader...")
    try:
        from framework.helpers.config_loader import get_config_loader

        config = get_config_loader()

        # Test port resolution
        port = config.get_port()
        if not isinstance(port, int) or port <= 0:
            print(f"❌ Invalid port: {port}")
            return False

        # Test template variables
        template_vars = config.get_template_vars()
        required_vars = ["version_no", "version_time", "feature_flags_config"]

        for var in required_vars:
            if var not in template_vars:
                print(f"❌ Missing template variable: {var}")
                return False

        # Check for unresolved placeholders in template vars
        for var, value in template_vars.items():
            if "{{" in str(value) and "}}" in str(value):
                print(f"❌ Template variable {var} has unresolved placeholder: {value}")
                return False

        print("✅ Configuration loader works correctly")
        return True

    except Exception as e:
        print(f"❌ Configuration loader test failed: {e}")
        return False


def main():
    """Run all entry point tests."""
    print("🚀 Testing All Entry Points for Template Consistency")
    print("=" * 55)

    # Set up test environment
    os.environ.setdefault("PORT", "8000")
    os.environ.setdefault("WEB_UI_HOST", "0.0.0.0")

    tests = [
        ("Configuration Loader", test_configuration_loader),
        ("Template Helper", test_template_helper_directly),
        ("Flask Route", test_flask_route),
        ("FastAPI Route", test_fastapi_route),
    ]

    passed = 0
    total = len(tests)

    for name, test_func in tests:
        print(f"\n📋 {name}:")
        if test_func():
            passed += 1

    print("\n" + "=" * 55)
    print(f"📊 Entry Point Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All entry points handle templates consistently!")
        return 0
    else:
        print("❌ Some entry points have template issues!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
