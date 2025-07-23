#!/usr/bin/env python3
"""
Startup validation script for Railway deployment.

This script validates the configuration and templates during application startup
to ensure proper Railway deployment and catch issues early.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_startup_config():
    """
    Validate configuration during application startup.
    
    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
        from framework.helpers.config_loader import get_config_loader
        
        print("🔍 Validating Railway deployment configuration...")
        
        config_loader = get_config_loader()
        
        # Log startup configuration
        config_loader.log_startup_config()
        
        # Get full validation results
        validation = config_loader.validate_railway_config()
        
        # Report results
        if validation["valid"]:
            print("✅ Configuration validation passed!")
        else:
            print("❌ Configuration validation failed:")
            for issue in validation["issues"]:
                print(f"   - {issue}")
        
        # Report warnings
        if validation["warnings"]:
            print("⚠️  Configuration warnings:")
            for warning in validation["warnings"]:
                print(f"   - {warning}")
        
        return validation["valid"]
        
    except Exception as e:
        print(f"❌ Configuration validation error: {e}")
        logger.exception("Configuration validation failed")
        return False


def validate_template_rendering():
    """
    Validate that templates can be rendered without placeholders.
    
    Returns:
        bool: True if templates render correctly, False otherwise
    """
    try:
        from framework.helpers.template_helper import render_index_html
        
        print("🎨 Validating template rendering...")
        
        # Try to render the main template
        rendered_html = render_index_html()
        
        # Check for unresolved placeholders
        placeholder_patterns = ["{{version_no}}", "{{version_time}}", "{{feature_flags_config}}"]
        found_placeholders = []
        
        for pattern in placeholder_patterns:
            if pattern in rendered_html:
                found_placeholders.append(pattern)
        
        if found_placeholders:
            print(f"❌ Unresolved template placeholders: {found_placeholders}")
            return False
        
        # Check that feature flags JavaScript was injected
        if "<script>" not in rendered_html:
            print("❌ Feature flags JavaScript not found in rendered template")
            return False
        
        print("✅ Template rendering validation passed!")
        return True
        
    except Exception as e:
        print(f"❌ Template rendering validation error: {e}")
        logger.exception("Template rendering validation failed")
        return False


def validate_environment_variables():
    """
    Validate critical environment variables for Railway deployment.
    
    Returns:
        bool: True if environment variables are properly set, False otherwise
    """
    try:
        print("🌍 Validating environment variables...")
        
        # Critical variables for Railway
        critical_vars = {
            "PORT": os.getenv("PORT"),
            "WEB_UI_HOST": os.getenv("WEB_UI_HOST"),
            "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT")
        }
        
        issues = []
        
        for var, value in critical_vars.items():
            if not value:
                print(f"⚠️  {var} not set, will use default")
            elif value.startswith("${{") and value.endswith("}}"):
                issues.append(f"{var} contains unresolved Railway placeholder: {value}")
            elif var == "PORT" and value == "$PORT":
                issues.append(f"{var} contains literal '$PORT' string")
            else:
                print(f"✅ {var} = {value}")
        
        # Optional but important variables
        optional_vars = {
            "SEARXNG_URL": os.getenv("SEARXNG_URL"),
            "E2B_API_KEY": os.getenv("E2B_API_KEY"),
            "NIXPACKS_PYTHON_VERSION": os.getenv("NIXPACKS_PYTHON_VERSION")
        }
        
        for var, value in optional_vars.items():
            if value and (value.startswith("${{") and value.endswith("}}")):
                print(f"⚠️  {var} contains Railway placeholder: {value}")
            elif value:
                print(f"✅ {var} = {value}")
            else:
                print(f"ℹ️  {var} not set (optional)")
        
        if issues:
            print("❌ Environment variable issues found:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        
        print("✅ Environment variable validation passed!")
        return True
        
    except Exception as e:
        print(f"❌ Environment variable validation error: {e}")
        logger.exception("Environment variable validation failed")
        return False


def validate_health_endpoint():
    """Validate that health endpoint exists in code."""
    print("🔍 Validating health endpoint...")
    
    try:
        with open('run_ui.py', 'r') as f:
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


def validate_file_consistency():
    """
    Validate that Railway configuration files are consistent.
    
    Returns:
        bool: True if all files are consistent, False otherwise
    """
    try:
        print("📁 Validating Railway configuration consistency...")
        
        # Check startup command consistency
        files_to_check = {
            "railway.toml": "python start_uvicorn.py",
            "nixpacks.toml": "python start_uvicorn.py",
            "Procfile": "python start_uvicorn.py"
        }
        
        consistent = True
        
        for file_path, expected_command in files_to_check.items():
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                
                if expected_command in content:
                    print(f"✅ {file_path} uses consistent startup command")
                else:
                    print(f"❌ {file_path} startup command inconsistent")
                    consistent = False
            else:
                print(f"⚠️  {file_path} not found")
        
        if consistent:
            print("✅ Railway configuration consistency validation passed!")
        
        return consistent
        
    except Exception as e:
        print(f"❌ File consistency validation error: {e}")
        logger.exception("File consistency validation failed")
        return False


def main():
    """
    Run all startup validations.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    print(f"🚀 {APP_NAME} Railway Deployment Startup Validation")
    print("=" * 50)
    
    # Run all validations
    validations = [
        ("Configuration", validate_startup_config),
        ("Template Rendering", validate_template_rendering),
        ("Environment Variables", validate_environment_variables),
        ("Health Endpoint", validate_health_endpoint),
        ("File Consistency", validate_file_consistency)
    ]
    
    passed = 0
    total = len(validations)
    
    for name, validation_func in validations:
        print(f"\n📋 {name} Validation:")
        if validation_func():
            passed += 1
        else:
            print(f"❌ {name} validation failed!")
    
    print("\n" + "=" * 50)
    print(f"📊 Validation Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All startup validations passed!")
        print("🚀 Gary-Zero is ready for Railway deployment!")
        return 0
    else:
        print("❌ Some validations failed!")
        print("⚠️  Gary-Zero may not deploy correctly on Railway")
        print("💡 Check the issues above before deploying")
        return 1


if __name__ == "__main__":
    sys.exit(main())