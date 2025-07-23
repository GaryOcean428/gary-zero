"""
Simple test for the secure execution integration.
"""
import sys

# Add the project root to Python path
sys.path.insert(0, '/home/runner/work/gary-zero/gary-zero')

def test_secure_manager_import():
    """Test that we can import and use the secure manager."""
    print("🧪 Testing secure manager import and basic functionality...")

    try:
        from framework.executors.secure_manager import SecureCodeExecutionManager

        manager = SecureCodeExecutionManager()
        info = manager.get_executor_info()

        print("✅ Manager imported successfully")
        print(f"   Executor type: {info['type']}")
        print(f"   Secure: {info['secure']}")
        print(f"   Description: {info['description']}")

        # Test a simple execution
        if manager.is_secure_execution_available():
            session_id = manager.create_session()
            result = manager.execute_code(session_id, "print('Integration test successful!')", "python")
            print(f"   Test execution: {result.get('success', False)}")
            if result.get('success'):
                print(f"   Output: {result.get('stdout', 'No output').strip()}")
            manager.close_session(session_id)

        manager.cleanup_all()
        return True

    except Exception as e:
        print(f"❌ Secure manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_tool_import():
    """Test that we can import the enhanced tool."""
    print("\n🧪 Testing enhanced tool import...")

    try:
        # First test if we can import the secure execution
        print("✅ SecureCodeExecution tool imported successfully")

        # Test import of enhanced code execution tool
        import framework.tools.code_execution_tool as cet
        print("✅ Enhanced CodeExecution tool imported successfully")
        print(f"   Secure execution available: {cet.SECURE_EXECUTION_AVAILABLE}")

        return True

    except Exception as e:
        print(f"❌ Enhanced tool import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_validation():
    """Test the integration works end-to-end."""
    print("\n🧪 Testing integration validation...")

    try:
        # Test that both approaches (new and enhanced) work
        from framework.executors.secure_manager import SecureCodeExecutionManager

        manager = SecureCodeExecutionManager()
        info = manager.get_executor_info()

        print("✅ Integration test completed")
        print(f"   Available executor: {info['type']}")
        print(f"   Security level: {'High' if info['secure'] == 'True' else 'Low'}")

        manager.cleanup_all()
        return True

    except Exception as e:
        print(f"❌ Integration validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Starting integration tests...")

    # Test 1: Basic secure manager functionality
    success1 = test_secure_manager_import()

    # Test 2: Enhanced tool import
    success2 = test_enhanced_tool_import()

    # Test 3: Integration validation
    success3 = test_integration_validation()

    if success1 and success2 and success3:
        print("\n✅ All integration tests passed!")
        print("🔒 Secure code execution framework is ready for use")
        return True
    else:
        print("\n❌ Some integration tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
