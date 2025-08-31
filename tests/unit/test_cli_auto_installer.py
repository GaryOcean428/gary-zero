"""
Unit tests for CLI auto-installer functionality.

Tests the detection, installation, and management of CLI tools
with mock environments and version checking.
"""

import os
import subprocess
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from framework.helpers.cli_auto_installer import (
    ClaudeCodeCLIInstaller,
    CLIInstaller,
    CLIManager,
    GeminiCLIInstaller,
    OpenAICodexCLIInstaller,
    QwenCoderCLIInstaller,
)
from framework.helpers.cli_startup_integration import (
    cli_health_check,
    get_cli_environment_variables,
    initialize_cli_tools,
    setup_cli_paths_in_config,
    verify_cli_installation,
)


class TestCLIInstaller(unittest.TestCase):
    """Test cases for the base CLIInstaller class."""

    def setUp(self):
        self.config = {"cli_path": "test-cli", "auto_install": True}
        self.installer = CLIInstaller("test-cli", self.config)

    def test_init(self):
        """Test CLI installer initialization."""
        self.assertEqual(self.installer.name, "test-cli")
        self.assertEqual(self.installer.config, self.config)
        self.assertTrue(self.installer.tmp_bin_path.exists())

    @patch("framework.helpers.cli_auto_installer.CLIInstaller._run_command")
    async def test_detect_cli_success(self, mock_run_command):
        """Test successful CLI detection."""
        mock_run_command.return_value = {
            "success": True,
            "output": "test-cli version 1.0.0",
            "error": "",
            "returncode": 0,
        }

        available, path = await self.installer.detect_cli()

        self.assertTrue(available)
        self.assertEqual(path, "test-cli")
        mock_run_command.assert_called_with(["test-cli", "--version"], timeout=10)

    @patch("framework.helpers.cli_auto_installer.CLIInstaller._run_command")
    async def test_detect_cli_not_found(self, mock_run_command):
        """Test CLI detection when CLI is not found."""
        mock_run_command.return_value = {
            "success": False,
            "output": "",
            "error": "command not found",
            "returncode": 1,
        }

        available, error = await self.installer.detect_cli()

        self.assertFalse(available)
        self.assertIn("not found", error)

    @patch("framework.helpers.cli_auto_installer.CLIInstaller._install_cli")
    async def test_auto_install_enabled(self, mock_install_cli):
        """Test auto-installation when enabled."""
        mock_install_cli.return_value = (True, "Installation successful")

        success, message = await self.installer.auto_install()

        self.assertTrue(success)
        self.assertIn("installed successfully", message)
        mock_install_cli.assert_called_once()

    async def test_auto_install_disabled(self):
        """Test auto-installation when disabled."""
        self.installer.config["auto_install"] = False

        success, message = await self.installer.auto_install()

        self.assertFalse(success)
        self.assertIn("Auto-install disabled", message)

    async def test_install_cli_not_implemented(self):
        """Test that base _install_cli raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            await self.installer._install_cli()

    @patch("asyncio.create_subprocess_exec")
    async def test_run_command_success(self, mock_subprocess):
        """Test successful command execution."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"output\n", b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        result = await self.installer._run_command(["echo", "test"])

        self.assertTrue(result["success"])
        self.assertEqual(result["output"], "output")
        self.assertEqual(result["returncode"], 0)

    @patch("asyncio.create_subprocess_exec")
    async def test_run_command_timeout(self, mock_subprocess):
        """Test command execution timeout."""
        mock_process = AsyncMock()
        mock_process.communicate.side_effect = TimeoutError()
        mock_process.kill = AsyncMock()
        mock_process.wait = AsyncMock()
        mock_subprocess.return_value = mock_process

        result = await self.installer._run_command(["sleep", "10"], timeout=1)

        self.assertFalse(result["success"])
        self.assertIn("timed out", result["error"])
        self.assertEqual(result["returncode"], -1)


class TestGeminiCLIInstaller(unittest.TestCase):
    """Test cases for the Gemini CLI installer."""

    def setUp(self):
        self.config = {"cli_path": "gemini", "auto_install": True}
        self.installer = GeminiCLIInstaller(self.config)

    def test_init(self):
        """Test Gemini CLI installer initialization."""
        self.assertEqual(self.installer.name, "gemini")

    @patch("framework.helpers.cli_auto_installer.GeminiCLIInstaller._run_command")
    async def test_install_cli_success(self, mock_run_command):
        """Test successful Gemini CLI installation."""
        # Mock pip install success
        mock_run_command.side_effect = [
            {"success": True, "output": "Successfully installed", "error": ""},
            {"success": True, "output": "/usr/local/bin/gemini", "error": ""},
        ]

        success, message = await self.installer._install_cli()

        self.assertTrue(success)
        self.assertIn("Installed and linked", message)

    @patch("framework.helpers.cli_auto_installer.GeminiCLIInstaller._run_command")
    async def test_install_cli_pip_failure(self, mock_run_command):
        """Test Gemini CLI installation failure during pip install."""
        mock_run_command.return_value = {
            "success": False,
            "output": "",
            "error": "pip install failed",
        }

        success, message = await self.installer._install_cli()

        self.assertFalse(success)
        self.assertEqual(message, "pip install failed")


