"""Tests for Claude Code tool."""

import os
import tempfile
from unittest.mock import AsyncMock, Mock, patch

import pytest

from framework.tools.claude_code import ClaudeCode, ClaudeCodeConfig


class TestClaudeCode:
    """Test Claude Code tool functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_agent = Mock()
        self.mock_agent.agent_name = "test_agent"
        self.mock_agent.context = Mock()
        self.mock_agent.context.log = Mock()
        self.mock_agent.context.log.log = Mock()
        self.mock_agent.hist_add_tool_result = Mock()

        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temp directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_tool_creation(self):
        """Test tool creation and configuration."""
        tool = ClaudeCode(
            agent=self.mock_agent,
            name="claude_code",
            method="file",
            args={"operation_type": "file", "operation": "read", "path": "test.py"},
            message="Read file",
        )

        assert tool.name == "claude_code"
        assert tool.method == "file"
        assert isinstance(tool.config, ClaudeCodeConfig)
        assert tool.config.enabled is False  # Default disabled for safety

    @pytest.mark.asyncio
    async def test_disabled_tool(self):
        """Test tool behavior when disabled."""
        tool = ClaudeCode(
            agent=self.mock_agent,
            name="claude_code",
            method="file",
            args={"operation_type": "file", "operation": "read", "path": "test.py"},
            message="Read file",
        )

        # Tool should be disabled by default
        response = await tool.execute()
        assert "disabled" in response.message.lower()
        assert response.break_loop is False

    @pytest.mark.asyncio
    async def test_file_read_operation(self):
        """Test file read operation."""
        # Create test file
        test_file = os.path.join(self.temp_dir, "test.py")
        test_content = "print('Hello, World!')"
        with open(test_file, "w") as f:
            f.write(test_content)

        tool = ClaudeCode(
            agent=self.mock_agent,
            name="claude_code",
            method="file",
            args={"operation_type": "file", "operation": "read", "path": test_file},
            message="Read file",
        )

        # Enable the tool and set workspace
        tool.config.enabled = True
        tool.workspace_root = self.temp_dir

        response = await tool.execute()

        # Should successfully read file
        assert test_content in response.message
        assert "File content of" in response.message

    @pytest.mark.asyncio
    async def test_file_write_operation(self):
        """Test file write operation."""
        # Create test file
        test_file = os.path.join(self.temp_dir, "test.py")
        original_content = "print('Original')"
        new_content = "print('Modified')"

        with open(test_file, "w") as f:
            f.write(original_content)

        tool = ClaudeCode(
            agent=self.mock_agent,
            name="claude_code",
            method="file",
            args={
                "operation_type": "file",
                "operation": "write",
                "path": test_file,
                "content": new_content,
            },
            message="Write file",
        )

        # Enable the tool and set workspace
        tool.config.enabled = True
        tool.workspace_root = self.temp_dir

        response = await tool.execute()

        # Should successfully write file
        assert "Successfully wrote" in response.message

        # Verify file content changed
        with open(test_file) as f:
            assert f.read() == new_content

        # Check backup was created
        backup_file = f"{test_file}.backup"
        assert os.path.exists(backup_file)
        with open(backup_file) as f:
            assert f.read() == original_content

    @pytest.mark.asyncio
    async def test_file_create_operation(self):
        """Test file create operation."""
        test_file = os.path.join(self.temp_dir, "new_file.py")
        test_content = "# New file content"

        tool = ClaudeCode(
            agent=self.mock_agent,
            name="claude_code",
            method="file",
            args={
                "operation_type": "file",
                "operation": "create",
                "path": test_file,
                "content": test_content,
            },
            message="Create file",
        )

        # Enable the tool and set workspace
        tool.config.enabled = True
        tool.workspace_root = self.temp_dir

        response = await tool.execute()

        # Should successfully create file
        assert "Successfully created file" in response.message
        assert os.path.exists(test_file)

        with open(test_file) as f:
            assert f.read() == test_content

    @pytest.mark.asyncio
    async def test_directory_list_operation(self):
        """Test directory listing operation."""
        # Create test files
        test_files = ["file1.py", "file2.txt", "subdir/file3.md"]
        for file_path in test_files:
            full_path = os.path.join(self.temp_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write("test content")

        tool = ClaudeCode(
            agent=self.mock_agent,
            name="claude_code",
            method="file",
            args={"operation_type": "file", "operation": "list", "path": self.temp_dir},
            message="List directory",
        )

        # Enable the tool and set workspace
        tool.config.enabled = True
        tool.workspace_root = self.temp_dir

        response = await tool.execute()

        # Should list directory contents
        assert "Contents of" in response.message
        assert "file1.py" in response.message
        assert "file2.txt" in response.message

    @pytest.mark.asyncio
    @patch("framework.tools.claude_code.asyncio.create_subprocess_exec")
    async def test_git_status_operation(self, mock_subprocess):
        """Test Git status operation."""
        # Mock successful git status
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"?? untracked_file.py\n", b"")
        mock_subprocess.return_value = mock_process

        tool = ClaudeCode(
            agent=self.mock_agent,
            name="claude_code",
            method="git",
            args={"operation_type": "git", "operation": "status"},
            message="Git status",
        )

        # Enable the tool
        tool.config.enabled = True
        tool.workspace_root = self.temp_dir

        response = await tool.execute()

        # Should show git status
        assert "Git status:" in response.message
        assert "untracked_file.py" in response.message

    @pytest.mark.asyncio
    @patch("framework.tools.claude_code.asyncio.create_subprocess_shell")
    async def test_terminal_operation(self, mock_subprocess):
        """Test terminal command execution."""
        # Mock successful command execution
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"Hello from terminal\n", b"")
        mock_subprocess.return_value = mock_process

        tool = ClaudeCode(
            agent=self.mock_agent,
            name="claude_code",
            method="terminal",
            args={
                "operation_type": "terminal",
                "command": "echo 'Hello from terminal'",
            },
            message="Run terminal command",
        )

        # Enable the tool
        tool.config.enabled = True
        tool.workspace_root = self.temp_dir

        response = await tool.execute()

        # Should show command output
        assert "Command: echo 'Hello from terminal'" in response.message
        assert "Hello from terminal" in response.message

    @pytest.mark.asyncio
    async def test_workspace_info_operation(self):
        """Test workspace info operation."""
        tool = ClaudeCode(
            agent=self.mock_agent,
            name="claude_code",
            method="workspace",
            args={"operation_type": "workspace", "operation": "info"},
            message="Get workspace info",
        )

        # Enable the tool
        tool.config.enabled = True
        tool.workspace_root = self.temp_dir

        response = await tool.execute()

        # Should show workspace info
        assert "Workspace root:" in response.message
        assert self.temp_dir in response.message
        assert "Git repository:" in response.message

    @pytest.mark.asyncio
    async def test_restricted_path_access(self):
        """Test that restricted paths are blocked."""
        tool = ClaudeCode(
            agent=self.mock_agent,
            name="claude_code",
            method="file",
            args={
                "operation_type": "file",
                "operation": "read",
                "path": "../etc/passwd",
            },
            message="Read restricted file",
        )

        # Enable the tool
        tool.config.enabled = True
        tool.workspace_root = self.temp_dir

        response = await tool.execute()

        # Should deny access
        assert "Access denied" in response.message

    @pytest.mark.asyncio
    async def test_disallowed_file_extension(self):
        """Test that disallowed file extensions are blocked."""
        # Create test file with disallowed extension
        test_file = os.path.join(self.temp_dir, "test.exe")
        with open(test_file, "wb") as f:
            f.write(b"binary content")

        tool = ClaudeCode(
            agent=self.mock_agent,
            name="claude_code",
            method="file",
            args={"operation_type": "file", "operation": "read", "path": test_file},
            message="Read binary file",
        )

        # Enable the tool
        tool.config.enabled = True
        tool.workspace_root = self.temp_dir

        response = await tool.execute()

        # Should deny access to disallowed file type
        assert "File type not allowed" in response.message

    @pytest.mark.asyncio
    async def test_git_operations_disabled(self):
        """Test Git operations when disabled."""
        tool = ClaudeCode(
            agent=self.mock_agent,
            name="claude_code",
            method="git",
            args={"operation_type": "git", "operation": "status"},
            message="Git status",
        )

        # Enable the tool but disable git operations
        tool.config.enabled = True
        tool.config.enable_git_ops = False

        response = await tool.execute()

        # Should deny git operations
        assert "Git operations are disabled" in response.message

    @pytest.mark.asyncio
    async def test_terminal_operations_disabled(self):
        """Test terminal operations when disabled."""
        tool = ClaudeCode(
            agent=self.mock_agent,
            name="claude_code",
            method="terminal",
            args={"operation_type": "terminal", "command": "ls"},
            message="List files",
        )

        # Enable the tool but disable terminal operations
        tool.config.enabled = True
        tool.config.enable_terminal = False

        response = await tool.execute()

        # Should deny terminal operations
        assert "Terminal operations are disabled" in response.message

    @pytest.mark.asyncio
    async def test_file_size_limit(self):
        """Test file size limit enforcement."""
        # Create large test file
        test_file = os.path.join(self.temp_dir, "large_file.txt")
        with open(test_file, "w") as f:
            f.write("x" * 2048)  # 2KB file

        tool = ClaudeCode(
            agent=self.mock_agent,
            name="claude_code",
            method="file",
            args={"operation_type": "file", "operation": "read", "path": test_file},
            message="Read large file",
        )

        # Enable the tool with small file size limit
        tool.config.enabled = True
        tool.config.max_file_size = 1024  # 1KB limit
        tool.workspace_root = self.temp_dir

        response = await tool.execute()

        # Should deny access due to file size
        assert "File too large" in response.message

    def test_config_validation(self):
        """Test configuration validation."""
        config = ClaudeCodeConfig(
            enabled=True,
            max_file_size=2097152,  # 2MB
            enable_git_ops=False,
            enable_terminal=False,
        )

        assert config.enabled is True
        assert config.max_file_size == 2097152
        assert config.enable_git_ops is False
        assert config.enable_terminal is False

    @pytest.mark.asyncio
    async def test_unknown_operation_type(self):
        """Test handling of unknown operation types."""
        tool = ClaudeCode(
            agent=self.mock_agent,
            name="claude_code",
            method="unknown",
            args={"operation_type": "unknown_type"},
            message="Unknown operation",
        )

        # Enable the tool
        tool.config.enabled = True

        response = await tool.execute()

        # Should handle unknown operation gracefully
        assert "Unknown operation type" in response.message
