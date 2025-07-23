"""
Claude Code Tool for Advanced Code Editing and Terminal Operations.

This tool integrates Claude Code capabilities for context-aware 
multi-file editing, Git operations, terminal commands, and includes
approval workflows for security.
"""

import asyncio
import os
from typing import Any

from pydantic import BaseModel, Field

from framework.helpers.print_style import PrintStyle
from framework.helpers.tool import Response, Tool
from framework.security import RiskLevel, require_approval


class ClaudeCodeConfig(BaseModel):
    """Configuration for Claude Code tool."""
    enabled: bool = Field(default=False, description="Enable Claude Code functionality")
    max_file_size: int = Field(default=1024*1024, description="Maximum file size to process (bytes)")
    allowed_extensions: list[str] = Field(
        default=[".py", ".js", ".ts", ".html", ".css", ".json", ".md", ".txt", ".yml", ".yaml", ".toml"],
        description="Allowed file extensions for editing"
    )
    restricted_paths: list[str] = Field(
        default=[".git", "node_modules", "__pycache__", ".venv", "venv"],
        description="Restricted directories"
    )
    enable_git_ops: bool = Field(default=True, description="Enable Git operations")
    enable_terminal: bool = Field(default=True, description="Enable terminal commands")


class FileOperation(BaseModel):
    """File operation model."""
    operation: str = Field(description="Operation type: read, write, create, delete, list")
    path: str = Field(description="File or directory path")
    content: str | None = Field(default=None, description="File content for write/create")
    encoding: str = Field(default="utf-8", description="File encoding")


class GitOperation(BaseModel):
    """Git operation model."""
    operation: str = Field(description="Git operation: status, add, commit, push, pull, branch, log")
    args: list[str] = Field(default=[], description="Additional arguments")
    message: str | None = Field(default=None, description="Commit message")


class TerminalOperation(BaseModel):
    """Terminal operation model."""
    command: str = Field(description="Terminal command to execute")
    cwd: str | None = Field(default=None, description="Working directory")
    timeout: int = Field(default=30, description="Command timeout in seconds")


