#!/usr/bin/env python3
"""
Demo script for Gary-Zero Kali Linux Docker service integration.

This script demonstrates the capabilities of the Kali service integration,
including service discovery, command execution, and security tool usage.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from framework.helpers.execution_mode import (
    get_execution_config,
    get_execution_info,
    should_use_kali_service,
)
from framework.helpers.kali_executor import (
    KaliCodeExecutor,
    is_kali_execution_available,
)
from framework.helpers.kali_service import get_kali_service, is_kali_service_available


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"🔐 {title}")
    print("=" * 60)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n📋 {title}")
    print("-" * 40)


def print_result(result: dict, show_output: bool = True):
    """Print execution result in a formatted way."""
    if result.get("success"):
        print("✅ Command executed successfully")
        if show_output and result.get("stdout"):
            print(f"Output:\n{result['stdout']}")
    else:
        print("❌ Command failed")
        if result.get("error"):
            print(f"Error: {result['error']}")
        if result.get("stderr"):
            print(f"Stderr: {result['stderr']}")


async def demo_service_discovery():
    """Demonstrate service discovery and configuration."""
    print_section("Service Discovery & Configuration")

    print(f"Kali service configured: {os.getenv('KALI_SHELL_URL') is not None}")
    print(f"Should use Kali service: {should_use_kali_service()}")
    print(f"Kali execution available: {is_kali_execution_available()}")
    print(f"Service availability: {is_kali_service_available()}")

    print("\nExecution configuration:")
    config = get_execution_config()
    for key, value in config.items():
        if key == "password":
            value = "*" * len(str(value)) if value else "not set"
        print(f"  {key}: {value}")

    print(f"\nExecution info: {get_execution_info()}")


async def demo_basic_connectivity():
    """Demonstrate basic connectivity to Kali service."""
    print_section("Basic Connectivity Test")

    kali = get_kali_service()
    if not kali:
        print("❌ Kali service not available")
        return False

    print("🔗 Testing service availability...")
    if kali.is_available():
        print("✅ Kali service is available")

        print("\n📊 Getting service information...")
        info = kali.get_service_info()
        if info.get("error"):
            print(f"Service info error: {info['error']}")
        else:
            print("Service info:")
            for key, value in info.items():
                print(f"  {key}: {value}")

        kali.close()
        return True
    else:
        print("❌ Kali service is not available")
        kali.close()
        return False


async def demo_command_execution():
    """Demonstrate basic command execution."""
    print_section("Command Execution")

    executor = KaliCodeExecutor()
    if not await executor.initialize():
        print("❌ Failed to initialize Kali executor")
        return

    # Test basic system commands
    commands = [
        ("System Info", "uname -a"),
        ("Current User", "whoami"),
        ("Working Directory", "pwd"),
        ("Network Config", "ip addr show | head -10"),
        ("Available Tools", "ls /usr/bin/ | grep -E '(nmap|nikto|sqlmap)' | head -5"),
    ]

    for description, command in commands:
        print(f"\n🔧 {description}:")
        print(f"Command: {command}")
        result = await executor.execute_command(command, timeout=15)
        print_result(result, show_output=True)

    executor.close()


async def demo_security_tools():
    """Demonstrate security tools usage."""
    print_section("Security Tools Demonstration")

    executor = KaliCodeExecutor()
    if not await executor.initialize():
        print("❌ Failed to initialize Kali executor")
        return

    # Get available tools
    print("🛠️  Getting available security tools...")
    tools_result = await executor.get_available_tools()
    print_result(tools_result)

    # Demonstrate tool usage (safe examples)
    print("\n🔍 Demonstrating tool usage with safe examples:")

    # Nmap localhost scan (safe)
    print("\n1. Nmap localhost scan:")
    nmap_result = await executor.execute_command(
        "nmap -sT localhost -p 80,443,8080", timeout=30
    )
    print_result(nmap_result)

    # Check SSL certificate for a public site (safe)
    print("\n2. SSL certificate check:")
    ssl_result = await executor.check_ssl_certificate("google.com")
    print_result(ssl_result)

    # Check tool versions
    print("\n3. Tool versions:")
    version_commands = [
        "nmap --version | head -2",
        "nikto -Version 2>/dev/null || echo 'Nikto version check failed'",
        "openssl version",
    ]

    for cmd in version_commands:
        result = await executor.execute_command(cmd, timeout=10)
        if result.get("success"):
            print(f"  {result['stdout'].strip()}")

    executor.close()


async def demo_integration_patterns():
    """Demonstrate common integration patterns."""
    print_section("Integration Patterns")

    # Pattern 1: Direct service access
    print("1. Direct service access pattern:")
    kali = get_kali_service()
    if kali:
        result = kali.execute_command("echo 'Direct service access working'")
        print_result(result)
        kali.close()

    # Pattern 2: High-level executor
    print("\n2. High-level executor pattern:")
    executor = KaliCodeExecutor()
    if await executor.initialize():
        result = await executor.execute_command("echo 'High-level executor working'")
        print_result(result)
        executor.close()

    # Pattern 3: Convenience function
    print("\n3. Convenience function pattern:")
    try:
        from framework.helpers.kali_executor import execute_in_kali

        result = await execute_in_kali("echo 'Convenience function working'")
        print_result(result)
    except ImportError:
        print("❌ Convenience function not available")


async def demo_error_handling():
    """Demonstrate error handling scenarios."""
    print_section("Error Handling")

    executor = KaliCodeExecutor()
    if not await executor.initialize():
        print("❌ Failed to initialize - testing error conditions")
        return

    # Test various error conditions
    error_tests = [
        ("Invalid command", "this_command_does_not_exist"),
        ("Command with error exit code", "ls /nonexistent_directory"),
        (
            "Long running command (timeout test)",
            "sleep 5",
        ),  # Short timeout to trigger timeout
    ]

    for description, command in error_tests:
        print(f"\n🔍 {description}:")
        print(f"Command: {command}")
        timeout = 3 if "timeout" in description else 10
        result = await executor.execute_command(command, timeout=timeout)
        print_result(result)

    executor.close()


async def main():
    """Main demo function."""
    print_header("Gary-Zero Kali Service Integration Demo")
    print(f"Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check if demo environment is set up
    if not os.getenv("KALI_SHELL_URL"):
        print("\n⚠️  Setting up demo environment...")
        demo_env = {
            "CODE_EXECUTION_MODE": "kali",
            "KALI_SHELL_URL": "http://kali-linux-docker.railway.internal:8080",
            "KALI_SHELL_HOST": "kali-linux-docker.railway.internal",
            "KALI_SHELL_PORT": "8080",
            "KALI_USERNAME": "GaryOcean",
            "KALI_PASSWORD": "I.Am.Dev.1",
            "KALI_PUBLIC_URL": "https://kali-linux-docker.up.railway.app",
        }

        for key, value in demo_env.items():
            os.environ[key] = value

        print("✅ Demo environment configured")

    try:
        # Run demo sections
        await demo_service_discovery()

        # Only proceed with connection tests if service is configured
        if os.getenv("KALI_SHELL_URL"):
            connectivity_ok = await demo_basic_connectivity()

            if connectivity_ok:
                await demo_command_execution()
                await demo_security_tools()
                await demo_integration_patterns()
                await demo_error_handling()
            else:
                print(
                    "\n⚠️  Skipping connection-dependent demos due to connectivity issues"
                )
                print(
                    "    (This is expected if the Kali service is not actually running)"
                )

        print_header("Demo Summary")
        print("✅ Demo completed successfully!")
        print("\n📚 For more information, see:")
        print("   - docs/KALI_INTEGRATION.md")
        print("   - framework/helpers/kali_service.py")
        print("   - framework/helpers/kali_executor.py")

        print("\n🚀 To use in production:")
        print("   1. Deploy kali-linux-docker service to Railway")
        print("   2. Configure Railway reference variables")
        print("   3. Set CODE_EXECUTION_MODE=kali")
        print("   4. Use KaliCodeExecutor or KaliServiceConnector in your code")

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
