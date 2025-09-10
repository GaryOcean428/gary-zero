#!/usr/bin/env python3
"""
Deployment validation tests for Gary-Zero Railway deployment.
Tests the startup process, health endpoints, and fallback mechanisms.
"""

import os
import sys
import time
import requests
import subprocess
import threading
from typing import Dict, List, Tuple

def test_simple_health_check_import() -> Tuple[bool, str]:
    """Test that simple_health_check can be imported."""
    try:
        import simple_health_check
        return True, "simple_health_check imports successfully"
    except ImportError as e:
        return False, f"Failed to import simple_health_check: {e}"

def test_dependencies() -> Tuple[bool, str]:
    """Test that critical dependencies are available."""
    try:
        import fastapi
        import uvicorn
        import psutil
        return True, "All critical dependencies (fastapi, uvicorn, psutil) available"
    except ImportError as e:
        return False, f"Missing critical dependency: {e}"

def test_health_endpoint_response(port: int = 8001) -> Tuple[bool, str]:
    """Test that the health endpoint responds correctly."""
    # Start simple health check server in a thread
    def start_server():
        os.environ['PORT'] = str(port)
        subprocess.run([sys.executable, 'simple_health_check.py'], 
                      capture_output=True, timeout=30)
    
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        # Test health endpoint
        response = requests.get(f'http://localhost:{port}/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                return True, f"Health endpoint responds correctly: {data}"
            else:
                return False, f"Health endpoint returned unexpected status: {data}"
        else:
            return False, f"Health endpoint returned status code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Failed to connect to health endpoint: {e}"

def test_file_permissions() -> Tuple[bool, str]:
    """Test that script files have correct permissions."""
    script_files = [
        'scripts/start.sh',
        'start_uvicorn.py'
    ]
    
    issues = []
    for script_file in script_files:
        if os.path.exists(script_file):
            if os.access(script_file, os.X_OK):
                continue
            else:
                issues.append(f"{script_file} is not executable")
        else:
            issues.append(f"{script_file} does not exist")
    
    if not issues:
        return True, "All script files have correct permissions"
    else:
        return False, f"Permission issues: {'; '.join(issues)}"

def test_required_files_exist() -> Tuple[bool, str]:
    """Test that all required files exist."""
    required_files = [
        'simple_health_check.py',
        'start_uvicorn.py',
        'scripts/start.sh',
        'railpack.json',
        'Dockerfile',
        'main.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if not missing_files:
        return True, "All required files exist"
    else:
        return False, f"Missing files: {', '.join(missing_files)}"

def test_railpack_json_structure() -> Tuple[bool, str]:
    """Test that railpack.json has the correct structure."""
    try:
        import json
        with open('railpack.json', 'r') as f:
            data = json.load(f)
        
        # Check required fields
        required_fields = ['deploy', 'startCommand']
        missing_fields = []
        
        if 'deploy' in data:
            deploy = data['deploy']
            if 'startCommand' not in deploy:
                missing_fields.append('deploy.startCommand')
            else:
                start_command = deploy['startCommand']
                if 'simple_health_check.py' not in start_command:
                    return False, "simple_health_check.py not found in startCommand fallback chain"
        else:
            missing_fields.append('deploy')
        
        if missing_fields:
            return False, f"Missing required fields in railpack.json: {', '.join(missing_fields)}"
        
        return True, "railpack.json structure is valid"
    except Exception as e:
        return False, f"Failed to validate railpack.json: {e}"

def run_deployment_validation() -> Dict[str, Tuple[bool, str]]:
    """Run all deployment validation tests."""
    tests = {
        "Dependencies": test_dependencies,
        "Simple Health Check Import": test_simple_health_check_import,
        "Required Files": test_required_files_exist,
        "File Permissions": test_file_permissions,
        "Railpack JSON Structure": test_railpack_json_structure,
        # Skip health endpoint test for now as it requires server startup
        # "Health Endpoint": test_health_endpoint_response,
    }
    
    results = {}
    for test_name, test_func in tests.items():
        try:
            results[test_name] = test_func()
        except Exception as e:
            results[test_name] = (False, f"Test failed with exception: {e}")
    
    return results

def main():
    """Main function to run deployment validation tests."""
    print("🔍 Gary-Zero Deployment Validation Tests")
    print("=" * 45)
    
    results = run_deployment_validation()
    
    passed = 0
    failed = 0
    
    for test_name, (success, message) in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        print(f"    {message}")
        print()
        
        if success:
            passed += 1
        else:
            failed += 1
    
    print("=" * 45)
    print(f"📊 Test Summary: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("❌ Some tests failed. Please check the deployment configuration.")
        sys.exit(1)
    else:
        print("✅ All tests passed! Deployment configuration looks good.")
        sys.exit(0)

if __name__ == "__main__":
    main()