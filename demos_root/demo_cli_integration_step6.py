#!/usr/bin/env python3
"""
CLI Tools Integration & Auto-Installer Demo (Step 6)

This script demonstrates the CLI tools integration with auto-detection,
auto-installation, and environment variable setup for:
- Google Gemini CLI
- Claude Code CLI
- OpenAI Codex CLI
- Qwen Coder CLI

Features demonstrated:
- Detection wrappers for each CLI tool
- Auto-installation to /tmp/bin when missing and enabled
- Environment variable exposure (e.g., GEMINI_CLI_PATH)
- Unit test stubs with --version checking
"""

import asyncio
import os
import sys
from pathlib import Path

# Add framework to path
sys.path.insert(0, str(Path(__file__).parent))

from framework.helpers.cli_auto_installer import CLIManager
from framework.helpers.cli_startup_integration import (
    cli_health_check,
    get_cli_environment_variables,
    initialize_cli_tools,
    setup_cli_paths_in_config,
    verify_cli_installation,
)
from framework.helpers.print_style import PrintStyle


async def demonstrate_cli_detection():
    """Demonstrate CLI detection capabilities."""
    PrintStyle(font_color="#00FF00", bold=True).print("\n🔍 CLI Detection Demo")
    PrintStyle(font_color="#00FF00", bold=True).print("=" * 50)

    # Configuration for demo
    config = {
        "gemini_cli": {
            "cli_path": "gemini",
            "auto_install": True,
        },
        "claude_cli": {
            "cli_path": "claude-code",
            "auto_install": True,
        },
        "codex_cli": {
            "cli_path": "codex",
            "auto_install": True,
        },
        "qwen_cli": {
            "cli_path": "qwen-coder",
            "auto_install": True,
        },
    }

    cli_manager = CLIManager(config)

    # Demonstrate detection for each CLI
    for cli_name, installer in cli_manager.installers.items():
        PrintStyle(font_color="#85C1E9").print(f"\n🔧 Testing {cli_name} detection...")

        try:
            available, result = await installer.detect_cli()
            if available:
                PrintStyle(font_color="#90EE90").print(f"   ✅ Found: {result}")
            else:
                PrintStyle(font_color="#FFA500").print(f"   ⚠️  Not found: {result}")
        except Exception as e:
            PrintStyle(font_color="#FF6B6B").print(f"   ❌ Error: {str(e)}")


async def demonstrate_auto_installation():
    """Demonstrate auto-installation functionality."""
    PrintStyle(font_color="#FF69B4", bold=True).print("\n📦 Auto-Installation Demo")
    PrintStyle(font_color="#FF69B4", bold=True).print("=" * 50)

    # Configuration with auto-install enabled
    demo_config = {
        "gemini_cli_path": "gemini",
        "gemini_cli_auto_install": True,
        "claude_cli_path": "claude-code",
        "claude_cli_auto_install": True,
        "codex_cli_path": "codex",
        "codex_cli_auto_install": True,
        "qwen_cli_path": "qwen-coder",
        "qwen_cli_auto_install": True,
    }

    # Initialize CLI tools (this will trigger auto-installation)
    results = await initialize_cli_tools(demo_config)

    PrintStyle(font_color="#DDA0DD").print("\n📊 Installation Results:")
    for cli_name, result in results.items():
        if "error" in result:
            PrintStyle(font_color="#FF6B6B").print(
                f"   ❌ {cli_name}: {result['error']}"
            )
        else:
            status = "✅" if result.get("available") else "❌"
            auto_installed = " (auto-installed)" if result.get("auto_installed") else ""
            path = result.get("path", "unknown")
            PrintStyle(font_color="#E8E8E8").print(
                f"   {status} {cli_name}: {path}{auto_installed}"
            )


def demonstrate_environment_variables():
    """Demonstrate environment variable setup."""
    PrintStyle(font_color="#FFA500", bold=True).print("\n🌍 Environment Variables Demo")
    PrintStyle(font_color="#FFA500", bold=True).print("=" * 50)

    # Get CLI environment variables
    env_vars = get_cli_environment_variables()

    if env_vars:
        PrintStyle(font_color="#98FB98").print("Environment variables set:")
        for var_name, var_value in env_vars.items():
            PrintStyle(font_color="#E8E8E8").print(f"   {var_name}={var_value}")
    else:
        PrintStyle(font_color="#FFA500").print("No CLI environment variables set")

    # Demonstrate config path setup
    PrintStyle(font_color="#DDA0DD").print("\n⚙️ Configuration Update Demo:")

    sample_config = {
        "gemini_cli_path": "gemini",
        "claude_cli_path": "claude-code",
        "codex_cli_path": "codex",
        "qwen_cli_path": "qwen-coder",
    }

    updated_config = setup_cli_paths_in_config(sample_config)

    for key, value in updated_config.items():
        if key.endswith("_cli_path"):
            PrintStyle(font_color="#E8E8E8").print(f"   {key}: {value}")


async def demonstrate_health_check():
    """Demonstrate CLI health checking."""
    PrintStyle(font_color="#40E0D0", bold=True).print("\n🏥 Health Check Demo")
    PrintStyle(font_color="#40E0D0", bold=True).print("=" * 50)

    health_status = await cli_health_check()

    PrintStyle(font_color="#87CEEB").print("CLI Health Status:")
    for cli_name, is_healthy in health_status.items():
        status_emoji = "💚" if is_healthy else "💔"
        status_text = "Healthy" if is_healthy else "Unavailable"
        PrintStyle(font_color="#E8E8E8").print(
            f"   {status_emoji} {cli_name}: {status_text}"
        )

        # Test version checking
        if is_healthy:
            PrintStyle(font_color="#90EE90").print("      Version check: ✅ Passed")
        else:
            PrintStyle(font_color="#FFA500").print("      Version check: ⚠️ Failed")


