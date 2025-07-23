"""
Test script for secure code execution framework.
"""
import sys
import traceback

# Add the project root to Python path
sys.path.insert(0, '/home/runner/work/gary-zero/gary-zero')

def test_executor_initialization():
    """Test that executors can be initialized properly."""
    print("🧪 Testing executor initialization...")

    try:
        from framework.executors.secure_manager import SecureCodeExecutionManager

        manager = SecureCodeExecutionManager()
        info = manager.get_executor_info()

        print("✅ Manager initialized successfully")
        print(f"   Executor type: {info['type']}")
        print(f"   Secure: {info['secure']}")
        print(f"   Description: {info['description']}")

        return True, manager

    except Exception as e:
        print(f"❌ Manager initialization failed: {e}")
        traceback.print_exc()
        return False, None

def test_basic_code_execution(manager):
    """Test basic code execution."""
    print("\n🧪 Testing basic code execution...")

    try:
        # Create a session
        session_id = manager.create_session()
        print(f"✅ Session created: {session_id}")

        # Test Python code execution
        test_code = "print('Hello from secure execution!'); x = 2 + 2; print(f'2 + 2 = {x}')"
        result = manager.execute_code(session_id, test_code, "python")

        print("✅ Code execution result:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Stdout: {result.get('stdout', 'N/A')}")
        if not result.get('success', False):
            print(f"   Error: {result.get('error', 'N/A')}")
            print(f"   Stderr: {result.get('stderr', 'N/A')}")

        # Clean up
        manager.close_session(session_id)
        print("✅ Session closed")

        return result.get('success', False)

    except Exception as e:
        print(f"❌ Code execution test failed: {e}")
        traceback.print_exc()
        return False

def test_package_installation(manager):
    """Test package installation if secure executor is available."""
    print("\n🧪 Testing package installation...")

    try:
        if not manager.is_secure_execution_available():
            print("⏭️  Skipping package installation test (no secure executor)")
            return True

        # Create a session
        session_id = manager.create_session()

        # Test package installation (use a small package)
        result = manager.install_package(session_id, "json-tricks")

        print("✅ Package installation result:")
        print(f"   Success: {result.get('success', False)}")
        if not result.get('success', False):
            print(f"   Error: {result.get('error', 'N/A')}")

        # Test if package is available
        if result.get('success', False):
            test_code = "import json_tricks; print('json_tricks imported successfully')"
            exec_result = manager.execute_code(session_id, test_code, "python")
            print(f"   Package usage test: {exec_result.get('success', False)}")

        # Clean up
        manager.close_session(session_id)

        return result.get('success', False)

    except Exception as e:
        print(f"❌ Package installation test failed: {e}")
        traceback.print_exc()
        return False

def test_shell_execution(manager):
    """Test shell command execution."""
    print("\n🧪 Testing shell execution...")

    try:
        if not manager.is_secure_execution_available():
            print("⏭️  Skipping shell execution test (no secure executor)")
            return True

        # Create a session
        session_id = manager.create_session()

        # Test shell command
        result = manager.execute_code(session_id, "echo 'Hello from shell!' && pwd", "bash")

        print("✅ Shell execution result:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Stdout: {result.get('stdout', 'N/A')}")
        if not result.get('success', False):
            print(f"   Error: {result.get('error', 'N/A')}")

        # Clean up
        manager.close_session(session_id)

        return result.get('success', False)

    except Exception as e:
        print(f"❌ Shell execution test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Starting secure code execution tests...")

    # Test 1: Initialization
    success, manager = test_executor_initialization()
    if not success:
        print("\n❌ Critical failure: Could not initialize manager")
        return False

    # Test 2: Basic code execution
    success = test_basic_code_execution(manager)
    if not success:
        print("\n❌ Critical failure: Basic code execution failed")
        return False

    # Test 3: Package installation (if available)
    test_package_installation(manager)

    # Test 4: Shell execution (if available)
    test_shell_execution(manager)

    # Cleanup
    manager.cleanup_all()

    print("\n✅ All critical tests passed!")
    print(f"ℹ️  Executor type: {manager.get_executor_info()['type']}")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
