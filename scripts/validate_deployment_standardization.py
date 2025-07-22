#!/usr/bin/env python3
"""
Final validation script for gary-zero Railway deployment standardization.
Validates all acceptance criteria from the issue.
"""

import os
import sys
import subprocess

def check_file_exists(filepath, description):
    """Check if a file exists and is readable."""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - NOT FOUND")
        return False

def check_railway_config():
    """Validate Railway configuration meets requirements."""
    print("\n🚂 Railway Configuration Validation")
    print("=" * 40)
    
    if not check_file_exists("railway.toml", "Railway configuration"):
        return False
    
    with open("railway.toml", "r") as f:
        content = f.read()
    
    checks = [
        ("Railpack builder", 'builder = "railpack"' in content),
        ("Build command", "./scripts/build.sh" in content),
        ("Start command", "./scripts/start.sh" in content),
        ("Health check path", 'healthcheckPath = "/health"' in content),
        ("Health check timeout", "healthcheckTimeout" in content),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed

def check_build_start_scripts():
    """Validate standardized build and start scripts."""
    print("\n🔧 Build/Start Scripts Validation")
    print("=" * 35)
    
    scripts = [
        ("scripts/build.sh", "Standardized build script"),
        ("scripts/start.sh", "Standardized start script")
    ]
    
    all_exist = True
    for script_path, description in scripts:
        if check_file_exists(script_path, description):
            # Check if executable
            if os.access(script_path, os.X_OK):
                print(f"    → Executable: ✅")
            else:
                print(f"    → Executable: ❌")
                all_exist = False
        else:
            all_exist = False
    
    return all_exist

def check_health_endpoint():
    """Validate health endpoint implementation."""
    print("\n🏥 Health Endpoint Validation")
    print("=" * 30)
    
    if not check_file_exists("main.py", "Main application"):
        return False
    
    with open("main.py", "r") as f:
        content = f.read()
    
    checks = [
        ("Health route defined", '@app.get("/health"' in content),
        ("HealthResponse model", "class HealthResponse" in content),
        ("Health check function", "async def health_check" in content),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed

def check_github_actions():
    """Validate GitHub Actions workflow."""
    print("\n⚡ GitHub Actions Workflow Validation")
    print("=" * 40)
    
    workflow_path = ".github/workflows/railway-deployment.yml"
    if not check_file_exists(workflow_path, "Railway deployment workflow"):
        return False
    
    with open(workflow_path, "r") as f:
        content = f.read()
    
    checks = [
        ("Railway validation job", "railway-validation:" in content),
        ("Docker test job", "docker-test:" in content),
        ("Build script test", "scripts/build.sh" in content),
        ("Start script test", "scripts/start.sh" in content),
        ("Health endpoint test", "/health" in content),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed

def check_docker_compatibility():
    """Validate Docker deployment compatibility."""
    print("\n🐳 Docker Compatibility Validation")
    print("=" * 35)
    
    docker_files = [
        ("Dockerfile", "Docker configuration"),
        ("docker-entrypoint.sh", "Docker entrypoint script"),
        ("wsgi.py", "WSGI application entry point"),
    ]
    
    all_exist = True
    for file_path, description in docker_files:
        if not check_file_exists(file_path, description):
            all_exist = False
    
    # Check that Docker uses separate entry point (maintains compatibility)
    if os.path.exists("Dockerfile"):
        with open("Dockerfile", "r") as f:
            content = f.read()
        if "docker-entrypoint.sh" in content:
            print("  ✅ Docker uses separate entrypoint (maintains compatibility)")
        else:
            print("  ❌ Docker entrypoint not found in Dockerfile")
            all_exist = False
    
    return all_exist

def check_environment_variables():
    """Validate environment variable standardization."""
    print("\n⚙️  Environment Variables Validation")
    print("=" * 37)
    
    # Run the environment validation script
    try:
        result = subprocess.run([
            sys.executable, "scripts/validate_env_standardization.py"
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("  ✅ Environment variable standardization passed")
            return True
        else:
            print("  ❌ Environment variable standardization failed")
            print("    Error output:")
            for line in result.stdout.split('\n')[-5:]:
                if line.strip():
                    print(f"    {line}")
            return False
    except Exception as e:
        print(f"  ❌ Failed to run environment validation: {e}")
        return False

def main():
    """Run all validation checks."""
    print("🔍 Gary-Zero Railway Deployment Standardization Validation")
    print("=" * 60)
    print()
    
    # Track all validation results
    validations = [
        ("Railway configuration", check_railway_config),
        ("Build/Start scripts", check_build_start_scripts),
        ("Health endpoint", check_health_endpoint),
        ("GitHub Actions workflow", check_github_actions),
        ("Docker compatibility", check_docker_compatibility),
        ("Environment variables", check_environment_variables),
    ]
    
    results = []
    for validation_name, validation_func in validations:
        try:
            result = validation_func()
            results.append((validation_name, result))
        except Exception as e:
            print(f"❌ {validation_name} validation failed with error: {e}")
            results.append((validation_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for validation_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} {validation_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("   Gary-Zero deployment standardization is complete.")
        print("   Both Railway and Docker deployments are ready.")
        return 0
    else:
        print("❌ SOME VALIDATIONS FAILED!")
        print("   Please review the failed checks above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())