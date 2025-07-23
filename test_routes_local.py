#!/usr/bin/env python3
"""Test routes locally to verify 405 fixes."""

import requests
import json
import time
import subprocess
import signal
import os
from urllib.parse import urljoin

def test_routes(base_url):
    """Test common routes and HTTP methods."""
    test_cases = [
        # Basic health endpoints
        {'path': '/health', 'method': 'GET', 'expected_status': [200]},
        {'path': '/health', 'method': 'OPTIONS', 'expected_status': [200, 204]},
        {'path': '/ready', 'method': 'GET', 'expected_status': [200]},
        {'path': '/ready', 'method': 'OPTIONS', 'expected_status': [200, 204]},
        
        # Root endpoint
        {'path': '/', 'method': 'GET', 'expected_status': [200, 302]},
        {'path': '/', 'method': 'POST', 'expected_status': [200, 201, 302]},
        {'path': '/', 'method': 'OPTIONS', 'expected_status': [200, 204]},
        
        # API endpoints
        {'path': '/api', 'method': 'GET', 'expected_status': [200, 404]},
        {'path': '/api', 'method': 'POST', 'expected_status': [200, 201, 404]},
        {'path': '/api', 'method': 'OPTIONS', 'expected_status': [200, 204]},
        
        # Debug routes
        {'path': '/debug/routes', 'method': 'GET', 'expected_status': [200, 404]},
        {'path': '/debug/routes', 'method': 'OPTIONS', 'expected_status': [200, 204]},
        
        # Metrics
        {'path': '/metrics', 'method': 'GET', 'expected_status': [200, 404]},
        {'path': '/metrics', 'method': 'OPTIONS', 'expected_status': [200, 204]},
        
        # Test 404 handling
        {'path': '/nonexistent', 'method': 'GET', 'expected_status': [404]},
        {'path': '/nonexistent', 'method': 'POST', 'expected_status': [404]},
    ]
    
    results = []
    
    for test in test_cases:
        url = urljoin(base_url, test['path'])
        try:
            if test['method'] == 'GET':
                response = requests.get(url, timeout=10)
            elif test['method'] == 'POST':
                # Test with JSON data
                response = requests.post(url, json={"message": "test"}, timeout=10)
            elif test['method'] == 'OPTIONS':
                response = requests.options(url, timeout=10)
            
            success = response.status_code in test['expected_status']
            status_icon = "✅" if success else "❌"
            
            results.append({
                'url': url,
                'method': test['method'],
                'status': response.status_code,
                'success': success,
                'expected': test['expected_status']
            })
            
            print(f"{status_icon} {test['method']:<7} {url:<30} - Status: {response.status_code}")
            
            # Show response for errors
            if not success and response.status_code not in [401, 403]:
                try:
                    if 'application/json' in response.headers.get('content-type', ''):
                        content = response.json()
                        print(f"    Response: {content}")
                    else:
                        print(f"    Response: {response.text[:100]}...")
                except:
                    print(f"    Response: {response.text[:100]}...")
            
        except Exception as e:
            results.append({
                'url': url,
                'method': test['method'],
                'error': str(e),
                'success': False
            })
            print(f"❌ {test['method']:<7} {url:<30} - Error: {e}")
    
    return results

def main():
    """Run route tests."""
    print("🧪 Testing Routes for 405 Method Not Allowed Fixes")
    print("=" * 60)
    
    # Test against FastAPI (main.py)
    fastapi_url = "http://localhost:8000"
    print(f"\n🚀 Testing FastAPI routes at: {fastapi_url}")
    
    try:
        # Quick check if server is running
        response = requests.get(f"{fastapi_url}/health", timeout=5)
        print(f"✅ Server is responding (status: {response.status_code})")
        
        results = test_routes(fastapi_url)
        
        # Summary
        successful = sum(1 for r in results if r.get('success', False))
        total = len(results)
        
        print(f"\n📊 Results: {successful}/{total} tests passed")
        
        # Show failures
        failures = [r for r in results if not r.get('success', False)]
        if failures:
            print(f"\n❌ {len(failures)} Failed Tests:")
            for failure in failures:
                if 'error' in failure:
                    print(f"  - {failure['method']} {failure['url']}: {failure['error']}")
                else:
                    print(f"  - {failure['method']} {failure['url']}: Status {failure['status']} (expected {failure['expected']})")
        
        return successful == total
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {fastapi_url}")
        print("💡 Make sure the server is running with: python main.py")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)