class ClaudeCode(Tool):
    """Claude Code tool for advanced code editing and operations."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = ClaudeCodeConfig()
        self.workspace_root = os.getcwd()

    @require_approval("code_execution", RiskLevel.HIGH, "Execute code operations with file system access")
    async def execute(self, **kwargs) -> Response:
        """Execute Claude Code operation with approval workflow."""
        try:
            # Extract user_id for approval system
            user_id = kwargs.get('user_id', 'system')

            # Check if tool is enabled
            if not self.config.enabled:
                return Response(
                    message="Claude Code tool is disabled. Enable it in settings to use code editing features.",
                    break_loop=False
                )

            operation_type = self.args.get("operation_type", "file")

            if operation_type == "file":
                result = await self.handle_file_operation()
            elif operation_type == "git":
                result = await self.handle_git_operation()
            elif operation_type == "terminal":
                user_id = kwargs.get('user_id', 'system')
                result = await self.handle_terminal_operation(user_id)
            elif operation_type == "workspace":
                result = await self.handle_workspace_operation()
            else:
                result = f"Unknown operation type: {operation_type}"

            return Response(message=result, break_loop=False)

        except Exception as e:
            error_msg = f"Claude Code error: {str(e)}"
            PrintStyle(font_color="red").print(error_msg)
            return Response(message=error_msg, break_loop=False)

    async def handle_file_operation(self) -> str:
        """Handle file operations."""
        try:
            operation = self.args.get("operation", "read")
            path = self.args.get("path", "")

            if not path:
                return "No file path provided"

            # Normalize and validate path
            full_path = self.resolve_path(path)
            if not self.is_path_allowed(full_path):
                return f"Access denied to path: {path}"

            if operation == "read":
                return await self.read_file(full_path)
            elif operation == "write":
                content = self.args.get("content", "")
                user_id = self.args.get("user_id", "system")
                return await self.write_file(full_path, content, user_id)
            elif operation == "create":
                content = self.args.get("content", "")
                return await self.create_file(full_path, content)
            elif operation == "delete":
                user_id = self.args.get("user_id", "system")
                return await self.delete_file(full_path, user_id)
            elif operation == "list":
                return await self.list_directory(full_path)
            else:
                return f"Unknown file operation: {operation}"

        except Exception as e:
            return f"File operation failed: {str(e)}"

    async def handle_git_operation(self) -> str:
        """Handle Git operations."""
        try:
            if not self.config.enable_git_ops:
                return "Git operations are disabled"

            operation = self.args.get("operation", "status")

            if operation == "status":
                return await self.git_status()
            elif operation == "add":
                files_to_add = self.args.get("files", [])
                return await self.git_add(files_to_add)
            elif operation == "commit":
                message = self.args.get("message", "")
                return await self.git_commit(message)
            elif operation == "push":
                return await self.git_push()
            elif operation == "pull":
                return await self.git_pull()
            elif operation == "branch":
                return await self.git_branch()
            elif operation == "log":
                limit = int(self.args.get("limit", 10))
                return await self.git_log(limit)
            else:
                return f"Unknown git operation: {operation}"

        except Exception as e:
            return f"Git operation failed: {str(e)}"

    @require_approval("shell_command", RiskLevel.HIGH, "Execute terminal command")
    async def handle_terminal_operation(self, user_id: str = "system") -> str:
        """Handle terminal operations with approval requirement."""
        try:
            if not self.config.enable_terminal:
                return "Terminal operations are disabled"

            command = self.args.get("command", "")
            if not command:
                return "No command provided"

            cwd = self.args.get("cwd", self.workspace_root)
            timeout = int(self.args.get("timeout", 30))

            return await self.execute_terminal_command(command, cwd, timeout)

        except Exception as e:
            return f"Terminal operation failed: {str(e)}"

    async def handle_workspace_operation(self) -> str:
        """Handle workspace-level operations."""
        try:
            operation = self.args.get("operation", "info")

            if operation == "info":
                return await self.get_workspace_info()
            elif operation == "search":
                pattern = self.args.get("pattern", "")
                return await self.search_files(pattern)
            elif operation == "tree":
                max_depth = int(self.args.get("max_depth", 3))
                return await self.get_directory_tree(max_depth)
            else:
                return f"Unknown workspace operation: {operation}"

        except Exception as e:
            return f"Workspace operation failed: {str(e)}"

    def resolve_path(self, path: str) -> str:
        """Resolve relative path to absolute path."""
        if os.path.isabs(path):
            return path
        return os.path.abspath(os.path.join(self.workspace_root, path))

    def is_path_allowed(self, path: str) -> bool:
        """Check if path is allowed for operations."""
        try:
            # Check if path is within workspace
            rel_path = os.path.relpath(path, self.workspace_root)
            if rel_path.startswith(".."):
                return False

            # Check restricted paths
            for restricted in self.config.restricted_paths:
                if restricted in rel_path:
                    return False

            return True
        except Exception:
            return False

    async def read_file(self, path: str) -> str:
        """Read file content."""
        try:
            if not os.path.exists(path):
                return f"File not found: {path}"

            if not os.path.isfile(path):
                return f"Path is not a file: {path}"

            # Check file size
            file_size = os.path.getsize(path)
            if file_size > self.config.max_file_size:
                return f"File too large: {file_size} bytes (max: {self.config.max_file_size})"

            # Check file extension
            _, ext = os.path.splitext(path)
            if ext and ext.lower() not in self.config.allowed_extensions:
                return f"File type not allowed: {ext}"

            with open(path, encoding='utf-8') as f:
                content = f.read()

            return f"File content of {path}:\n```\n{content}\n```"

        except UnicodeDecodeError:
            return f"Cannot read file (binary or encoding issue): {path}"
        except Exception as e:
            return f"Failed to read file: {str(e)}"

    @require_approval("file_write", RiskLevel.MEDIUM, "Write content to file")
    async def write_file(self, path: str, content: str, user_id: str = "system") -> str:
        """Write content to file with approval requirement."""
        try:
            if not os.path.exists(path):
                return f"File not found: {path}"

            # Check file extension
            _, ext = os.path.splitext(path)
            if ext and ext.lower() not in self.config.allowed_extensions:
                return f"File type not allowed: {ext}"

            # Create backup
            backup_path = f"{path}.backup"
            if os.path.exists(path):
                with open(path, encoding='utf-8') as f:
                    backup_content = f.read()
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(backup_content)

            # Write new content
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

            return f"Successfully wrote {len(content)} characters to {path}"

        except Exception as e:
            return f"Failed to write file: {str(e)}"

    async def create_file(self, path: str, content: str = "") -> str:
        """Create new file."""
        try:
            if os.path.exists(path):
                return f"File already exists: {path}"

            # Check file extension
            _, ext = os.path.splitext(path)
            if ext and ext.lower() not in self.config.allowed_extensions:
                return f"File type not allowed: {ext}"

            # Ensure directory exists
            os.makedirs(os.path.dirname(path), exist_ok=True)

            # Create file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

            return f"Successfully created file: {path}"

        except Exception as e:
            return f"Failed to create file: {str(e)}"

    @require_approval("file_delete", RiskLevel.HIGH, "Delete file or directory")
    async def delete_file(self, path: str, user_id: str = "system") -> str:
        """Delete file with approval requirement."""
        try:
            if not os.path.exists(path):
                return f"File not found: {path}"

            if os.path.isdir(path):
                return f"Cannot delete directory with file operation: {path}"

            os.remove(path)
            return f"Successfully deleted file: {path}"

        except Exception as e:
            return f"Failed to delete file: {str(e)}"

    async def list_directory(self, path: str) -> str:
        """List directory contents."""
        try:
            if not os.path.exists(path):
                return f"Directory not found: {path}"

            if not os.path.isdir(path):
                return f"Path is not a directory: {path}"

            items = []
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    items.append(f"📁 {item}/")
                else:
                    size = os.path.getsize(item_path)
                    items.append(f"📄 {item} ({size} bytes)")

            return f"Contents of {path}:\n" + "\n".join(items)

        except Exception as e:
            return f"Failed to list directory: {str(e)}"

    async def git_status(self) -> str:
        """Get Git status."""
        result = await self.run_git_command(["status", "--porcelain"])
        if result["returncode"] == 0:
            if result["stdout"]:
                return f"Git status:\n{result['stdout']}"
            else:
                return "Working directory clean"
        else:
            return f"Git status failed: {result['stderr']}"

    async def git_add(self, files: list[str]) -> str:
        """Add files to Git."""
        if not files:
            files = ["."]

        result = await self.run_git_command(["add"] + files)
        if result["returncode"] == 0:
            return f"Successfully added files: {', '.join(files)}"
        else:
            return f"Git add failed: {result['stderr']}"

    async def git_commit(self, message: str) -> str:
        """Commit changes."""
        if not message:
            return "Commit message required"

        result = await self.run_git_command(["commit", "-m", message])
        if result["returncode"] == 0:
            return f"Successfully committed: {message}"
        else:
            return f"Git commit failed: {result['stderr']}"

    async def git_push(self) -> str:
        """Push changes."""
        result = await self.run_git_command(["push"])
        if result["returncode"] == 0:
            return "Successfully pushed changes"
        else:
            return f"Git push failed: {result['stderr']}"

    async def git_pull(self) -> str:
        """Pull changes."""
        result = await self.run_git_command(["pull"])
        if result["returncode"] == 0:
            return f"Successfully pulled changes:\n{result['stdout']}"
        else:
            return f"Git pull failed: {result['stderr']}"

    async def git_branch(self) -> str:
        """List branches."""
        result = await self.run_git_command(["branch", "-a"])
        if result["returncode"] == 0:
            return f"Git branches:\n{result['stdout']}"
        else:
            return f"Git branch failed: {result['stderr']}"

    async def git_log(self, limit: int = 10) -> str:
        """Get Git log."""
        result = await self.run_git_command(["log", "--oneline", f"-{limit}"])
        if result["returncode"] == 0:
            return f"Recent commits:\n{result['stdout']}"
        else:
            return f"Git log failed: {result['stderr']}"

    async def run_git_command(self, args: list[str]) -> dict[str, Any]:
        """Run Git command."""
        try:
            process = await asyncio.create_subprocess_exec(
                "git", *args,
                cwd=self.workspace_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            return {
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8').strip(),
                "stderr": stderr.decode('utf-8').strip()
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }

    async def execute_terminal_command(self, command: str, cwd: str, timeout: int) -> str:
        """Execute terminal command."""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            result = f"Command: {command}\n"
            result += f"Exit code: {process.returncode}\n"

            if stdout:
                result += f"Output:\n{stdout.decode('utf-8')}\n"

            if stderr:
                result += f"Error:\n{stderr.decode('utf-8')}\n"

            return result

        except TimeoutError:
            return f"Command timed out after {timeout} seconds"
        except Exception as e:
            return f"Command execution failed: {str(e)}"

    async def get_workspace_info(self) -> str:
        """Get workspace information."""
        try:
            info = []
            info.append(f"Workspace root: {self.workspace_root}")

            # Check if it's a Git repository
            if os.path.exists(os.path.join(self.workspace_root, ".git")):
                info.append("Git repository: Yes")

                # Get current branch
                result = await self.run_git_command(["branch", "--show-current"])
                if result["returncode"] == 0:
                    info.append(f"Current branch: {result['stdout']}")
            else:
                info.append("Git repository: No")

            # Count files
            file_count = 0
            for root, dirs, files in os.walk(self.workspace_root):
                # Skip restricted directories
                dirs[:] = [d for d in dirs if d not in self.config.restricted_paths]
                file_count += len(files)

            info.append(f"Total files: {file_count}")

            return "\n".join(info)

        except Exception as e:
            return f"Failed to get workspace info: {str(e)}"

    async def search_files(self, pattern: str) -> str:
        """Search for files matching pattern."""
        try:
            if not pattern:
                return "Search pattern required"

            matches = []
            for root, dirs, files in os.walk(self.workspace_root):
                # Skip restricted directories
                dirs[:] = [d for d in dirs if d not in self.config.restricted_paths]

                for file in files:
                    if pattern.lower() in file.lower():
                        rel_path = os.path.relpath(os.path.join(root, file), self.workspace_root)
                        matches.append(rel_path)

            if matches:
                return f"Files matching '{pattern}':\n" + "\n".join(matches[:50])
            else:
                return f"No files found matching '{pattern}'"

        except Exception as e:
            return f"Search failed: {str(e)}"

    async def get_directory_tree(self, max_depth: int = 3) -> str:
        """Get directory tree structure."""
        try:
            def build_tree(path: str, prefix: str = "", depth: int = 0) -> list[str]:
                if depth >= max_depth:
                    return []

                items = []
                try:
                    entries = sorted(os.listdir(path))
                    entries = [e for e in entries if e not in self.config.restricted_paths]

                    for i, entry in enumerate(entries):
                        entry_path = os.path.join(path, entry)
                        is_last = i == len(entries) - 1

                        current_prefix = "└── " if is_last else "├── "
                        items.append(f"{prefix}{current_prefix}{entry}")

                        if os.path.isdir(entry_path) and depth < max_depth - 1:
                            next_prefix = prefix + ("    " if is_last else "│   ")
                            items.extend(build_tree(entry_path, next_prefix, depth + 1))

                except PermissionError:
                    pass

                return items

            tree_lines = [os.path.basename(self.workspace_root)]
            tree_lines.extend(build_tree(self.workspace_root))

            return "\n".join(tree_lines)

        except Exception as e:
            return f"Failed to build directory tree: {str(e)}"

    async def before_execution(self, **kwargs):
        """Pre-execution setup."""
        await super().before_execution(**kwargs)

        PrintStyle(font_color="blue", bold=True).print(
            "🔧 Claude Code tool: Advanced code editing and terminal operations"
        )
