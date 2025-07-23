#!/usr/bin/env python3
"""
Test script for SSH fallback mechanism in CodeExecution tool.
"""

import asyncio
import os
import sys
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, '/home/runner/work/gary-zero/gary-zero')

from framework.helpers.execution_mode import get_execution_info, should_use_ssh_execution
from framework.tools.code_execution_tool import CodeExecution


class MockAgentConfig:
    """Mock agent configuration for testing."""
    def __init__(self, ssh_enabled=True):
        self.code_exec_ssh_enabled = ssh_enabled
        self.code_exec_ssh_addr = "127.0.0.1"
        self.code_exec_ssh_port = 55022
        self.code_exec_ssh_user = "root"
        self.code_exec_ssh_pass = ""
        self.code_exec_docker_enabled = False


class MockLog:
    """Mock logger for testing."""
    def log(self, *args, **kwargs):
        return MagicMock()


class MockAgentContext:
    """Mock agent context for testing."""
    def __init__(self):
        self.log = MockLog()


class MockAgent:
    """Mock agent for testing."""
    def __init__(self, ssh_enabled=True):
        self.config = MockAgentConfig(ssh_enabled)
        self.context = MockAgentContext()

    def get_data(self, key):
        return None

    def set_data(self, key, value):
        pass


async def test_ssh_fallback():
    """Test that SSH fallback works when SSH is not available."""
    print("🧪 Testing SSH fallback mechanism...")

    # Test 1: SSH enabled but not available (should fallback to local)
    print("\n📋 Test 1: SSH enabled but not available")
    print(f"Environment info: {get_execution_info()}")
    print(f"Should use SSH: {should_use_ssh_execution()}")

    agent = MockAgent(ssh_enabled=True)
    tool = CodeExecution(agent=agent, name="test_tool", method="execute", args={"runtime": "python", "code": "print('test')"}, message="test message")

    try:
        await tool.prepare_state()

        # Check that session 0 was created and is a LocalInteractiveSession
        if hasattr(tool, 'state') and tool.state and 0 in tool.state.shells:
            session_type = type(tool.state.shells[0]).__name__
            print(f"✅ Session created successfully with type: {session_type}")

            if session_type == "LocalInteractiveSession":
                print("✅ Correctly fell back to local execution")
            else:
                print(f"❌ Expected LocalInteractiveSession, got {session_type}")

            # Clean up
            tool.state.shells[0].close()
        else:
            print("❌ No session was created")

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: SSH explicitly disabled
    print("\n📋 Test 2: SSH explicitly disabled")
    agent = MockAgent(ssh_enabled=False)
    tool = CodeExecution(agent=agent, name="test_tool", method="execute", args={"runtime": "python", "code": "print('test')"}, message="test message")

    try:
        await tool.prepare_state()

        if hasattr(tool, 'state') and tool.state and 0 in tool.state.shells:
            session_type = type(tool.state.shells[0]).__name__
            print(f"✅ Session created with type: {session_type}")

            if session_type == "LocalInteractiveSession":
                print("✅ Correctly used local execution when SSH disabled")
            else:
                print(f"❌ Expected LocalInteractiveSession, got {session_type}")

            # Clean up
            tool.state.shells[0].close()
        else:
            print("❌ No session was created")

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")


async def test_environment_variables():
    """Test environment variable override behavior."""
    print("\n🧪 Testing environment variable overrides...")

    # Test with DISABLE_SSH_EXECUTION=true
    os.environ['DISABLE_SSH_EXECUTION'] = 'true'

    try:
        print(f"Should use SSH (with DISABLE_SSH_EXECUTION=true): {should_use_ssh_execution()}")
        print(f"Execution info: {get_execution_info()}")

        if not should_use_ssh_execution():
            print("✅ Environment variable correctly disables SSH")
        else:
            print("❌ Environment variable did not disable SSH")

    finally:
        # Clean up
        del os.environ['DISABLE_SSH_EXECUTION']

    # Test with CODE_EXECUTION_MODE=direct
    os.environ['CODE_EXECUTION_MODE'] = 'direct'

    try:
        print(f"Should use SSH (with CODE_EXECUTION_MODE=direct): {should_use_ssh_execution()}")
        print(f"Execution info: {get_execution_info()}")

        if not should_use_ssh_execution():
            print("✅ Environment variable correctly sets direct execution")
        else:
            print("❌ Environment variable did not set direct execution")

    finally:
        # Clean up
        del os.environ['CODE_EXECUTION_MODE']


async def main():
    """Run all tests."""
    print("🚀 Starting SSH fallback tests...")

    await test_environment_variables()
    await test_ssh_fallback()

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
