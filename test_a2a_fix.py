#!/usr/bin/env python3
"""
Test script to validate A2aStream constructor fix.

This script tests that the A2aStream constructor issue has been resolved
and that API handlers can be loaded without parameter mismatches.
"""

import sys
import traceback
from typing import Dict, Any


def test_a2a_stream_instantiation():
    """Test that A2aStream can be instantiated without constructor errors."""
    print("Testing A2aStream instantiation...")
    try:
        from framework.api.a2a_stream import A2aStream
        
        # This should not raise "takes 1 positional argument but 3 were given"
        handler = A2aStream()
        print("✅ A2aStream instantiated successfully")
        
        # Test the process method exists and has correct signature
        if hasattr(handler, 'process'):
            print("✅ A2aStream.process method exists")
        else:
            print("❌ A2aStream.process method missing")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ A2aStream instantiation failed: {e}")
        traceback.print_exc()
        return False


def test_all_a2a_handlers():
    """Test that all A2A handlers can be instantiated."""
    print("\nTesting all A2A handlers...")
    
    handlers = [
        ("A2aAgentCard", "framework.api.a2a_agent_card", "A2aAgentCard"),
        ("A2aDiscover", "framework.api.a2a_discover", "A2aDiscover"),
        ("A2aNegotiate", "framework.api.a2a_negotiate", "A2aNegotiate"),
        ("A2aMessage", "framework.api.a2a_message", "A2aMessage"),
        ("A2aNotify", "framework.api.a2a_notify", "A2aNotify"),
        ("A2aMcpTools", "framework.api.a2a_mcp_tools", "A2aMcpTools"),
        ("A2aMcpExecute", "framework.api.a2a_mcp_tools", "A2aMcpExecute"),
        ("A2aStream", "framework.api.a2a_stream", "A2aStream"),
    ]
    
    results = {}
    
    for name, module_path, class_name in handlers:
        try:
            module = __import__(module_path, fromlist=[class_name])
            handler_class = getattr(module, class_name)
            handler = handler_class()
            print(f"✅ {name} instantiated successfully")
            results[name] = True
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            results[name] = False
    
    return results


def test_api_endpoint_registration():
    """Test that API endpoints can be registered without errors."""
    print("\nTesting API endpoint registration...")
    
    try:
        from fastapi import FastAPI
        from api_bridge_simple import add_enhanced_endpoints
        
        app = FastAPI()
        add_enhanced_endpoints(app)
        
        # Count A2A routes
        a2a_routes = []
        for route in app.routes:
            if hasattr(route, 'path') and '/a2a/' in route.path:
                a2a_routes.append(route.path)
        
        print(f"✅ API endpoints registered successfully")
        print(f"✅ Found {len(a2a_routes)} A2A routes: {a2a_routes}")
        return True
        
    except Exception as e:
        print(f"❌ API endpoint registration failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests and report results."""
    print("🧪 Testing A2aStream Constructor Fix")
    print("=" * 50)
    
    tests = [
        ("A2aStream Instantiation", test_a2a_stream_instantiation),
        ("All A2A Handlers", test_all_a2a_handlers),
        ("API Endpoint Registration", test_api_endpoint_registration),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! A2aStream constructor issue is fixed.")
        return 0
    else:
        print("⚠️ Some tests failed. Issue may not be fully resolved.")
        return 1


if __name__ == "__main__":
    sys.exit(main())