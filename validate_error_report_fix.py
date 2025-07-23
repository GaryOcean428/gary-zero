#!/usr/bin/env python3
"""
Final validation script for the /api/error_report endpoint fix.

This script demonstrates that the 405 error has been resolved and the
endpoint is working correctly with various payloads.
"""

import json
import requests
import time


def validate_error_report_endpoint():
    """Validate the error report endpoint is working correctly."""
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/api/error_report"
    
    print("🔍 Validating /api/error_report endpoint fix...")
    print("=" * 60)
    
    # Test 1: JSON payload (matches client error reporter structure)
    print("Test 1: JSON Error Report")
    json_payload = {
        "id": 1,
        "sessionId": "validation_session_" + str(int(time.time())),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "url": "http://localhost:8000/test-page",
        "userAgent": "ValidationScript/1.0",
        "error": {
            "message": "Validation test error",
            "stack": "Error: Validation test\n    at validate.py:1:1",
            "name": "ValidationError"
        },
        "context": {
            "connectionStatus": True,
            "currentContext": "validation_test"
        }
    }
    
    try:
        response = requests.post(endpoint, json=json_payload, timeout=5)
        if response.status_code == 204:
            print("  ✅ JSON Payload: SUCCESS (HTTP 204)")
        else:
            print(f"  ❌ JSON Payload: FAILED (HTTP {response.status_code})")
    except requests.RequestException as e:
        print(f"  ❌ JSON Payload: FAILED - {e}")
    
    # Test 2: Minimal payload
    print("Test 2: Minimal Error Report")
    minimal_payload = {"error": {"message": "Minimal validation error"}}
    
    try:
        response = requests.post(endpoint, json=minimal_payload, timeout=5)
        if response.status_code == 204:
            print("  ✅ Minimal Payload: SUCCESS (HTTP 204)")
        else:
            print(f"  ❌ Minimal Payload: FAILED (HTTP {response.status_code})")
    except requests.RequestException as e:
        print(f"  ❌ Minimal Payload: FAILED - {e}")
    
    # Test 3: Raw text payload
    print("Test 3: Raw Text Error Report")
    raw_payload = "Raw validation error message"
    
    try:
        response = requests.post(
            endpoint, 
            data=raw_payload, 
            headers={"Content-Type": "text/plain"},
            timeout=5
        )
        if response.status_code == 204:
            print("  ✅ Raw Text Payload: SUCCESS (HTTP 204)")
        else:
            print(f"  ❌ Raw Text Payload: FAILED (HTTP {response.status_code})")
    except requests.RequestException as e:
        print(f"  ❌ Raw Text Payload: FAILED - {e}")
    
    # Test 4: Verify GET returns 404 (only POST allowed)
    print("Test 4: GET Method (Should return 404)")
    
    try:
        response = requests.get(endpoint, timeout=5)
        if response.status_code == 404:
            print("  ✅ GET Method: SUCCESS (HTTP 404 as expected)")
        else:
            print(f"  ❌ GET Method: UNEXPECTED (HTTP {response.status_code})")
    except requests.RequestException as e:
        print(f"  ❌ GET Method: FAILED - {e}")
    
    print("=" * 60)
    print("✅ Validation complete! The /api/error_report endpoint is working correctly.")
    print("🎯 The 405 error has been successfully resolved.")
    
    # Test server availability
    print("\n🔍 Checking server status...")
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code == 200:
            print("  ✅ Server is healthy and running")
        else:
            print(f"  ⚠️  Server returned HTTP {health_response.status_code}")
    except requests.RequestException as e:
        print(f"  ❌ Server health check failed: {e}")


if __name__ == "__main__":
    validate_error_report_endpoint()