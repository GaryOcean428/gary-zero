#!/usr/bin/env python3
"""
Kali Shell Integration Validation Script for Gary-Zero

This script validates that the Kali shell service integration is properly
configured and operational, testing connectivity, environment variables,
and service availability.
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests


def validate_environment_variables() -> dict[str, Any]:
    """Check all required environment variables for Kali service integration."""
    required_vars = [
        "KALI_SHELL_URL",
        "KALI_SHELL_HOST",
        "KALI_SHELL_PORT",
        "KALI_USERNAME",
        "KALI_PASSWORD",
    ]

    optional_vars = ["KALI_PUBLIC_URL", "CODE_EXECUTION_MODE", "SHELL_SERVICE_ENABLED"]

    results = {"required": {}, "optional": {}, "all_required_present": True}

    # Check required variables
    for var in required_vars:
        value = os.getenv(var)
        is_present = value is not None and value.strip() != ""
        results["required"][var] = {
            "present": is_present,
            "value": value if var != "KALI_PASSWORD" else "***" if value else None,
            "length": len(value) if value else 0,
        }
        if not is_present:
            results["all_required_present"] = False

    # Check optional variables
    for var in optional_vars:
        value = os.getenv(var)
        results["optional"][var] = {
            "present": value is not None,
            "value": value,
            "default_used": value is None,
        }

    return results


def test_shell_connectivity() -> dict[str, Any]:
    """Test basic connectivity to the Kali shell service."""
    shell_url = os.getenv("KALI_SHELL_URL")
    username = os.getenv("KALI_USERNAME")
    password = os.getenv("KALI_PASSWORD")

    if not all([shell_url, username, password]):
        return {
            "error": "Missing required environment variables for connectivity test",
            "connectivity": False,
        }

    try:
        # Test health endpoint
        print(f"Testing connectivity to: {shell_url}")

        health_response = requests.get(
            f"{shell_url}/health", auth=(username, password), timeout=10
        )

        connectivity_result = {
            "connectivity": health_response.status_code == 200,
            "status_code": health_response.status_code,
            "response_time": health_response.elapsed.total_seconds(),
            "headers": dict(health_response.headers),
        }

        if health_response.status_code == 200:
            try:
                connectivity_result["service_info"] = health_response.json()
            except:
                connectivity_result["service_info"] = health_response.text
        else:
            connectivity_result["error_response"] = health_response.text

        # Test service info endpoint if health check passed
        if connectivity_result["connectivity"]:
            try:
                info_response = requests.get(
                    f"{shell_url}/info", auth=(username, password), timeout=5
                )
                if info_response.status_code == 200:
                    connectivity_result["service_details"] = info_response.json()
            except Exception as e:
                connectivity_result["info_endpoint_error"] = str(e)

        return connectivity_result

    except requests.exceptions.ConnectTimeout:
        return {
            "error": "Connection timeout - service may be unavailable",
            "connectivity": False,
            "error_type": "timeout",
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "error": f"Connection error: {str(e)}",
            "connectivity": False,
            "error_type": "connection",
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "connectivity": False,
            "error_type": "unexpected",
        }


def test_shell_command_execution() -> dict[str, Any]:
    """Test basic command execution through the shell service."""
    shell_url = os.getenv("KALI_SHELL_URL")
    username = os.getenv("KALI_USERNAME")
    password = os.getenv("KALI_PASSWORD")

    if not all([shell_url, username, password]):
        return {
            "error": "Missing required environment variables for command test",
            "success": False,
        }

    try:
        # Test basic command execution
        test_commands = [
            {"command": "whoami", "description": "Check current user"},
            {"command": "pwd", "description": "Check current directory"},
            {"command": "uname -a", "description": "Check system information"},
            {"command": "which nmap", "description": "Check if nmap is available"},
        ]

        results = {}

        for test_cmd in test_commands:
            try:
                response = requests.post(
                    f"{shell_url}/execute",
                    json={
                        "command": test_cmd["command"],
                        "timeout": 10,
                        "environment": "kali",
                    },
                    auth=(username, password),
                    timeout=15,
                )

                if response.status_code == 200:
                    cmd_result = response.json()
                    results[test_cmd["command"]] = {
                        "success": cmd_result.get("success", False),
                        "stdout": cmd_result.get("stdout", ""),
                        "stderr": cmd_result.get("stderr", ""),
                        "exit_code": cmd_result.get("exit_code", -1),
                        "description": test_cmd["description"],
                    }
                else:
                    results[test_cmd["command"]] = {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "description": test_cmd["description"],
                    }

            except Exception as e:
                results[test_cmd["command"]] = {
                    "success": False,
                    "error": str(e),
                    "description": test_cmd["description"],
                }

        # Overall success if at least basic commands work
        overall_success = any(
            results.get(cmd, {}).get("success", False)
            for cmd in ["whoami", "pwd", "uname -a"]
        )

        return {
            "success": overall_success,
            "command_results": results,
            "total_commands": len(test_commands),
            "successful_commands": sum(
                1 for r in results.values() if r.get("success", False)
            ),
        }

    except Exception as e:
        return {"success": False, "error": f"Command execution test failed: {str(e)}"}


def validate_framework_integration() -> dict[str, Any]:
    """Validate that the framework integration files are present and correct."""
    base_path = Path(__file__).parent

    required_files = [
        "framework/helpers/kali_service.py",
        "framework/helpers/kali_executor.py",
        "framework/tools/shell_execute.py",
        "prompts/default/shell_integration_guide.md",
        "webui/js/shell-iframe.js",
    ]

    results = {
        "files_present": {},
        "all_files_present": True,
        "integration_complete": False,
    }

    for file_path in required_files:
        full_path = base_path / file_path
        is_present = full_path.exists()
        file_size = full_path.stat().st_size if is_present else 0

        results["files_present"][file_path] = {
            "present": is_present,
            "size_bytes": file_size,
            "path": str(full_path),
        }

        if not is_present:
            results["all_files_present"] = False

    # Check if shell integration is included in main agent prompt
    try:
        main_prompt_path = base_path / "prompts/default/agent.system.main.md"
        if main_prompt_path.exists():
            with open(main_prompt_path) as f:
                prompt_content = f.read()
                has_shell_integration = "shell_integration_guide.md" in prompt_content
                results["prompt_integration"] = {
                    "main_prompt_exists": True,
                    "shell_integration_included": has_shell_integration,
                }
        else:
            results["prompt_integration"] = {
                "main_prompt_exists": False,
                "shell_integration_included": False,
            }
    except Exception as e:
        results["prompt_integration"] = {"error": str(e)}

    # Overall integration status
    results["integration_complete"] = results["all_files_present"] and results.get(
        "prompt_integration", {}
    ).get("shell_integration_included", False)

    return results


async def test_kali_executor_integration() -> dict[str, Any]:
    """Test the KaliCodeExecutor class functionality."""
    try:
        # Import the executor
        sys.path.insert(0, str(Path(__file__).parent))
        from framework.helpers.kali_executor import (
            KaliCodeExecutor,
            is_kali_execution_available,
        )

        results = {
            "import_successful": True,
            "availability_check": is_kali_execution_available(),
            "executor_tests": {},
        }

        if not results["availability_check"]:
            results["executor_tests"]["note"] = (
                "Kali service not available - skipping executor tests"
            )
            return results

        # Test executor initialization
        executor = KaliCodeExecutor()
        init_success = await executor.initialize()

        results["executor_tests"]["initialization"] = {
            "success": init_success,
            "available": executor.is_available(),
        }

        if init_success:
            # Test basic command execution
            try:
                cmd_result = await executor.execute_command(
                    'echo "Hello from Kali"', timeout=10
                )
                results["executor_tests"]["basic_command"] = {
                    "success": cmd_result.get("success", False),
                    "output": cmd_result.get("stdout", ""),
                    "error": cmd_result.get("stderr", ""),
                }
            except Exception as e:
                results["executor_tests"]["basic_command"] = {
                    "success": False,
                    "error": str(e),
                }

            # Test tool availability
            try:
                tools_result = await executor.get_available_tools()
                results["executor_tests"]["tools_check"] = {
                    "success": tools_result.get("success", False),
                    "tools_found": tools_result.get("stdout", "").count("\n")
                    if tools_result.get("success")
                    else 0,
                }
            except Exception as e:
                results["executor_tests"]["tools_check"] = {
                    "success": False,
                    "error": str(e),
                }

            # Clean up
            executor.close()

        return results

    except ImportError as e:
        return {
            "import_successful": False,
            "import_error": str(e),
            "note": "Could not import KaliCodeExecutor - check framework installation",
        }
    except Exception as e:
        return {"import_successful": False, "unexpected_error": str(e)}


def generate_integration_report(results: dict[str, Any]) -> str:
    """Generate a comprehensive integration report."""
    report_lines = [
        "🛡️  GARY-ZERO KALI SHELL INTEGRATION VALIDATION REPORT",
        "=" * 60,
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
        "",
    ]

    # Environment Variables Section
    report_lines.extend(["📋 ENVIRONMENT VARIABLES", "-" * 30])

    env_results = results.get("environment", {})
    for var, info in env_results.get("required", {}).items():
        status = "✅" if info["present"] else "❌"
        value_display = info["value"] if info["value"] != "***" else "*** (hidden)"
        report_lines.append(f"  {status} {var}: {value_display}")

    if env_results.get("optional"):
        report_lines.append("\n  Optional Variables:")
        for var, info in env_results.get("optional", {}).items():
            status = "✅" if info["present"] else "➖"
            report_lines.append(f"  {status} {var}: {info['value'] or 'Not set'}")

    # Connectivity Section
    report_lines.extend(["", "🌐 CONNECTIVITY TEST", "-" * 30])

    conn_results = results.get("connectivity", {})
    if conn_results.get("connectivity"):
        response_time = conn_results.get("response_time", 0)
        report_lines.extend(
            [
                "  ✅ Shell service reachable",
                f"  📊 Response time: {response_time:.3f}s",
                f"  📡 Status code: {conn_results.get('status_code')}",
            ]
        )

        if conn_results.get("service_info"):
            report_lines.append(f"  📋 Service info: {conn_results['service_info']}")

    else:
        error_msg = conn_results.get("error", "Unknown connectivity error")
        report_lines.extend(
            [
                f"  ❌ Connection failed: {error_msg}",
                f"  🔍 Error type: {conn_results.get('error_type', 'unknown')}",
            ]
        )

    # Command Execution Section
    report_lines.extend(["", "💻 COMMAND EXECUTION TEST", "-" * 30])

    cmd_results = results.get("command_execution", {})
    if cmd_results.get("success"):
        total = cmd_results.get("total_commands", 0)
        successful = cmd_results.get("successful_commands", 0)
        report_lines.extend(
            [
                f"  ✅ Command execution working ({successful}/{total} commands successful)",
                "  📋 Command results:",
            ]
        )

        for cmd, result in cmd_results.get("command_results", {}).items():
            status = "✅" if result.get("success") else "❌"
            output = result.get("stdout", "").strip()[:50]
            output_display = f" → {output}" if output else ""
            report_lines.append(f"    {status} {cmd}{output_display}")
    else:
        error_msg = cmd_results.get("error", "Command execution failed")
        report_lines.append(f"  ❌ {error_msg}")

    # Framework Integration Section
    report_lines.extend(["", "🔧 FRAMEWORK INTEGRATION", "-" * 30])

    framework_results = results.get("framework_integration", {})
    for file_path, info in framework_results.get("files_present", {}).items():
        status = "✅" if info["present"] else "❌"
        size_kb = info["size_bytes"] / 1024 if info["present"] else 0
        report_lines.append(f"  {status} {file_path} ({size_kb:.1f} KB)")

    prompt_integration = framework_results.get("prompt_integration", {})
    if prompt_integration.get("shell_integration_included"):
        report_lines.append("  ✅ Shell integration included in agent prompts")
    else:
        report_lines.append("  ❌ Shell integration not found in agent prompts")

    # Executor Integration Section
    report_lines.extend(["", "⚙️  EXECUTOR INTEGRATION", "-" * 30])

    executor_results = results.get("executor_integration", {})
    if executor_results.get("import_successful"):
        report_lines.append("  ✅ KaliCodeExecutor import successful")

        if executor_results.get("availability_check"):
            report_lines.append("  ✅ Kali execution environment available")

            executor_tests = executor_results.get("executor_tests", {})
            if executor_tests.get("initialization", {}).get("success"):
                report_lines.append("  ✅ Executor initialization successful")

                if executor_tests.get("basic_command", {}).get("success"):
                    report_lines.append("  ✅ Basic command execution working")

                if executor_tests.get("tools_check", {}).get("success"):
                    tools_count = executor_tests.get("tools_check", {}).get(
                        "tools_found", 0
                    )
                    report_lines.append(
                        f"  ✅ Security tools available ({tools_count} found)"
                    )
            else:
                report_lines.append("  ❌ Executor initialization failed")
        else:
            report_lines.append("  ⚠️  Kali execution environment not available")
    else:
        import_error = executor_results.get("import_error", "Unknown import error")
        report_lines.append(f"  ❌ Import failed: {import_error}")

    # Summary Section
    report_lines.extend(["", "📊 INTEGRATION SUMMARY", "-" * 30])

    # Calculate overall status
    checks = [
        env_results.get("all_required_present", False),
        conn_results.get("connectivity", False),
        cmd_results.get("success", False),
        framework_results.get("integration_complete", False),
        executor_results.get("import_successful", False),
    ]

    passed_checks = sum(checks)
    total_checks = len(checks)

    if passed_checks == total_checks:
        status_emoji = "🎉"
        status_text = "FULLY OPERATIONAL"
        status_detail = "All integration components are working correctly!"
    elif passed_checks >= total_checks * 0.8:
        status_emoji = "⚠️"
        status_text = "MOSTLY OPERATIONAL"
        status_detail = "Most components working, minor issues detected"
    elif passed_checks >= total_checks * 0.5:
        status_emoji = "🔧"
        status_text = "PARTIAL INTEGRATION"
        status_detail = "Some components working, configuration needed"
    else:
        status_emoji = "❌"
        status_text = "INTEGRATION ISSUES"
        status_detail = "Major configuration or connectivity problems detected"

    report_lines.extend(
        [
            f"  {status_emoji} Status: {status_text}",
            f"  📋 Checks passed: {passed_checks}/{total_checks}",
            f"  💬 {status_detail}",
            "",
        ]
    )

    # Recommendations
    if passed_checks < total_checks:
        report_lines.extend(["🔍 RECOMMENDATIONS", "-" * 30])

        if not env_results.get("all_required_present"):
            report_lines.append(
                "  • Configure missing environment variables in Railway service"
            )

        if not conn_results.get("connectivity"):
            report_lines.append(
                "  • Check Kali service deployment and network configuration"
            )

        if not cmd_results.get("success"):
            report_lines.append(
                "  • Verify Kali service API endpoints and authentication"
            )

        if not framework_results.get("integration_complete"):
            report_lines.append(
                "  • Ensure all framework integration files are properly deployed"
            )

        if not executor_results.get("import_successful"):
            report_lines.append(
                "  • Check Python environment and framework dependencies"
            )

        report_lines.append("")

    report_lines.extend(["🛡️  End of Kali Shell Integration Report", "=" * 60])

    return "\n".join(report_lines)


async def main():
    """Main validation function."""
    print("🔍 Starting Kali Shell Integration Validation...")
    print("=" * 50)

    results = {}

    # Test 1: Environment Variables
    print("\n📋 Validating environment variables...")
    results["environment"] = validate_environment_variables()

    env_status = (
        "✅ All required variables present"
        if results["environment"]["all_required_present"]
        else "❌ Missing required variables"
    )
    print(f"   {env_status}")

    # Test 2: Connectivity
    print("\n🌐 Testing shell service connectivity...")
    results["connectivity"] = test_shell_connectivity()

    conn_status = (
        "✅ Service reachable"
        if results["connectivity"]["connectivity"]
        else "❌ Connection failed"
    )
    print(f"   {conn_status}")

    # Test 3: Command Execution
    if results["connectivity"]["connectivity"]:
        print("\n💻 Testing command execution...")
        results["command_execution"] = test_shell_command_execution()

        cmd_status = (
            "✅ Commands working"
            if results["command_execution"]["success"]
            else "❌ Command execution failed"
        )
        print(f"   {cmd_status}")
    else:
        print("\n💻 Skipping command execution test (no connectivity)")
        results["command_execution"] = {
            "success": False,
            "error": "No connectivity to test",
        }

    # Test 4: Framework Integration
    print("\n🔧 Validating framework integration...")
    results["framework_integration"] = validate_framework_integration()

    framework_status = (
        "✅ Integration complete"
        if results["framework_integration"]["integration_complete"]
        else "❌ Integration incomplete"
    )
    print(f"   {framework_status}")

    # Test 5: Executor Integration
    print("\n⚙️  Testing executor integration...")
    results["executor_integration"] = await test_kali_executor_integration()

    executor_status = (
        "✅ Executor working"
        if results["executor_integration"]["import_successful"]
        else "❌ Executor issues"
    )
    print(f"   {executor_status}")

    # Generate comprehensive report
    print("\n📊 Generating integration report...")
    report = generate_integration_report(results)

    # Output report
    print("\n" + report)

    # Save report to file
    try:
        report_file = Path(__file__).parent / "kali_integration_validation_report.txt"
        with open(report_file, "w") as f:
            f.write(report)
        print(f"\n📄 Full report saved to: {report_file}")
    except Exception as e:
        print(f"\n⚠️  Could not save report file: {e}")

    # Return appropriate exit code
    overall_success = (
        results["environment"]["all_required_present"]
        and results["connectivity"]["connectivity"]
        and results["command_execution"]["success"]
        and results["framework_integration"]["integration_complete"]
    )

    if overall_success:
        print("\n🎉 Kali shell integration validation completed successfully!")
        return 0
    else:
        print("\n⚠️  Kali shell integration requires attention - see report above")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
