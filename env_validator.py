#!/usr/bin/env python3
"""Environment validation script for Railway deployments.

This script validates required and optional environment variables
to ensure proper Railway deployment configuration.
"""

import os
import sys

# Required environment variables for Railway deployment
REQUIRED_VARS = ['PORT']

# Optional Railway-specific variables that provide useful information
OPTIONAL_VARS = [
    'RAILWAY_SERVICE_NAME',
    'RAILWAY_ENVIRONMENT',
    'RAILWAY_PROJECT_NAME',
    'RAILWAY_DEPLOYMENT_ID',
    'DATABASE_URL'
]

# Application-specific optional variables
APP_OPTIONAL_VARS = [
    'WEB_UI_HOST',
    'WEB_UI_PORT',
    'PYTHONUNBUFFERED',
    'FLASK_ENV',
    'AUTH_LOGIN',
    'AUTH_PASSWORD'
]


def validate_env() -> bool:
    """Validate environment variables for Railway deployment.
    
    Returns:
        bool: True if validation passes, False otherwise.
    """
    print("🔍 Validating environment variables...")

    # Check required variables
    missing_required = [var for var in REQUIRED_VARS if not os.getenv(var)]
    if missing_required:
        print(f"❌ Missing required environment variables: {missing_required}")
        print("💡 These variables are mandatory for Railway service exposure.")
        return False

    print(f"✅ All required variables present: {REQUIRED_VARS}")

    # Check optional Railway variables (informational)
    present_railway = [var for var in OPTIONAL_VARS if os.getenv(var)]
    if present_railway:
        print(f"📋 Railway variables detected: {present_railway}")

    # Check application variables (informational)
    present_app = [var for var in APP_OPTIONAL_VARS if os.getenv(var)]
    if present_app:
        print(f"⚙️  Application variables present: {present_app}")

    # Validate PORT value
    port_value = os.getenv('PORT')
    if port_value:
        try:
            port_int = int(port_value)
            if 1 <= port_int <= 65535:
                print(f"✅ PORT value is valid: {port_int}")
            else:
                print(f"⚠️  PORT value out of valid range (1-65535): {port_int}")
                return False
        except ValueError:
            print(f"❌ PORT value is not a valid integer: {port_value}")
            return False

    print("✅ Environment validation passed")
    return True


def main() -> None:
    """Main entry point for environment validation."""
    print("🚀 Railway Environment Validator")
    print("=" * 50)

    # Check if we're running in Railway environment
    if os.getenv('RAILWAY_ENVIRONMENT'):
        print(f"🚄 Running in Railway environment: {os.getenv('RAILWAY_ENVIRONMENT')}")
    else:
        print("🏠 Running in local/non-Railway environment")

    if not validate_env():
        print("\n❌ Environment validation failed!")
        print("Please ensure all required environment variables are set.")
        sys.exit(1)

    print("\n🎉 Environment validation successful!")
    print("Ready for Railway deployment.")


if __name__ == "__main__":
    main()
