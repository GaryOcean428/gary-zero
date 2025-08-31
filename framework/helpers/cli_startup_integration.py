"""
CLI Startup Integration for Zero Agent.

This module handles the initialization of CLI tools during agent startup
with auto-detection, installation, and environment variable setup.
"""

import os
from typing import Any

from framework.helpers.cli_auto_installer import CLIManager
from framework.helpers.print_style import PrintStyle


async def initialize_cli_tools(config: dict[str, Any]) -> dict[str, Any]:
    """
    Initialize all CLI tools during agent startup.

    This function:
    1. Detects available CLI tools
    2. Auto-installs missing tools (if enabled)
    3. Sets up environment variables
    4. Returns initialization results

    Args:
        config: Agent configuration dictionary

    Returns:
        Dictionary with initialization results for each CLI tool
    """
    try:
        PrintStyle(font_color="#85C1E9", bold=True).print(
            "🔧 Initializing CLI tools..."
        )

        # Create CLI manager with config
        cli_config = {
            "gemini_cli": {
                "cli_path": config.get("gemini_cli_path", "gemini"),
                "auto_install": config.get("gemini_cli_auto_install", True),
            },
            "claude_cli": {
                "cli_path": config.get("claude_cli_path", "claude-code"),
                "auto_install": config.get("claude_cli_auto_install", True),
            },
            "codex_cli": {
                "cli_path": config.get("codex_cli_path", "codex"),
                "auto_install": config.get("codex_cli_auto_install", True),
            },
            "qwen_cli": {
                "cli_path": config.get("qwen_cli_path", "qwen-coder"),
                "auto_install": config.get("qwen_cli_auto_install", True),
            },
        }

        cli_manager = CLIManager(cli_config)

        # Initialize all CLI tools
        results = await cli_manager.initialize_all()

        # Log initialization results
        _log_initialization_results(results)

        # Return results for further processing
        return results

    except Exception as e:
        PrintStyle(font_color="#FF6B6B").print(
            f"❌ CLI initialization failed: {str(e)}"
        )
        return {"error": str(e)}


def _log_initialization_results(results: dict[str, dict[str, Any]]) -> None:
    """Log CLI initialization results in a formatted way."""
    try:
        available_count = sum(
            1 for result in results.values() if result.get("available", False)
        )
        total_count = len(results)

        PrintStyle(font_color="#85C1E9", bold=True).print(
            f"📊 CLI Tools Status: {available_count}/{total_count} available"
        )

        for cli_name, result in results.items():
            if result.get("available"):
                status_emoji = "✅"
                path = result.get("path", "unknown")
                auto_installed = (
                    " (auto-installed)" if result.get("auto_installed") else ""
                )
                message = f"{status_emoji} {cli_name}: {path}{auto_installed}"
            else:
                status_emoji = "❌"
                error = result.get("error", "unknown error")
                message = f"{status_emoji} {cli_name}: {error}"

            PrintStyle(font_color="#E8E8E8").print(f"   {message}")

        # Log environment variables
        env_vars = []
        for cli_name in results:
            env_var = f"{cli_name.upper().replace('-', '_')}_CLI_PATH"
            if os.environ.get(env_var):
                env_vars.append(f"{env_var}={os.environ[env_var]}")

        if env_vars:
            PrintStyle(font_color="#DDA0DD").print("🌍 Environment variables set:")
            for env_var in env_vars:
                PrintStyle(font_color="#E8E8E8").print(f"   {env_var}")

    except Exception as e:
        PrintStyle(font_color="#FF6B6B").print(f"❌ Error logging results: {str(e)}")


def get_cli_environment_variables() -> dict[str, str]:
    """
    Get all CLI-related environment variables.

    Returns:
        Dictionary of environment variable names and their values
    """
    cli_env_vars = {}

    cli_names = ["gemini", "claude-code", "codex", "qwen-coder"]

    for cli_name in cli_names:
        env_var = f"{cli_name.upper().replace('-', '_')}_CLI_PATH"
        value = os.environ.get(env_var)
        if value:
            cli_env_vars[env_var] = value

    return cli_env_vars


def verify_cli_installation(cli_name: str) -> bool:
    """
    Verify that a specific CLI tool is properly installed and available.

    Args:
        cli_name: Name of the CLI tool to verify

    Returns:
        True if CLI is available, False otherwise
    """
    try:
        env_var = f"{cli_name.upper().replace('-', '_')}_CLI_PATH"
        cli_path = os.environ.get(env_var)

        if not cli_path:
            return False

        # Try to run --version command
        import subprocess

        result = subprocess.run(
            [cli_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        return result.returncode == 0

    except Exception:
        return False


async def cli_health_check() -> dict[str, bool]:
    """
    Perform a health check on all CLI tools.

    Returns:
        Dictionary mapping CLI names to their health status
    """
    cli_names = ["gemini", "claude-code", "codex", "qwen-coder"]
    health_status = {}

    for cli_name in cli_names:
        health_status[cli_name] = verify_cli_installation(cli_name)

    return health_status


def setup_cli_paths_in_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Update configuration with CLI paths from environment variables.

    Args:
        config: Configuration dictionary to update

    Returns:
        Updated configuration dictionary
    """
    try:
        # Update paths from environment variables
        cli_mappings = [
            ("GEMINI_CLI_PATH", "gemini_cli_path"),
            ("CLAUDE_CODE_CLI_PATH", "claude_cli_path"),
            ("CODEX_CLI_PATH", "codex_cli_path"),
            ("QWEN_CODER_CLI_PATH", "qwen_cli_path"),
        ]

        for env_var, config_key in cli_mappings:
            env_value = os.environ.get(env_var)
            if env_value:
                config[config_key] = env_value

        return config

    except Exception as e:
        PrintStyle(font_color="#FF6B6B").print(
            f"❌ Error updating config with CLI paths: {str(e)}"
        )
        return config
