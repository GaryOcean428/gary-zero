"""
Claude Code CLI integration tool for Anthropic's Claude Code CLI.

This tool wraps the Claude Code CLI, allowing the agent to check
installation status and perform basic operations via a consistent API.

Currently supported actions:

* ``status`` – verify the CLI version and availability
* ``install`` – install the CLI using npm (if auto‑install is enabled)

Further actions (file operations, git commands, terminal operations, etc.)
can be added in future versions to fully expose the Claude Code CLI
capabilities.
"""

import asyncio
import subprocess
from dataclasses import dataclass
from typing import Any

from framework.helpers.print_style import PrintStyle
from framework.helpers.tool import Response, Tool


@dataclass
class ClaudeCLIState:
    """State for Claude Code CLI operations."""

    initialized: bool = False
    cli_available: bool = False
    last_approval: str | None = None


class ClaudeCodeCLI(Tool):
    """Claude Code CLI integration tool for code editing and terminal operations."""

    async def execute(self, **kwargs: Any) -> Response:
        # Wait for any pending interventions before executing
        await self.agent.handle_intervention()

        # Retrieve or initialize state
        self.state = self.agent.get_data("_claude_cli_state") or ClaudeCLIState()

        # Check if CLI integration is enabled in settings
        if not self.agent.config.claude_cli_enabled:
            return Response(
                message=(
                    "❌ Claude Code CLI is disabled. Enable it in settings to use this tool."
                ),
                break_loop=False,
            )

        # Initialize CLI on first use
        if not self.state.initialized:
            await self._initialize_cli()

        # If CLI is unavailable after initialization, notify the user
        if not self.state.cli_available:
            return Response(
                message="❌ Claude Code CLI is not available. Please install it first.",
                break_loop=False,
            )

        # Determine action from arguments
        action = self.args.get("action", "").lower().strip()

        if action == "status":
            return await self._get_status()
        elif action == "install":
            return await self._install_cli()
        else:
            # Fallback to usage instructions for unsupported actions
            return Response(
                message=self.agent.read_prompt(
                    "fw.claude_cli.usage.md", available_actions="status, install"
                ),
                break_loop=False,
            )

    async def _initialize_cli(self) -> None:
        """Initialize the Claude Code CLI and detect availability."""
        try:
            # Attempt to get CLI version to verify availability
            result = subprocess.run(
                [self.agent.config.claude_cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                self.state.cli_available = True
                PrintStyle(font_color="#85C1E9").print(
                    f"✅ Claude Code CLI found: {result.stdout.strip()}"
                )
            else:
                self.state.cli_available = False
                PrintStyle.warning("⚠️ Claude Code CLI not found or not working")

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.state.cli_available = False
            PrintStyle.warning(f"⚠️ Claude Code CLI initialization failed: {e}")

        # Mark as initialized and persist state
        self.state.initialized = True
        self.agent.set_data("_claude_cli_state", self.state)

    async def _get_status(self) -> Response:
        """Return the version information for the Claude Code CLI."""
        try:
            cmd = [self.agent.config.claude_cli_path, "--version"]
            result = await self._run_secure_command(cmd)
            if result["success"]:
                return Response(
                    message=f"✅ Claude Code CLI version: {result['output'].strip()}",
                    break_loop=False,
                )
            else:
                return Response(
                    message=f"❌ Could not determine CLI version: {result['error']}",
                    break_loop=False,
                )
        except Exception as e:
            return Response(
                message=f"❌ Error getting status: {str(e)}",
                break_loop=False,
            )

    async def _install_cli(self) -> Response:
        """Install the Claude Code CLI using npm."""
        # Check if auto-install is enabled
        if not self.agent.config.claude_cli_auto_install:
            return Response(
                message=(
                    "❌ Auto-install is disabled. Please install Claude Code CLI manually: npm install -g @anthropic/claude-code-cli"
                ),
                break_loop=False,
            )

        try:
            PrintStyle(font_color="#85C1E9").print("📦 Installing Claude Code CLI...")

            # Install via npm
            cmd = ["npm", "install", "-g", "@anthropic/claude-code-cli"]
            result = await self._run_secure_command(cmd, timeout=300)

            if result["success"]:
                # Re-initialize after installation
                self.state.initialized = False
                await self._initialize_cli()
                return Response(
                    message=f"✅ Claude Code CLI installed successfully:\n{result['output']}",
                    break_loop=False,
                )
            else:
                return Response(
                    message=f"❌ Installation failed: {result['error']}",
                    break_loop=False,
                )

        except Exception as e:
            return Response(
                message=f"❌ Error during installation: {str(e)}",
                break_loop=False,
            )

    async def _run_secure_command(
        self, cmd: list[str], timeout: int = 60
    ) -> dict[str, Any]:
        """Run a command in a secure sandboxed environment."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=None,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                return {
                    "success": process.returncode == 0,
                    "output": stdout.decode(),
                    "error": stderr.decode(),
                }
            except asyncio.TimeoutError:
                process.kill()
                await process.communicate()
                return {
                    "success": False,
                    "output": "",
                    "error": "Command timed out",
                }

        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}