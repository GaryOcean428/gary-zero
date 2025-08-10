#!/usr/bin/env python3
"""Validation script for gary-zero Railpack configuration."""

import json
import os
import sys
import importlib.util
from pathlib import Path

def validate_railpack_config():
    """Validate railpack.json configuration."""
    print("🔍 Validating Railpack configuration...")
    
    railpack_path = Path("railpack.json")
    if not railpack_path.exists():
        print("❌ railpack.json not found")
        return False
    
    try:
        with open(railpack_path) as f:
            config = json.load(f)
        
        # Check required fields
        required_fields = ["provider", "packages", "steps", "deploy"]
        for field in required_fields:
            if field not in config:
                print(f"❌ Missing required field: {field}")
                return False
        
        print("✅ railpack.json is valid")
        print(f"  Provider: {config.get('provider')}")
        print(f"  Python version: {config.get('packages', {}).get('python')}")
        print(f"  Node version: {config.get('packages', {}).get('node')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading railpack.json: {e}")
        return False

def validate_dependencies():
    """Validate critical dependencies are available."""
    print("📦 Validating critical dependencies...")
    
    critical_modules = [
        ("flask", "Web framework"),
        ("gunicorn", "WSGI server"),
        ("uvicorn", "ASGI server"),
        ("watchdog", "File monitoring")
    ]
    
    all_available = True
    for module_name, description in critical_modules:
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is not None:
                print(f"✅ {module_name} ({description})")
            else:
                print(f"⚠️ {module_name} ({description}) - Not found")
                all_available = False
        except Exception as e:
            print(f"❌ {module_name} ({description}) - Error: {e}")
            all_available = False
    
    return all_available

def validate_service_config():
    """Validate service configuration."""
    print("🌐 Validating service configuration...")
    
    try:
        import service_config
        print("✅ service_config module loads successfully")
        
        # Test service URL configuration
        urls = service_config.get_service_urls()
        print(f"  Redis URL: {urls.get('redis', 'Not configured')}")
        print(f"  Postgres URL: {urls.get('postgres', 'Not configured')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Service configuration error: {e}")
        return False

def validate_yarn_config():
    """Validate Yarn configuration."""
    print("🧶 Validating Yarn configuration...")
    
    # Check .yarnrc.yml exists
    if not Path(".yarnrc.yml").exists():
        print("⚠️ .yarnrc.yml not found")
        return False
    
    # Check yarn.lock exists
    if not Path("yarn.lock").exists():
        print("⚠️ yarn.lock not found")
        return False
    
    # Check package-lock.json is removed
    if Path("package-lock.json").exists():
        print("⚠️ package-lock.json should be removed for Yarn-only usage")
        return False
    
    print("✅ Yarn configuration is valid")
    return True

def validate_files():
    """Validate required files exist."""
    print("📁 Validating required files...")
    
    required_files = [
        ("railpack.json", "Railpack configuration"),
        ("package.json", "Node.js configuration"),
        ("requirements.txt", "Python dependencies"),
        ("scripts/start.sh", "Startup script"),
        ("scripts/build.sh", "Build script"),
        ("service_config.py", "Service configuration")
    ]
    
    all_present = True
    for file_path, description in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} ({description})")
        else:
            print(f"❌ {file_path} ({description}) - Missing")
            all_present = False
    
    return all_present

def main():
    """Run all validations."""
    print("🚀 Gary-Zero Railpack Configuration Validator")
    print("=" * 50)
    
    validations = [
        ("Configuration", validate_railpack_config),
        ("Files", validate_files),
        ("Yarn Setup", validate_yarn_config),
        ("Dependencies", validate_dependencies),
        ("Service Config", validate_service_config)
    ]
    
    results = {}
    for name, validator in validations:
        print(f"\n{name}:")
        results[name] = validator()
    
    print("\n" + "=" * 50)
    print("📊 Validation Summary:")
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All validations passed! Ready for Railpack deployment.")
        return 0
    else:
        print("\n⚠️ Some validations failed. Please review and fix issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())