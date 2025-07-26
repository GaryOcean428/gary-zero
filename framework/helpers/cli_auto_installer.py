"""
CLI Auto-Installer Framework for Zero Agent.

This module provides automatic detection and installation of CLI tools
with secure sandboxed execution and proper error handling.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any

from framework.helpers.print_style import PrintStyle


class CLIInstaller:
    """Base class for CLI tool installation and management."""

    def __init__(self, name: str, config: dict[str, Any]):
        self.name = name
        self.config = config
        # Use proper temporary directory with secure permissions
        self.tmp_bin_path = Path(tempfile.mkdtemp(prefix=f"cli_installer_{name}_"))
        # Set secure permissions (readable/writable only by owner)
        self.tmp_bin_path.chmod(0o700)

    async def detect_cli(self) -> tuple[bool, str | None]:
        """
        Detect if CLI tool is available.

        Returns:
            Tuple of (is_available, path_or_error)
        """
        cli_path = self.config.get("cli_path", self.name)

        try:
            # First try the configured path
            result = await self._run_command([cli_path, "--version"], timeout=10)
            if result["success"]:
                PrintStyle(font_color="#85C1E9").print(
                    f"✅ {self.name} CLI found: {result['output']}"
                )
                return True, cli_path

            # Try PATH lookup
            if not os.path.isabs(cli_path):
                result = await self._run_command(["which", cli_path], timeout=5)
                if result["success"] and result["output"].strip():
                    actual_path = result["output"].strip()
                    PrintStyle(font_color="#85C1E9").print(
                        f"✅ {self.name} CLI found at: {actual_path}"
                    )
                    return True, actual_path

            # Check /tmp/bin for auto-installed CLIs
            tmp_cli_path = self.tmp_bin_path / cli_path
            if tmp_cli_path.exists():
                result = await self._run_command(
                    [str(tmp_cli_path), "--version"], timeout=10
                )
                if result["success"]:
                    PrintStyle(font_color="#85C1E9").print(
                        f"✅ {self.name} CLI found in /tmp/bin: {result['output']}"
                    )
                    return True, str(tmp_cli_path)

            return False, f"{self.name} CLI not found in PATH or /tmp/bin"

        except Exception as e:
            return False, f"Error detecting {self.name} CLI: {str(e)}"

    async def auto_install(self) -> tuple[bool, str]:
        """
        Auto-install CLI tool if enabled.

        Returns:
            Tuple of (success, message)
        """
        if not self.config.get("auto_install", False):
            return False, f"Auto-install disabled for {self.name}"

        try:
            PrintStyle(font_color="#FFA500").print(
                f"📦 Auto-installing {self.name} CLI to /tmp/bin..."
            )

            success, message = await self._install_cli()

            if success:
                # Set environment variable for the CLI path
                env_var = f"{self.name.upper().replace('-', '_')}_CLI_PATH"
                cli_path = str(self.tmp_bin_path / self.name)
                os.environ[env_var] = cli_path

                PrintStyle(font_color="#85C1E9").print(f"✅ {env_var}={cli_path}")
                return True, f"{self.name} CLI installed successfully to /tmp/bin"
            else:
                return False, f"Failed to install {self.name} CLI: {message}"

        except Exception as e:
            return False, f"Error during auto-install: {str(e)}"

    async def _install_cli(self) -> tuple[bool, str]:
        """
        Override this method in subclasses to implement specific installation logic.

        Returns:
            Tuple of (success, message)
        """
        raise NotImplementedError("Subclasses must implement _install_cli")

    async def _run_command(
        self, cmd: list[str], timeout: int = 60, cwd: str | None = None
    ) -> dict[str, Any]:
        """
        Run a command in a secure environment with timeout.

        Args:
            cmd: Command and arguments
            timeout: Timeout in seconds
            cwd: Working directory

        Returns:
            Dictionary with success, output, error, and returncode
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )

                return {
                    "success": process.returncode == 0,
                    "output": stdout.decode().strip() if stdout else "",
                    "error": stderr.decode().strip() if stderr else "",
                    "returncode": process.returncode,
                }

            except TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "output": "",
                    "error": f"Command timed out after {timeout} seconds",
                    "returncode": -1,
                }

        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "returncode": -1,
            }


class GeminiCLIInstaller(CLIInstaller):
    """Google Gemini CLI installer."""

    def __init__(self, config: dict[str, Any]):
        super().__init__("gemini", config)

    async def _install_cli(self) -> tuple[bool, str]:
        """Install Google Gemini CLI via pip."""
        try:
            # Install via pip
            result = await self._run_command(
                ["pip", "install", "google-generativeai[cli]"], timeout=300
            )

            if not result["success"]:
                return False, result["error"]

            # Create symlink in /tmp/bin if installed globally
            result = await self._run_command(["which", "gemini"], timeout=5)
            if result["success"] and result["output"].strip():
                global_path = result["output"].strip()
                local_path = self.tmp_bin_path / "gemini"

                # Create symlink
                if local_path.exists():
                    local_path.unlink()
                local_path.symlink_to(global_path)

                return True, f"Installed and linked from {global_path}"
            else:
                return False, "Installation succeeded but CLI not found in PATH"

        except Exception as e:
            return False, str(e)