class TestClaudeCodeCLIInstaller(unittest.TestCase):
    """Test cases for the Claude Code CLI installer."""

    def setUp(self):
        self.config = {"cli_path": "claude-code", "auto_install": True}
        self.installer = ClaudeCodeCLIInstaller(self.config)

    def test_init(self):
        """Test Claude Code CLI installer initialization."""
        self.assertEqual(self.installer.name, "claude-code")

    @patch("framework.helpers.cli_auto_installer.ClaudeCodeCLIInstaller._run_command")
    async def test_install_cli_success(self, mock_run_command):
        """Test successful Claude Code CLI installation."""
        # Mock npm install success
        mock_run_command.side_effect = [
            {"success": True, "output": "Successfully installed", "error": ""},
            {"success": True, "output": "/usr/local/bin/claude-code", "error": ""},
        ]

        success, message = await self.installer._install_cli()

        self.assertTrue(success)
        self.assertIn("Installed and linked", message)


class TestOpenAICodexCLIInstaller(unittest.TestCase):
    """Test cases for the OpenAI Codex CLI installer."""

    def setUp(self):
        self.config = {"cli_path": "codex", "auto_install": True}
        self.installer = OpenAICodexCLIInstaller(self.config)

    def test_init(self):
        """Test OpenAI Codex CLI installer initialization."""
        self.assertEqual(self.installer.name, "codex")

    @patch("framework.helpers.cli_auto_installer.OpenAICodexCLIInstaller._run_command")
    async def test_install_cli_success(self, mock_run_command):
        """Test successful OpenAI Codex CLI installation."""
        # Mock npm install success
        mock_run_command.side_effect = [
            {"success": True, "output": "Successfully installed", "error": ""},
            {"success": True, "output": "/usr/local/bin/codex", "error": ""},
        ]

        success, message = await self.installer._install_cli()

        self.assertTrue(success)
        self.assertIn("Installed and linked", message)


class TestQwenCoderCLIInstaller(unittest.TestCase):
    """Test cases for the Qwen Coder CLI installer."""

    def setUp(self):
        self.config = {"cli_path": "qwen-coder", "auto_install": True}
        self.installer = QwenCoderCLIInstaller(self.config)

    def test_init(self):
        """Test Qwen Coder CLI installer initialization."""
        self.assertEqual(self.installer.name, "qwen-coder")

    @patch("framework.helpers.cli_auto_installer.QwenCoderCLIInstaller._run_command")
    async def test_install_cli_success(self, mock_run_command):
        """Test successful Qwen Coder CLI installation."""
        # Mock pip install success
        mock_run_command.side_effect = [
            {"success": True, "output": "Successfully installed", "error": ""},
            {"success": True, "output": "/usr/local/bin/qwen-coder", "error": ""},
        ]

        success, message = await self.installer._install_cli()

        self.assertTrue(success)
        self.assertIn("Installed and linked", message)


class TestCLIManager(unittest.TestCase):
    """Test cases for the CLI manager."""

    def setUp(self):
        self.config = {
            "gemini_cli": {"cli_path": "gemini", "auto_install": True},
            "claude_cli": {"cli_path": "claude-code", "auto_install": True},
            "codex_cli": {"cli_path": "codex", "auto_install": True},
            "qwen_cli": {"cli_path": "qwen-coder", "auto_install": True},
        }
        self.manager = CLIManager(self.config)

    def test_init(self):
        """Test CLI manager initialization."""
        self.assertEqual(len(self.manager.installers), 4)
        self.assertIn("gemini", self.manager.installers)
        self.assertIn("claude-code", self.manager.installers)
        self.assertIn("codex", self.manager.installers)
        self.assertIn("qwen-coder", self.manager.installers)

    @patch("framework.helpers.cli_auto_installer.CLIManager._initialize_cli")
    async def test_initialize_all(self, mock_initialize_cli):
        """Test initializing all CLI tools."""
        mock_initialize_cli.return_value = {
            "name": "test-cli",
            "available": True,
            "path": "/usr/local/bin/test-cli",
            "auto_installed": False,
            "error": None,
        }

        results = await self.manager.initialize_all()

        self.assertEqual(len(results), 4)
        self.assertEqual(mock_initialize_cli.call_count, 4)

    def test_get_cli_status(self):
        """Test getting CLI status."""
        # Set some environment variables
        os.environ["GEMINI_CLI_PATH"] = "/usr/local/bin/gemini"
        os.environ["CODEX_CLI_PATH"] = "/usr/local/bin/codex"

        status = self.manager.get_cli_status()

        self.assertEqual(len(status), 4)
        self.assertTrue(status["gemini"]["available"])
        self.assertTrue(status["codex"]["available"])
        self.assertFalse(status["claude-code"]["available"])
        self.assertFalse(status["qwen-coder"]["available"])

        # Clean up environment variables
        os.environ.pop("GEMINI_CLI_PATH", None)
        os.environ.pop("CODEX_CLI_PATH", None)


