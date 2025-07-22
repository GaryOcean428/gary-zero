#!/usr/bin/env python3
"""
Railway Configuration Verification Script
Validates all aspects of the Railway build timeout and retry implementation
"""

import os
import subprocess
import sys

import toml


def check_railway_toml():
    """Verify railway.toml configuration"""
    print("🔧 Checking railway.toml configuration...")

    try:
        with open('railway.toml') as f:
            config = toml.load(f)

        build_config = config.get('build', {})
        deploy_config = config.get('deploy', {})

        # Check build configuration
        timeout = build_config.get('timeout')
        retries = build_config.get('retries')
        build_command = build_config.get('buildCommand', '')

        print(f"  ⏱️  Build Timeout: {timeout}s ({timeout/60:.1f} minutes)")
        print(f"  🔄 Build Retries: {retries}")
        print(f"  📦 Build Command: {build_command}")

        # Check deploy configuration
        restart_retries = deploy_config.get('restartPolicyMaxRetries')
        restart_policy = deploy_config.get('restartPolicyType')
        replicas = deploy_config.get('replicas')

        print(f"  🚀 Deploy Restart Policy: {restart_policy}")
        print(f"  🔁 Deploy Max Retries: {restart_retries}")
        print(f"  📊 Replicas: {replicas}")

        # Validate requirements
        issues = []
        if timeout != 1800:
            issues.append(f"❌ Build timeout should be 1800s, got {timeout}s")
        if retries != 3:
            issues.append(f"❌ Build retries should be 3, got {retries}")
        if 'uv sync --locked' not in build_command:
            issues.append("❌ Build command should use 'uv sync --locked'")
        if restart_retries != 3:
            issues.append(f"❌ Restart retries should be 3, got {restart_retries}")
        if replicas != 1:
            issues.append(f"❌ Replicas should be 1, got {replicas}")

        if issues:
            for issue in issues:
                print(f"  {issue}")
            return False
        else:
            print("  ✅ Railway configuration is correct!")
            return True

    except Exception as e:
        print(f"  ❌ Error reading railway.toml: {e}")
        return False

def check_dockerfile():
    """Verify Dockerfile optimizations"""
    print("\n🐳 Checking Dockerfile optimizations...")

    try:
        with open('Dockerfile') as f:
            dockerfile_content = f.read()

        # Check for UV environment variables
        uv_vars = [
            'UV_CACHE_DIR=/root/.cache/uv',
            'PIP_CACHE_DIR=/root/.cache/pip',
            'UV_COMPILE_BYTECODE=1',
            'UV_NO_SYNC=1'
        ]

        missing_vars = []
        for var in uv_vars:
            if var not in dockerfile_content:
                missing_vars.append(var)

        if missing_vars:
            print(f"  ❌ Missing UV environment variables: {missing_vars}")
            return False
        else:
            print("  ✅ UV environment variables configured")

        # Check for cache mounts
        if '--mount=type=cache,target=/root/.cache/uv' in dockerfile_content:
            print("  ✅ UV cache mount configured")
        else:
            print("  ❌ UV cache mount missing")
            return False

        # Check for UV usage
        if 'uv sync' in dockerfile_content:
            print("  ✅ UV sync command found")
        else:
            print("  ❌ UV sync command missing")
            return False

        # Check for fallback mechanism
        if 'pip install --no-cache-dir -r requirements.txt' in dockerfile_content:
            print("  ✅ Fallback to pip configured")
        else:
            print("  ❌ Fallback mechanism missing")
            return False

        return True

    except Exception as e:
        print(f"  ❌ Error reading Dockerfile: {e}")
        return False

def check_build_monitor():
    """Verify build monitor script"""
    print("\n📊 Checking build monitor script...")

    if not os.path.exists('scripts/build_monitor.py'):
        print("  ❌ Build monitor script missing")
        return False

    try:
        # Test the script's check functionality
        result = subprocess.run(
            ['python', 'scripts/build_monitor.py', '--check-only'],
            capture_output=True, text=True, timeout=30
        )

        if 'Railway timeout and retry configuration looks good' in result.stdout:
            print("  ✅ Build monitor validates Railway config")
        else:
            print("  ⚠️  Build monitor configuration check issues")

        if 'UV not found in PATH' in result.stdout:
            print("  ⚠️  UV not available (expected in some environments)")

        if os.access('scripts/build_monitor.py', os.X_OK):
            print("  ✅ Build monitor script is executable")
        else:
            print("  ❌ Build monitor script not executable")
            return False

        return True

    except Exception as e:
        print(f"  ❌ Error testing build monitor: {e}")
        return False

def check_files_exist():
    """Check that all required files exist"""
    print("\n📁 Checking required files...")

    required_files = [
        'railway.toml',
        'Dockerfile',
        'requirements.txt',
        'uv.lock',
        'scripts/build_monitor.py'
    ]

    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} missing")
            missing_files.append(file_path)

    return len(missing_files) == 0

def main():
    """Run all verification checks"""
    print("🚀 Railway Build Configuration Verification")
    print("=" * 50)

    checks = [
        ("Required Files", check_files_exist),
        ("Railway TOML", check_railway_toml),
        ("Dockerfile", check_dockerfile),
        ("Build Monitor", check_build_monitor)
    ]

    results = []
    for name, check_func in checks:
        result = check_func()
        results.append((name, result))

    print("\n" + "=" * 50)
    print("📋 Verification Summary:")

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 All verification checks passed!")
        print("Railway build timeout and retry mechanisms are properly configured.")
        return 0
    else:
        print("\n⚠️  Some verification checks failed.")
        print("Please review the issues above before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