class ClaudeCodeCLIInstaller(CLIInstaller):
    """Claude Code CLI installer."""

    def __init__(self, config: dict[str, Any]):
        super().__init__("claude-code", config)

    async def _install_cli(self) -> tuple[bool, str]:
        """Install Claude Code CLI via npm."""
        try:
            # Install via npm
            result = await self._run_command(
                ["npm", "install", "-g", "@anthropic/claude-code-cli"], timeout=300
            )

            if not result["success"]:
                return False, result["error"]

            # Create symlink in /tmp/bin if installed globally
            result = await self._run_command(["which", "claude-code"], timeout=5)
            if result["success"] and result["output"].strip():
                global_path = result["output"].strip()
                local_path = self.tmp_bin_path / "claude-code"

                # Create symlink
                if local_path.exists():
                    local_path.unlink()
                local_path.symlink_to(global_path)

                return True, f"Installed and linked from {global_path}"
            else:
                return False, "Installation succeeded but CLI not found in PATH"

        except Exception as e:
            return False, str(e)


class OpenAICodexCLIInstaller(CLIInstaller):
    """OpenAI Codex CLI installer."""

    def __init__(self, config: dict[str, Any]):
        super().__init__("codex", config)

    async def _install_cli(self) -> tuple[bool, str]:
        """Install OpenAI Codex CLI via npm."""
        try:
            # Install via npm
            result = await self._run_command(
                ["npm", "install", "-g", "@openai/codex-cli"], timeout=300
            )

            if not result["success"]:
                return False, result["error"]

            # Create symlink in /tmp/bin if installed globally
            result = await self._run_command(["which", "codex"], timeout=5)
            if result["success"] and result["output"].strip():
                global_path = result["output"].strip()
                local_path = self.tmp_bin_path / "codex"

                # Create symlink
                if local_path.exists():
                    local_path.unlink()
                local_path.symlink_to(global_path)

                return True, f"Installed and linked from {global_path}"
            else:
                return False, "Installation succeeded but CLI not found in PATH"

        except Exception as e:
            return False, str(e)


class QwenCoderCLIInstaller(CLIInstaller):
    """Qwen Coder CLI installer."""

    def __init__(self, config: dict[str, Any]):
        super().__init__("qwen-coder", config)

    async def _install_cli(self) -> tuple[bool, str]:
        """Install Qwen Coder CLI via pip."""
        try:
            # Install via pip
            result = await self._run_command(
                ["pip", "install", "qwen-coder-cli"], timeout=300
            )

            if not result["success"]:
                return False, result["error"]

            # Create symlink in /tmp/bin if installed globally
            result = await self._run_command(["which", "qwen-coder"], timeout=5)
            if result["success"] and result["output"].strip():
                global_path = result["output"].strip()
                local_path = self.tmp_bin_path / "qwen-coder"

                # Create symlink
                if local_path.exists():
                    local_path.unlink()
                local_path.symlink_to(global_path)

                return True, f"Installed and linked from {global_path}"
            else:
                return False, "Installation succeeded but CLI not found in PATH"

        except Exception as e:
            return False, str(e)


class CLIManager:
    """Manager for all CLI tools with auto-detection and installation."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.installers = {
            "gemini": GeminiCLIInstaller(config.get("gemini_cli", {})),
            "claude-code": ClaudeCodeCLIInstaller(config.get("claude_cli", {})),
            "codex": OpenAICodexCLIInstaller(config.get("codex_cli", {})),
            "qwen-coder": QwenCoderCLIInstaller(config.get("qwen_cli", {})),
        }

    async def initialize_all(self) -> dict[str, dict[str, Any]]:
        """
        Initialize all CLI tools with detection and auto-installation.

        Returns:
            Dictionary with results for each CLI tool
        """
        results = {}

        for cli_name, installer in self.installers.items():
            results[cli_name] = await self._initialize_cli(installer)

        return results

    async def _initialize_cli(self, installer: CLIInstaller) -> dict[str, Any]:
        """Initialize a single CLI tool."""
        result = {
            "name": installer.name,
            "available": False,
            "path": None,
            "auto_installed": False,
            "error": None,
        }

        try:
            # First try detection
            available, path_or_error = await installer.detect_cli()

            if available:
                result["available"] = True
                result["path"] = path_or_error

                # Set environment variable
                env_var = f"{installer.name.upper().replace('-', '_')}_CLI_PATH"
                os.environ[env_var] = path_or_error

            else:
                # Try auto-installation if detection failed
                success, message = await installer.auto_install()

                if success:
                    result["auto_installed"] = True
                    # Re-detect after installation
                    available, path_or_error = await installer.detect_cli()
                    if available:
                        result["available"] = True
                        result["path"] = path_or_error
                    else:
                        result["error"] = (
                            f"Installation succeeded but CLI still not detected: {path_or_error}"
                        )
                else:
                    result["error"] = message

        except Exception as e:
            result["error"] = f"Initialization failed: {str(e)}"

        return result

    def get_cli_status(self) -> dict[str, dict[str, Any]]:
        """Get status of all CLI tools including environment variables."""
        status = {}

        for cli_name in self.installers.keys():
            env_var = f"{cli_name.upper().replace('-', '_')}_CLI_PATH"
            status[cli_name] = {
                "env_var": env_var,
                "path": os.environ.get(env_var),
                "available": os.environ.get(env_var) is not None,
            }

        return status