class TestCLIStartupIntegration(unittest.TestCase):
    """Test cases for CLI startup integration."""

    def setUp(self):
        self.config = {
            "gemini_cli_path": "gemini",
            "gemini_cli_auto_install": True,
            "claude_cli_path": "claude-code",
            "claude_cli_auto_install": True,
            "codex_cli_path": "codex",
            "codex_cli_auto_install": True,
            "qwen_cli_path": "qwen-coder",
            "qwen_cli_auto_install": True,
        }

    @patch("framework.helpers.cli_startup_integration.CLIManager")
    async def test_initialize_cli_tools(self, mock_cli_manager_class):
        """Test CLI tools initialization during startup."""
        mock_manager = AsyncMock()
        mock_manager.initialize_all.return_value = {
            "gemini": {"available": True, "path": "/usr/local/bin/gemini"},
            "claude-code": {"available": False, "error": "Not found"},
        }
        mock_cli_manager_class.return_value = mock_manager

        results = await initialize_cli_tools(self.config)

        self.assertIn("gemini", results)
        self.assertIn("claude-code", results)
        mock_manager.initialize_all.assert_called_once()

    def test_get_cli_environment_variables(self):
        """Test getting CLI environment variables."""
        # Set some environment variables
        os.environ["GEMINI_CLI_PATH"] = "/usr/local/bin/gemini"
        os.environ["QWEN_CODER_CLI_PATH"] = "/usr/local/bin/qwen-coder"

        env_vars = get_cli_environment_variables()

        self.assertIn("GEMINI_CLI_PATH", env_vars)
        self.assertIn("QWEN_CODER_CLI_PATH", env_vars)
        self.assertEqual(env_vars["GEMINI_CLI_PATH"], "/usr/local/bin/gemini")

        # Clean up environment variables
        os.environ.pop("GEMINI_CLI_PATH", None)
        os.environ.pop("QWEN_CODER_CLI_PATH", None)

    @patch("subprocess.run")
    def test_verify_cli_installation_success(self, mock_subprocess):
        """Test successful CLI installation verification."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        os.environ["GEMINI_CLI_PATH"] = "/usr/local/bin/gemini"

        result = verify_cli_installation("gemini")

        self.assertTrue(result)
        mock_subprocess.assert_called_with(
            ["/usr/local/bin/gemini", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Clean up
        os.environ.pop("GEMINI_CLI_PATH", None)

    def test_verify_cli_installation_no_env_var(self):
        """Test CLI installation verification when environment variable is not set."""
        result = verify_cli_installation("nonexistent-cli")

        self.assertFalse(result)

    @patch("framework.helpers.cli_startup_integration.verify_cli_installation")
    async def test_cli_health_check(self, mock_verify):
        """Test CLI health check."""
        mock_verify.side_effect = [True, False, True, False]

        health_status = await cli_health_check()

        self.assertEqual(len(health_status), 4)
        self.assertTrue(health_status["gemini"])
        self.assertFalse(health_status["claude-code"])
        self.assertTrue(health_status["codex"])
        self.assertFalse(health_status["qwen-coder"])

    def test_setup_cli_paths_in_config(self):
        """Test setting up CLI paths in configuration from environment variables."""
        # Set environment variables
        os.environ["GEMINI_CLI_PATH"] = "/custom/gemini"
        os.environ["CODEX_CLI_PATH"] = "/custom/codex"

        config = {"gemini_cli_path": "gemini", "codex_cli_path": "codex"}
        updated_config = setup_cli_paths_in_config(config)

        self.assertEqual(updated_config["gemini_cli_path"], "/custom/gemini")
        self.assertEqual(updated_config["codex_cli_path"], "/custom/codex")

        # Clean up
        os.environ.pop("GEMINI_CLI_PATH", None)
        os.environ.pop("CODEX_CLI_PATH", None)


class TestCLIVersionStubs(unittest.TestCase):
    """Test version checking stubs for CLI tools."""

    def test_gemini_version_stub(self):
        """Test Gemini CLI version stub."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Google Gemini CLI v1.0.0\n"
            )

            result = subprocess.run(
                ["gemini", "--version"], capture_output=True, text=True
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("Gemini CLI", result.stdout)

    def test_claude_code_version_stub(self):
        """Test Claude Code CLI version stub."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Claude Code CLI v1.2.0\n"
            )

            result = subprocess.run(
                ["claude-code", "--version"], capture_output=True, text=True
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("Claude Code CLI", result.stdout)

    def test_codex_version_stub(self):
        """Test OpenAI Codex CLI version stub."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="OpenAI Codex CLI v0.8.5\n"
            )

            result = subprocess.run(
                ["codex", "--version"], capture_output=True, text=True
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("Codex CLI", result.stdout)

    def test_qwen_coder_version_stub(self):
        """Test Qwen Coder CLI version stub."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Qwen Coder CLI v2.1.0\n"
            )

            result = subprocess.run(
                ["qwen-coder", "--version"], capture_output=True, text=True
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("Qwen Coder CLI", result.stdout)


if __name__ == "__main__":
    unittest.main()
