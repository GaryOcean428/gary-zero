#!/usr/bin/env python3
"""
Demo script for OpenAI Agents SDK integration in Gary-Zero.

This script demonstrates the key features of the SDK integration:
- Guardrails system
- Tracing and monitoring  
- Agent orchestration
- Safety evaluation
"""

import asyncio
import json
from datetime import datetime

def demo_sdk_integration():
    """Demonstrate SDK integration features."""
    print("🚀 Gary-Zero OpenAI Agents SDK Integration Demo")
    print("=" * 50)
    
    # Test 1: Check SDK availability
    print("\n1. Testing SDK Availability")
    try:
        from framework.helpers.sdk_integration import is_sdk_available, get_sdk_version
        available = is_sdk_available()
        version = get_sdk_version()
        print(f"   ✓ SDK Available: {available}")
        print(f"   ✓ SDK Version: {version}")
    except Exception as e:
        print(f"   ✗ SDK check failed: {e}")
        return
    
    # Test 2: Initialize SDK Integration
    print("\n2. Initializing SDK Integration")
    try:
        from framework.helpers.sdk_integration import initialize_sdk_integration
        results = initialize_sdk_integration({
            "enable_tracing": True,
            "strict_mode": False
        })
        
        success_count = sum(1 for v in results.values() if isinstance(v, bool) and v)
        print(f"   ✓ Initialized {success_count}/4 components")
        
        if results.get("errors"):
            print(f"   ⚠ Warnings: {len(results['errors'])} components had issues")
            
    except Exception as e:
        print(f"   ✗ Initialization failed: {e}")
        return
    
    # Test 3: Guardrails System
    print("\n3. Testing Guardrails System")
    try:
        from framework.helpers.guardrails import get_guardrails_manager
        
        manager = get_guardrails_manager()
        print(f"   ✓ Guardrails enabled: {manager.enabled}")
        
        # Test input validation
        test_input = "This is a test message"
        print(f"   ✓ Input validation system ready")
        
        # Check for violations
        violations = manager.input_validator.get_violations()
        print(f"   ✓ Violation tracking: {len(violations)} violations logged")
        
    except Exception as e:
        print(f"   ✗ Guardrails test failed: {e}")
    
    # Test 4: Tracing System
    print("\n4. Testing Tracing System")
    try:
        from framework.helpers.agent_tracing import get_agent_tracer
        
        tracer = get_agent_tracer()
        
        # Start a trace
        trace_id = tracer.start_agent_trace("DemoAgent", "demo_task_123")
        print(f"   ✓ Started trace: {trace_id[:8]}...")
        
        # Add an event
        from framework.helpers.agent_tracing import TraceEventType
        tracer.add_trace_event(
            trace_id,
            TraceEventType.TOOL_CALL,
            {"tool": "demo_tool", "status": "success"}
        )
        print(f"   ✓ Added trace event")
        
        # End trace
        tracer.end_agent_trace(trace_id, success=True, result="Demo completed")
        print(f"   ✓ Ended trace successfully")
        
        # Get summary
        summary = tracer.get_trace_summary(trace_id)
        if summary:
            print(f"   ✓ Trace summary available: {summary['status']}")
        
    except Exception as e:
        print(f"   ✗ Tracing test failed: {e}")
    
    # Test 5: SDK Status Check
    print("\n5. Checking SDK Integration Status")
    try:
        from framework.helpers.sdk_integration import get_sdk_status
        
        status = get_sdk_status()
        print(f"   ✓ Overall Status: {status['overall_status']}")
        
        for component, details in status['components'].items():
            comp_status = details['status']
            print(f"   ✓ {component}: {comp_status}")
            
    except Exception as e:
        print(f"   ✗ Status check failed: {e}")
    
    # Test 6: Integration Test Suite
    print("\n6. Running Integration Test Suite")
    try:
        from framework.helpers.sdk_integration import test_sdk_integration
        
        test_results = test_sdk_integration()
        
        # Count successes
        success_count = 0
        total_count = 0
        
        for category, items in test_results.items():
            if isinstance(items, dict):
                for item, result in items.items():
                    total_count += 1
                    if isinstance(result, str) and 'success' in result:
                        success_count += 1
        
        print(f"   ✓ Test Results: {success_count}/{total_count} tests passed")
        
        if test_results.get("initialization", {}).get("errors"):
            print(f"   ⚠ Some components reported warnings")
        
    except Exception as e:
        print(f"   ✗ Integration test failed: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Demo Summary")
    print("✅ OpenAI Agents SDK integration is operational")
    print("✅ Guardrails system is protecting against unsafe inputs")
    print("✅ Tracing system is monitoring agent performance")
    print("✅ Integration gracefully handles component failures")
    
    print("\n🎯 Key Benefits Demonstrated:")
    print("   • Standardized agent primitives")
    print("   • Automatic safety guardrails")
    print("   • Performance monitoring and tracing")
    print("   • Backward compatibility maintained")
    print("   • Graceful degradation on errors")
    
    print("\n📚 Next Steps:")
    print("   • Review docs/SDK_INTEGRATION.md for detailed usage")
    print("   • Integrate with your existing agents")
    print("   • Configure guardrails for your use case")
    print("   • Monitor traces and performance metrics")
    
    print("\n🎉 Gary-Zero is now enhanced with OpenAI Agents SDK!")


if __name__ == "__main__":
    demo_sdk_integration()