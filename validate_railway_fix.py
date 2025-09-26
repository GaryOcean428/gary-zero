#!/usr/bin/env python3
"""
Railway Deployment Fix Validation
Validates that the critical Railway deployment fixes are properly implemented.
"""

import json
import os
import subprocess
from pathlib import Path


def check_railway_toml():
    """Verify railway.toml forces RAILPACK builder."""
    print("🚂 Railway TOML Configuration")
    
    if not Path("railway.toml").exists():
        print("  ❌ railway.toml missing")
        return False
    
    with open("railway.toml") as f:
        content = f.read()
    
    if 'builder = "RAILPACK"' in content:
        print("  ✅ Forces RAILPACK builder (overrides Nixpacks)")
    else:
        print("  ❌ RAILPACK builder not configured")
        return False
    
    if "startCommand" in content:
        print("  ✅ Start command configured")
    else:
        print("  ❌ Start command not configured")
        return False
        
    return True


def check_railpack_json():
    """Verify railpack.json is properly configured for multi-provider."""
    print("\n📦 Railpack JSON Configuration")
    
    if not Path("railpack.json").exists():
        print("  ❌ railpack.json missing")
        return False
    
    try:
        with open("railpack.json") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  ❌ Invalid JSON: {e}")
        return False
    
    print("  ✅ Valid JSON syntax")
    
    # Check provider
    provider = config.get("provider")
    if provider == "multi":
        print("  ✅ Multi-provider configured (Node + Python)")
    else:
        print(f"  ❌ Provider is '{provider}', should be 'multi'")
        return False
    
    # Check packages
    packages = config.get("packages", {})
    if "node" in packages and "python" in packages:
        print(f"  ✅ Both Node ({packages['node']}) and Python ({packages['python']}) specified")
    else:
        print("  ❌ Missing Node or Python packages")
        return False
    
    # Check start command
    start_cmd = config.get("deploy", {}).get("startCommand")
    if start_cmd == "bash scripts/start.sh":
        print("  ✅ Start command uses bash scripts/start.sh")
    else:
        print(f"  ❌ Start command is '{start_cmd}', should be 'bash scripts/start.sh'")
        return False
    
    # Check Python verification commands
    setup_commands = config.get("steps", {}).get("setup-directories", {}).get("commands", [])
    python_check_found = any("python3" in cmd for cmd in setup_commands)
    if python_check_found:
        print("  ✅ Python verification commands added")
    else:
        print("  ❌ Missing Python verification commands")
        return False
    
    return True


def check_start_script():
    """Verify scripts/start.sh exists and handles Python properly."""
    print("\n🚀 Start Script Validation")
    
    script_path = Path("scripts/start.sh")
    if not script_path.exists():
        print("  ❌ scripts/start.sh missing")
        return False
    
    if not os.access(script_path, os.X_OK):
        print("  ❌ scripts/start.sh not executable")
        return False
    
    print("  ✅ scripts/start.sh exists and is executable")
    
    with open(script_path) as f:
        content = f.read()
    
    # Check Python dependency
    if "command -v uvicorn" in content:
        print("  ✅ Checks for uvicorn availability")
    else:
        print("  ❌ Missing uvicorn availability check")
        return False
    
    if "python start_uvicorn.py" in content:
        print("  ✅ Uses Python startup script")
    else:
        print("  ❌ Missing Python startup script invocation")
        return False
    
    return True


def check_no_conflicting_configs():
    """Ensure no conflicting build configurations exist."""
    print("\n🔍 Conflicting Configuration Check")
    
    conflicting_files = ["Dockerfile", "nixpacks.toml"]
    conflicts = []
    
    for filename in conflicting_files:
        if Path(filename).exists():
            conflicts.append(filename)
    
    if conflicts:
        print(f"  ⚠️  Found potential conflicts: {', '.join(conflicts)}")
        print("     These may override railway.toml - consider removing if causing issues")
        return True  # Not a hard failure, just a warning
    else:
        print("  ✅ No conflicting build configurations found")
        return True


def main():
    """Run all validation checks."""
    print("🔧 Railway Deployment Fix Validation")
    print("=" * 40)
    
    checks = [
        ("Railway TOML", check_railway_toml),
        ("Railpack JSON", check_railpack_json),
        ("Start Script", check_start_script),
        ("Conflicting Configs", check_no_conflicting_configs),
    ]
    
    all_passed = True
    for name, check_func in checks:
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 ALL VALIDATION CHECKS PASSED!")
        print("   Railway deployment fix is ready.")
        print("   Expected outcome:")
        print("   - Railway uses RAILPACK builder (not Nixpacks)")
        print("   - Container has both Node and Python runtimes")
        print("   - Python/uvicorn available for startup")
        print("   - /api/health endpoint should respond 200 OK")
        return 0
    else:
        print("❌ SOME VALIDATION CHECKS FAILED!")
        print("   Please fix the issues above before deploying.")
        return 1


if __name__ == "__main__":
    exit(main())