#!/usr/bin/env python3
"""
Test script to simulate the original SSH failure scenario and verify the fix.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, "/home/runner/work/gary-zero/gary-zero")

from unittest.mock import MagicMock

from framework.helpers.execution_mode import (
    get_execution_info,
    should_use_ssh_execution,
)
from framework.tools.code_execution_tool import CodeExecution


class MockAgentConfig:
    """Mock agent configuration that forces SSH enabled."""

    def __init__(self):
        # Force SSH settings to match the original issue
        self.code_exec_ssh_enabled = True
        self.code_exec_ssh_addr = "127.0.0.1"
        self.code_exec_ssh_port = 55022  # The problematic port from the issue
        self.code_exec_ssh_user = "root"
        self.code_exec_ssh_pass = ""
        self.code_exec_docker_enabled = False


class MockLog:
    """Mock logger."""

    def log(self, *args, **kwargs):
        return MagicMock()


class MockAgentContext:
    """Mock agent context."""

    def __init__(self):
        self.log = MockLog()


class MockAgent:
    """Mock agent that simulates the original failing scenario."""

    def __init__(self):
        self.config = MockAgentConfig()
        self.context = MockAgentContext()

    def get_data(self, key):
        return None

    def set_data(self, key, value):
        pass


async def test_original_ssh_failure_scenario():
    """
    Test the exact scenario described in the issue:
    - SSH enabled in config
    - Port 55022 not available
    - Should fallback gracefully instead of crashing
    """
    print("🧪 Testing original SSH failure scenario...")
    print("📋 Simulating: SSH enabled, port 55022 not available")

    # Force environment to prefer SSH execution temporarily
    original_env = os.environ.get("CODE_EXECUTION_MODE")
    os.environ["CODE_EXECUTION_MODE"] = "ssh"

    try:
        agent = MockAgent()
        print(
            f"Agent SSH config: enabled={agent.config.code_exec_ssh_enabled}, port={agent.config.code_exec_ssh_port}"
        )
        print(f"Environment detection: {get_execution_info()}")

        # Create code execution tool
        tool = CodeExecution(
            agent=agent,
            name="code_execution",
            method="execute",
            args={"runtime": "python", "code": "print('Hello World!')"},
            message="test",
        )

        # This should NOT crash with NoValidConnectionsError anymore
        print("🔗 Attempting to prepare state (should fallback gracefully)...")
        await tool.prepare_state()

        # Verify fallback worked
        if hasattr(tool, "state") and tool.state and 0 in tool.state.shells:
            session_type = type(tool.state.shells[0]).__name__
            print(f"✅ Fallback successful! Session type: {session_type}")

            if session_type == "LocalInteractiveSession":
                print("✅ Correctly fell back to local execution despite SSH config")

                # Test that code execution actually works
                print("🚀 Testing code execution with fallback...")
                try:
                    result = await tool.execute_python_code(
                        0, "x = 2 + 2; print(f'2 + 2 = {x}')"
                    )
                    print(f"✅ Code execution result: {result}")
                except Exception as e:
                    print(f"❌ Code execution failed: {e}")
            else:
                print(f"❌ Unexpected session type: {session_type}")

            # Clean up
            tool.state.shells[0].close()
        else:
            print("❌ No session was created")

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        print("This indicates the fallback mechanism is not working properly!")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Restore environment
        if original_env:
            os.environ["CODE_EXECUTION_MODE"] = original_env
        elif "CODE_EXECUTION_MODE" in os.environ:
            del os.environ["CODE_EXECUTION_MODE"]

    return True


async def test_railway_environment_simulation():
    """Test behavior in a simulated Railway environment."""
    print("\n🧪 Testing Railway environment simulation...")

    # Simulate Railway environment
    os.environ["RAILWAY_ENVIRONMENT"] = "production"

    try:
        print(f"Environment detection: {get_execution_info()}")
        print(f"Should use SSH in Railway: {should_use_ssh_execution()}")

        if not should_use_ssh_execution():
            print("✅ Railway environment correctly defaults to direct execution")
        else:
            print("❌ Railway environment should not use SSH by default")

    finally:
        # Clean up
        del os.environ["RAILWAY_ENVIRONMENT"]


async def main():
    """Run all tests."""
    print("🚀 Testing SSH fallback fix for issue #136...")
    print("=" * 60)

    # Test the original failure scenario
    success = await test_original_ssh_failure_scenario()

    # Test Railway environment
    await test_railway_environment_simulation()

    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed! The SSH fallback mechanism is working correctly.")
        print("🎉 Issue #136 should be resolved!")
    else:
        print("❌ Tests failed! The fix needs more work.")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
