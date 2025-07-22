#!/usr/bin/env python3
"""
Environment variable compatibility validator for gary-zero deployment standardization.
Validates that environment variables are consistently named between Railway and Docker deployments.
"""

import os
import sys

def validate_environment_variables():
    """Validate standard environment variables are properly named."""
    
    print("🔍 Environment Variable Standardization Check")
    print("=" * 50)
    
    # Standard environment variables that should be consistent
    standard_vars = {
        "PORT": "Application port (Railway/Docker compatible)",
        "WEB_UI_HOST": "Web UI host binding (0.0.0.0 for containers)",
        "PYTHONUNBUFFERED": "Python output buffering (1 for containers)",
        "RAILWAY_ENVIRONMENT": "Railway environment indicator",
        "DATA_DIR": "Data directory for persistent storage",
        "CODE_EXECUTION_MODE": "Code execution mode (secure/direct/kali)",
        "SEARXNG_URL": "SearXNG service URL",
        "KALI_SHELL_URL": "Kali shell service URL"
    }
    
    print("📋 Standard Environment Variables:")
    for var, description in standard_vars.items():
        value = os.getenv(var, "Not set")
        print(f"  {var}: {value}")
        print(f"    → {description}")
    
    print()
    
    # Check for Railway-specific patterns
    railway_vars = [key for key in os.environ.keys() if key.startswith('RAILWAY_')]
    print(f"🚂 Railway Variables Found: {len(railway_vars)}")
    for var in railway_vars:
        print(f"  {var}: {os.getenv(var)}")
    
    print()
    
    # Validate naming consistency
    inconsistencies = []
    
    # Check for common inconsistency patterns
    if os.getenv("PORT") and os.getenv("WEB_UI_PORT"):
        if os.getenv("PORT") != os.getenv("WEB_UI_PORT"):
            print("⚠️  PORT and WEB_UI_PORT have different values")
    
    # Check for proper Railway integration
    if not os.getenv("RAILWAY_ENVIRONMENT"):
        print("ℹ️  RAILWAY_ENVIRONMENT not set (expected for local/Docker deployment)")
    
    print("✅ Environment variable standardization check completed")
    return len(inconsistencies) == 0

def check_deployment_compatibility():
    """Check that both Railway and Docker deployments use compatible variables."""
    
    print("\n🐳 Deployment Compatibility Check")
    print("=" * 35)
    
    # Read railway.toml variables
    railway_vars = set()
    try:
        with open('railway.toml', 'r') as f:
            content = f.read()
            # Extract variable names from railway.toml
            lines = content.split('\n')
            in_variables = False
            for line in lines:
                if '[services.variables]' in line:
                    in_variables = True
                elif line.startswith('[') and in_variables:
                    break
                elif in_variables and '=' in line and not line.strip().startswith('#'):
                    var_name = line.split('=')[0].strip()
                    railway_vars.add(var_name)
    except FileNotFoundError:
        print("❌ railway.toml not found")
        return False
    
    # Read .env.example variables  
    env_vars = set()
    try:
        with open('.env.example', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    var_name = line.split('=')[0].strip()
                    env_vars.add(var_name)
    except FileNotFoundError:
        print("❌ .env.example not found")
        return False
    
    print(f"📋 Railway variables: {len(railway_vars)}")
    print(f"📋 Environment variables: {len(env_vars)}")
    
    # Check for overlapping core variables
    core_vars = ["PORT", "WEB_UI_HOST", "PYTHONUNBUFFERED", "DATA_DIR"]
    missing_in_railway = []
    missing_in_env = []
    
    for var in core_vars:
        if var not in railway_vars:
            missing_in_railway.append(var)
        if var not in env_vars:
            missing_in_env.append(var)
    
    if missing_in_railway:
        print(f"⚠️  Core variables missing in Railway: {missing_in_railway}")
    if missing_in_env:
        print(f"⚠️  Core variables missing in .env.example: {missing_in_env}")
    
    if not missing_in_railway and not missing_in_env:
        print("✅ Core variables are consistently defined")
    
    return len(missing_in_railway) == 0 and len(missing_in_env) == 0

if __name__ == "__main__":
    print("🔧 Gary-Zero Environment Variable Validator")
    print("=" * 45)
    
    env_ok = validate_environment_variables()
    compat_ok = check_deployment_compatibility()
    
    if env_ok and compat_ok:
        print("\n🎉 All environment variable checks passed!")
        sys.exit(0)
    else:
        print("\n❌ Some environment variable issues found")
        sys.exit(1)