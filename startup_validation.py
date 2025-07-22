#!/usr/bin/env python3
"""Startup validation script to ensure health endpoint is ready."""

import os
import sys


def validate_gunicorn_setup():
    """Validate that Gunicorn configuration is correct."""
    print("🔍 Validating Gunicorn setup...")

    # Check that wsgi.py exists
    if not os.path.exists('wsgi.py'):
        print("❌ wsgi.py file not found")
        return False

    # Check that gunicorn is available
    try:
        import gunicorn
        print(f"✅ Gunicorn {gunicorn.__version__} is available")
    except ImportError:
        print("❌ Gunicorn not installed")
        return False

    print("✅ Gunicorn setup validation passed")
    return True

def validate_health_endpoint():
    """Validate that health endpoint exists in code."""
    print("🔍 Validating health endpoint...")

    try:
        with open('run_ui.py') as f:
            content = f.read()

        # Check for health endpoint definition
        if '@webapp.route("/health"' not in content:
            print("❌ Health endpoint route not found")
            return False

        if 'def health_check():' not in content:
            print("❌ Health check function not found")
            return False

        print("✅ Health endpoint found in code")
        return True

    except Exception as e:
        print(f"❌ Error validating health endpoint: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Railway deployment startup validation")
    print("=" * 50)

    validations = [
        validate_gunicorn_setup,
        validate_health_endpoint,
    ]

    passed = 0
    for validation in validations:
        if validation():
            passed += 1
        print()

    if passed == len(validations):
        print("🎉 All startup validations passed!")
        print("✅ Application should be ready for Railway deployment")
    else:
        print(f"❌ {len(validations) - passed} validation(s) failed")
        sys.exit(1)