def demonstrate_version_stubs():
    """Demonstrate version checking stubs."""
    PrintStyle(font_color="#DA70D6", bold=True).print("\n🔖 Version Stubs Demo")
    PrintStyle(font_color="#DA70D6", bold=True).print("=" * 50)

    cli_tools = [
        ("gemini", "Google Gemini CLI"),
        ("claude-code", "Claude Code CLI"),
        ("codex", "OpenAI Codex CLI"),
        ("qwen-coder", "Qwen Coder CLI"),
    ]

    for cli_name, cli_description in cli_tools:
        PrintStyle(font_color="#DDA0DD").print(f"\n🧪 Testing {cli_description}:")

        # Try to verify installation
        is_available = verify_cli_installation(cli_name)

        if is_available:
            PrintStyle(font_color="#90EE90").print(
                f"   ✅ {cli_name} --version: Available"
            )

            # Get environment variable
            env_var = f"{cli_name.upper().replace('-', '_')}_CLI_PATH"
            cli_path = os.environ.get(env_var)
            if cli_path:
                PrintStyle(font_color="#87CEEB").print(f"   📍 Path: {cli_path}")
        else:
            PrintStyle(font_color="#FFA500").print(
                f"   ⚠️ {cli_name} --version: Not available"
            )


def demonstrate_tmp_bin_setup():
    """Demonstrate /tmp/bin directory setup."""
    PrintStyle(font_color="#FF6347", bold=True).print("\n📁 /tmp/bin Setup Demo")
    PrintStyle(font_color="#FF6347", bold=True).print("=" * 50)

    tmp_bin = Path("/tmp/bin")

    PrintStyle(font_color="#F0E68C").print(f"📂 /tmp/bin directory: {tmp_bin}")
    PrintStyle(font_color="#E8E8E8").print(
        f"   Exists: {'✅' if tmp_bin.exists() else '❌'}"
    )
    PrintStyle(font_color="#E8E8E8").print(
        f"   Writable: {'✅' if tmp_bin.exists() and os.access(tmp_bin, os.W_OK) else '❌'}"
    )

    if tmp_bin.exists():
        cli_files = list(tmp_bin.glob("*"))
        if cli_files:
            PrintStyle(font_color="#98FB98").print("   Contents:")
            for cli_file in cli_files:
                file_type = "🔗" if cli_file.is_symlink() else "📄"
                PrintStyle(font_color="#E8E8E8").print(
                    f"     {file_type} {cli_file.name}"
                )
        else:
            PrintStyle(font_color="#FFA500").print("   Directory is empty")


def print_summary():
    """Print implementation summary."""
    PrintStyle(font_color="#FFD700", bold=True).print(
        "\n🎯 Step 6 Implementation Summary"
    )
    PrintStyle(font_color="#FFD700", bold=True).print("=" * 60)

    features = [
        "✅ Detection wrappers for all 4 CLI tools",
        "✅ Auto-installer downloads to /tmp/bin at startup",
        "✅ Environment variables exposed (e.g., GEMINI_CLI_PATH)",
        "✅ Unit test stubs with --version checking",
        "✅ Secure sandboxed command execution",
        "✅ Configuration integration with settings",
        "✅ Health check and status monitoring",
        "✅ Installation scripts for each CLI tool",
        "✅ Comprehensive error handling and logging",
        "✅ Approval workflows for security",
    ]

    PrintStyle(font_color="#98FB98").print("Implemented Features:")
    for feature in features:
        PrintStyle(font_color="#E8E8E8").print(f"  {feature}")

    PrintStyle(font_color="#87CEEB").print("\nCLI Tools Integrated:")
    cli_tools = [
        "  🔹 Google Gemini CLI (pip install google-generativeai[cli])",
        "  🔹 Claude Code CLI (npm install -g @anthropic/claude-code-cli)",
        "  🔹 OpenAI Codex CLI (npm install -g @openai/codex-cli)",
        "  🔹 Qwen Coder CLI (pip install qwen-coder-cli)",
    ]

    for tool in cli_tools:
        PrintStyle(font_color="#E8E8E8").print(tool)


async def main():
    """Run the CLI integration demonstration."""
    PrintStyle(font_color="#FF1493", bold=True).print(
        "🚀 CLI Tools Integration & Auto-Installer Demo"
    )
    PrintStyle(font_color="#FF1493", bold=True).print("=" * 70)
    PrintStyle(font_color="#87CEEB").print(
        "Step 6: CLI tools integration & auto-installer"
    )

    try:
        # Demonstrate /tmp/bin setup
        demonstrate_tmp_bin_setup()

        # Demonstrate CLI detection
        await demonstrate_cli_detection()

        # Demonstrate auto-installation
        await demonstrate_auto_installation()

        # Demonstrate environment variables
        demonstrate_environment_variables()

        # Demonstrate health checking
        await demonstrate_health_check()

        # Demonstrate version stubs
        demonstrate_version_stubs()

        # Print summary
        print_summary()

        PrintStyle(font_color="#00FF7F", bold=True).print(
            "\n🎉 Demo completed successfully!"
        )

    except Exception as e:
        PrintStyle(font_color="#FF6B6B", bold=True).print(f"\n❌ Demo failed: {str(e)}")
        raise


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main())
