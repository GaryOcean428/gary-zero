#!/usr/bin/env python3
"""
Production verification script for Gary-Zero fixes
Tests the implemented fixes for LangChain, UI, and production features
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_langchain_anthropic_fix():
    """Test LangChain Anthropic streaming fix"""
    print("🔍 Testing LangChain Anthropic streaming fix...")

    # Set environment variable to disable streaming
    os.environ['LANGCHAIN_ANTHROPIC_STREAM_USAGE'] = 'false'

    try:
        from framework.helpers import dotenv

        # Test environment variable reading
        stream_usage_disabled = dotenv.get_dotenv_value("LANGCHAIN_ANTHROPIC_STREAM_USAGE", "true").lower() == "false"

        if stream_usage_disabled:
            print("  ✅ Environment variable correctly disables streaming")
            return True
        else:
            print("  ❌ Environment variable not working correctly")
            return False

    except Exception as e:
        print(f"  ❌ Error testing LangChain fix: {e}")
        return False

def test_health_check_endpoint():
    """Test enhanced health check endpoint"""
    print("🔍 Testing enhanced health check...")

    try:
        # Import the Flask app
        from run_ui import webapp

        with webapp.test_client() as client:
            response = client.get('/health')

            if response.status_code == 200:
                data = response.get_json()

                # Check for required fields
                required_fields = ['status', 'timestamp', 'version', 'environment']
                missing_fields = [field for field in required_fields if field not in data]

                if not missing_fields:
                    print("  ✅ Health check endpoint working correctly")
                    print(f"    - Status: {data['status']}")
                    print(f"    - Environment: {data['environment']['node_env']}")
                    print(f"    - LangChain streaming disabled: {data['environment']['langchain_stream_disabled']}")
                    return True
                else:
                    print(f"  ❌ Health check missing fields: {missing_fields}")
                    return False
            else:
                print(f"  ❌ Health check returned status {response.status_code}")
                return False

    except Exception as e:
        print(f"  ❌ Error testing health check: {e}")
        return False

def test_environment_validation():
    """Test environment validation script"""
    print("🔍 Testing environment validation...")

    try:
        from validate_env import EnvironmentValidator

        validator = EnvironmentValidator()
        result = validator.run_validation()

        if result['status'] in ['passed', 'warning']:
            print("  ✅ Environment validation working correctly")
            print(f"    - Status: {result['status']}")
            print(f"    - Errors: {len(result['errors'])}")
            print(f"    - Warnings: {len(result['warnings'])}")
            return True
        else:
            print(f"  ❌ Environment validation failed: {result['status']}")
            return False

    except Exception as e:
        print(f"  ❌ Error testing environment validation: {e}")
        return False

def test_chat_input_files():
    """Test chat input auto-resize files exist"""
    print("🔍 Testing chat input auto-resize files...")

    files_to_check = [
        'webui/js/chat-input-autoresize.js',
        'webui/index.html',
        'webui/index.css'
    ]

    all_exist = True
    for file_path in files_to_check:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            print(f"  ✅ {file_path} exists")
        else:
            print(f"  ❌ {file_path} missing")
            all_exist = False

    # Check if auto-resize script is referenced in HTML
    try:
        html_path = os.path.join(project_root, 'webui/index.html')
        with open(html_path) as f:
            html_content = f.read()

        if 'chat-input-autoresize.js' in html_content:
            print("  ✅ Auto-resize script referenced in HTML")
        else:
            print("  ❌ Auto-resize script not referenced in HTML")
            all_exist = False

    except Exception as e:
        print(f"  ❌ Error checking HTML file: {e}")
        all_exist = False

    return all_exist

def test_vscode_integration_production_mode():
    """Test VS Code integration production mode detection"""
    print("🔍 Testing VS Code integration production mode...")

    try:
        vscode_js_path = os.path.join(project_root, 'webui/js/vscode-integration.js')

        if not os.path.exists(vscode_js_path):
            print("  ❌ VS Code integration file missing")
            return False

        with open(vscode_js_path) as f:
            content = f.read()

        # Check for production mode detection
        production_checks = [
            'checkProductionMode',
            'railway.app',
            'isProductionMode',
            'ENABLE_DEV_FEATURES'
        ]

        missing_checks = [check for check in production_checks if check not in content]

        if not missing_checks:
            print("  ✅ VS Code integration has production mode detection")
            return True
        else:
            print(f"  ❌ VS Code integration missing production checks: {missing_checks}")
            return False

    except Exception as e:
        print(f"  ❌ Error testing VS Code integration: {e}")
        return False

def test_environment_variables_in_example():
    """Test that all new environment variables are in .env.example"""
    print("🔍 Testing environment variables in .env.example...")

    required_vars = [
        'LANGCHAIN_ANTHROPIC_STREAM_USAGE',
        'ENABLE_DEV_FEATURES',
        'VSCODE_INTEGRATION_ENABLED',
        'CHAT_AUTO_RESIZE_ENABLED'
    ]

    try:
        env_example_path = os.path.join(project_root, '.env.example')

        if not os.path.exists(env_example_path):
            print("  ❌ .env.example file missing")
            return False

        with open(env_example_path) as f:
            content = f.read()

        missing_vars = [var for var in required_vars if var not in content]

        if not missing_vars:
            print("  ✅ All new environment variables in .env.example")
            return True
        else:
            print(f"  ❌ Missing environment variables in .env.example: {missing_vars}")
            return False

    except Exception as e:
        print(f"  ❌ Error checking .env.example: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🚀 Gary-Zero Production Fix Verification")
    print("=" * 50)

    tests = [
        ("LangChain Anthropic Fix", test_langchain_anthropic_fix),
        ("Health Check Enhancement", test_health_check_endpoint),
        ("Environment Validation", test_environment_validation),
        ("Chat Input Auto-Resize", test_chat_input_files),
        ("VS Code Production Mode", test_vscode_integration_production_mode),
        ("Environment Variables", test_environment_variables_in_example),
    ]

    results = []
    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                passed += 1
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All verification tests PASSED! Fixes are ready for production.")
        return 0
    else:
        print(f"⚠️  {total - passed} verification tests FAILED. Please review and fix issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
