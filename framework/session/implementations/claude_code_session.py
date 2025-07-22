"""
Claude Code Session Implementation.

Provides session management for Claude Code tool operations including
file editing, Git operations, and terminal commands.
"""

import asyncio
import os
import uuid
from typing import Any

from ..session_interface import (
    SessionInterface,
    SessionMessage,
    SessionResponse,
    SessionState,
    SessionType,
)


class ClaudeCodeSession(SessionInterface):
    """Session implementation for Claude Code operations."""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize Claude Code session.
        
        Args:
            config: Configuration dictionary with Claude Code settings
        """
        session_id = str(uuid.uuid4())
        super().__init__(session_id, SessionType.TERMINAL, config)

        self.max_file_size = config.get('max_file_size', 1024*1024)
        self.allowed_extensions = config.get('allowed_extensions', ['.py', '.js', '.ts', '.html', '.css', '.json', '.md', '.txt', '.yml', '.yaml', '.toml'])
        self.restricted_paths = config.get('restricted_paths', ['.git', 'node_modules', '__pycache__', '.venv', 'venv'])
        self.enable_git_ops = config.get('enable_git_ops', True)
        self.enable_terminal = config.get('enable_terminal', True)

        # Working directory
        self.workspace_root = os.getcwd()

        # State tracking
        self._connected = False

    async def connect(self) -> SessionResponse:
        """
        Establish connection to file system and tools.
        
        Returns:
            SessionResponse indicating connection success or failure
        """
        try:
            await self.update_state(SessionState.INITIALIZING)

            # Verify workspace access
            if not os.path.exists(self.workspace_root):
                await self.update_state(SessionState.ERROR, "Workspace not accessible")
                return SessionResponse(
                    success=False,
                    message="Workspace directory not accessible",
                    error=f"Directory not found: {self.workspace_root}",
                    session_id=self.session_id
                )

            # Test basic file operations
            try:
                test_file = os.path.join(self.workspace_root, f".test_access_{self.session_id}")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
            except Exception as file_error:
                await self.update_state(SessionState.ERROR, str(file_error))
                return SessionResponse(
                    success=False,
                    message="File system access test failed",
                    error=str(file_error),
                    session_id=self.session_id
                )

            # Test Git availability if enabled
            git_available = False
            if self.enable_git_ops:
                try:
                    result = await self._run_command(['git', '--version'], timeout=5)
                    git_available = result['returncode'] == 0
                except Exception:
                    pass

            self._connected = True
            await self.update_state(SessionState.CONNECTED)

            return SessionResponse(
                success=True,
                message="Connected to Claude Code environment",
                data={
                    'workspace_root': self.workspace_root,
                    'git_available': git_available,
                    'terminal_enabled': self.enable_terminal
                },
                session_id=self.session_id
            )

        except Exception as e:
            await self.update_state(SessionState.ERROR, str(e))
            return SessionResponse(
                success=False,
                message=f"Connection failed: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )

    async def disconnect(self) -> SessionResponse:
        """
        Disconnect from Claude Code environment.
        
        Returns:
            SessionResponse indicating disconnection status
        """
        self._connected = False
        await self.update_state(SessionState.DISCONNECTED)

        return SessionResponse(
            success=True,
            message="Disconnected from Claude Code environment",
            session_id=self.session_id
        )

    async def execute(self, message: SessionMessage) -> SessionResponse:
        """
        Execute a Claude Code operation.
        
        Args:
            message: Message containing the operation to execute
            
        Returns:
            SessionResponse with operation results
        """
        try:
            if not self._connected:
                return SessionResponse(
                    success=False,
                    message="Claude Code environment not connected",
                    error="Environment not connected",
                    session_id=self.session_id
                )

            await self.update_state(SessionState.ACTIVE)

            operation_type = message.payload.get('operation_type', 'file')

            if operation_type == 'file':
                return await self._handle_file_operation(message.payload)
            elif operation_type == 'git':
                return await self._handle_git_operation(message.payload)
            elif operation_type == 'terminal':
                return await self._handle_terminal_operation(message.payload)
            elif operation_type == 'workspace':
                return await self._handle_workspace_operation(message.payload)
            else:
                return SessionResponse(
                    success=False,
                    message=f"Unknown operation type: {operation_type}",
                    error=f"Unsupported operation: {operation_type}",
                    session_id=self.session_id
                )

        except Exception as e:
            await self.update_state(SessionState.ERROR, str(e))
            return SessionResponse(
                success=False,
                message=f"Execution failed: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )
        finally:
            await self.update_state(SessionState.IDLE)

    async def health_check(self) -> SessionResponse:
        """
        Check if the Claude Code session is healthy.
        
        Returns:
            SessionResponse indicating session health
        """
        try:
            if not self._connected:
                return SessionResponse(
                    success=False,
                    message="Environment not connected",
                    session_id=self.session_id
                )

            # Test basic file system access
            if not os.path.exists(self.workspace_root):
                return SessionResponse(
                    success=False,
                    message="Workspace no longer accessible",
                    error=f"Directory not found: {self.workspace_root}",
                    session_id=self.session_id
                )

            return SessionResponse(
                success=True,
                message="Session healthy",
                session_id=self.session_id
            )

        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Health check failed: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )

    async def _handle_file_operation(self, payload: dict[str, Any]) -> SessionResponse:
        """Handle file operations."""
        operation = payload.get('operation', 'read')
        path = payload.get('path', '')

        if not path:
            return SessionResponse(
                success=False,
                message="No file path provided",
                error="Missing path parameter",
                session_id=self.session_id
            )

        # Normalize and validate path
        full_path = self._resolve_path(path)
        if not self._is_path_allowed(full_path):
            return SessionResponse(
                success=False,
                message=f"Access denied to path: {path}",
                error="Path not allowed",
                session_id=self.session_id
            )

        try:
            if operation == 'read':
                return await self._read_file(full_path)
            elif operation == 'write':
                content = payload.get('content', '')
                return await self._write_file(full_path, content)
            elif operation == 'create':
                content = payload.get('content', '')
                return await self._create_file(full_path, content)
            elif operation == 'delete':
                return await self._delete_file(full_path)
            elif operation == 'list':
                return await self._list_directory(full_path)
            else:
                return SessionResponse(
                    success=False,
                    message=f"Unknown file operation: {operation}",
                    error=f"Unsupported file operation: {operation}",
                    session_id=self.session_id
                )
        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"File operation failed: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )

    async def _handle_git_operation(self, payload: dict[str, Any]) -> SessionResponse:
        """Handle Git operations."""
        if not self.enable_git_ops:
            return SessionResponse(
                success=False,
                message="Git operations are disabled",
                error="Git operations disabled in configuration",
                session_id=self.session_id
            )

        operation = payload.get('operation', 'status')

        try:
            if operation == 'status':
                return await self._git_status()
            elif operation == 'add':
                files = payload.get('files', [])
                return await self._git_add(files)
            elif operation == 'commit':
                message = payload.get('message', '')
                return await self._git_commit(message)
            elif operation == 'push':
                return await self._git_push()
            elif operation == 'pull':
                return await self._git_pull()
            elif operation == 'branch':
                return await self._git_branch()
            elif operation == 'log':
                limit = int(payload.get('limit', 10))
                return await self._git_log(limit)
            else:
                return SessionResponse(
                    success=False,
                    message=f"Unknown git operation: {operation}",
                    error=f"Unsupported git operation: {operation}",
                    session_id=self.session_id
                )
        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Git operation failed: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )

    async def _handle_terminal_operation(self, payload: dict[str, Any]) -> SessionResponse:
        """Handle terminal operations."""
        if not self.enable_terminal:
            return SessionResponse(
                success=False,
                message="Terminal operations are disabled",
                error="Terminal operations disabled in configuration",
                session_id=self.session_id
            )

        command = payload.get('command', '')
        if not command:
            return SessionResponse(
                success=False,
                message="No command provided",
                error="Missing command parameter",
                session_id=self.session_id
            )

        cwd = payload.get('cwd', self.workspace_root)
        timeout = int(payload.get('timeout', 30))

        try:
            result = await self._execute_terminal_command(command, cwd, timeout)
            return SessionResponse(
                success=True,
                message="Terminal command executed",
                data=result,
                session_id=self.session_id
            )
        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Terminal command failed: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )

    async def _handle_workspace_operation(self, payload: dict[str, Any]) -> SessionResponse:
        """Handle workspace-level operations."""
        operation = payload.get('operation', 'info')

        try:
            if operation == 'info':
                return await self._get_workspace_info()
            elif operation == 'search':
                pattern = payload.get('pattern', '')
                return await self._search_files(pattern)
            elif operation == 'tree':
                max_depth = int(payload.get('max_depth', 3))
                return await self._get_directory_tree(max_depth)
            else:
                return SessionResponse(
                    success=False,
                    message=f"Unknown workspace operation: {operation}",
                    error=f"Unsupported workspace operation: {operation}",
                    session_id=self.session_id
                )
        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Workspace operation failed: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )

    def _resolve_path(self, path: str) -> str:
        """Resolve relative path to absolute path."""
        if os.path.isabs(path):
            return path
        return os.path.abspath(os.path.join(self.workspace_root, path))

    def _is_path_allowed(self, path: str) -> bool:
        """Check if path is allowed for operations."""
        try:
            # Check if path is within workspace
            rel_path = os.path.relpath(path, self.workspace_root)
            if rel_path.startswith('..'):
                return False

            # Check restricted paths
            for restricted in self.restricted_paths:
                if restricted in rel_path:
                    return False

            return True
        except Exception:
            return False

    async def _read_file(self, path: str) -> SessionResponse:
        """Read file content."""
        try:
            if not os.path.exists(path):
                return SessionResponse(
                    success=False,
                    message=f"File not found: {path}",
                    error="File not found",
                    session_id=self.session_id
                )

            if not os.path.isfile(path):
                return SessionResponse(
                    success=False,
                    message=f"Path is not a file: {path}",
                    error="Not a file",
                    session_id=self.session_id
                )

            # Check file size
            file_size = os.path.getsize(path)
            if file_size > self.max_file_size:
                return SessionResponse(
                    success=False,
                    message=f"File too large: {file_size} bytes (max: {self.max_file_size})",
                    error="File too large",
                    session_id=self.session_id
                )

            # Check file extension
            _, ext = os.path.splitext(path)
            if ext and ext.lower() not in self.allowed_extensions:
                return SessionResponse(
                    success=False,
                    message=f"File type not allowed: {ext}",
                    error="File type not allowed",
                    session_id=self.session_id
                )

            with open(path, encoding='utf-8') as f:
                content = f.read()

            return SessionResponse(
                success=True,
                message=f"Read file: {path}",
                data={'content': content, 'size': file_size},
                session_id=self.session_id
            )

        except UnicodeDecodeError:
            return SessionResponse(
                success=False,
                message=f"Cannot read file (binary or encoding issue): {path}",
                error="Encoding error",
                session_id=self.session_id
            )
        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Failed to read file: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )

    async def _write_file(self, path: str, content: str) -> SessionResponse:
        """Write content to file."""
        try:
            if not os.path.exists(path):
                return SessionResponse(
                    success=False,
                    message=f"File not found: {path}",
                    error="File not found",
                    session_id=self.session_id
                )

            # Check file extension
            _, ext = os.path.splitext(path)
            if ext and ext.lower() not in self.allowed_extensions:
                return SessionResponse(
                    success=False,
                    message=f"File type not allowed: {ext}",
                    error="File type not allowed",
                    session_id=self.session_id
                )

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

            return SessionResponse(
                success=True,
                message=f"Successfully wrote {len(content)} characters to {path}",
                data={'bytes_written': len(content.encode('utf-8'))},
                session_id=self.session_id
            )

        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Failed to write file: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )

    async def _create_file(self, path: str, content: str = "") -> SessionResponse:
        """Create new file."""
        try:
            if os.path.exists(path):
                return SessionResponse(
                    success=False,
                    message=f"File already exists: {path}",
                    error="File already exists",
                    session_id=self.session_id
                )

            # Check file extension
            _, ext = os.path.splitext(path)
            if ext and ext.lower() not in self.allowed_extensions:
                return SessionResponse(
                    success=False,
                    message=f"File type not allowed: {ext}",
                    error="File type not allowed",
                    session_id=self.session_id
                )

            # Ensure directory exists
            os.makedirs(os.path.dirname(path), exist_ok=True)

            # Create file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

            return SessionResponse(
                success=True,
                message=f"Successfully created file: {path}",
                data={'bytes_written': len(content.encode('utf-8'))},
                session_id=self.session_id
            )

        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Failed to create file: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )

    async def _delete_file(self, path: str) -> SessionResponse:
        """Delete file."""
        try:
            if not os.path.exists(path):
                return SessionResponse(
                    success=False,
                    message=f"File not found: {path}",
                    error="File not found",
                    session_id=self.session_id
                )

            if os.path.isdir(path):
                return SessionResponse(
                    success=False,
                    message=f"Cannot delete directory with file operation: {path}",
                    error="Cannot delete directory",
                    session_id=self.session_id
                )

            os.remove(path)

            return SessionResponse(
                success=True,
                message=f"Successfully deleted file: {path}",
                session_id=self.session_id
            )

        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Failed to delete file: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )

    async def _list_directory(self, path: str) -> SessionResponse:
        """List directory contents."""
        try:
            if not os.path.exists(path):
                return SessionResponse(
                    success=False,
                    message=f"Directory not found: {path}",
                    error="Directory not found",
                    session_id=self.session_id
                )

            if not os.path.isdir(path):
                return SessionResponse(
                    success=False,
                    message=f"Path is not a directory: {path}",
                    error="Not a directory",
                    session_id=self.session_id
                )

            items = []
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    items.append({'name': item, 'type': 'directory'})
                else:
                    size = os.path.getsize(item_path)
                    items.append({'name': item, 'type': 'file', 'size': size})

            return SessionResponse(
                success=True,
                message=f"Listed directory: {path}",
                data={'items': items, 'count': len(items)},
                session_id=self.session_id
            )

        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Failed to list directory: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )

    async def _git_status(self) -> SessionResponse:
        """Get Git status."""
        result = await self._run_git_command(['status', '--porcelain'])
        if result['returncode'] == 0:
            status_output = result['stdout']
            return SessionResponse(
                success=True,
                message="Git status retrieved",
                data={'status': status_output, 'clean': not bool(status_output.strip())},
                session_id=self.session_id
            )
        else:
            return SessionResponse(
                success=False,
                message="Git status failed",
                error=result['stderr'],
                session_id=self.session_id
            )

    async def _git_add(self, files: list) -> SessionResponse:
        """Add files to Git."""
        if not files:
            files = ['.']

        result = await self._run_git_command(['add'] + files)
        if result['returncode'] == 0:
            return SessionResponse(
                success=True,
                message=f"Successfully added files: {', '.join(files)}",
                data={'files_added': files},
                session_id=self.session_id
            )
        else:
            return SessionResponse(
                success=False,
                message="Git add failed",
                error=result['stderr'],
                session_id=self.session_id
            )

    async def _git_commit(self, message: str) -> SessionResponse:
        """Commit changes."""
        if not message:
            return SessionResponse(
                success=False,
                message="Commit message required",
                error="No commit message provided",
                session_id=self.session_id
            )

        result = await self._run_git_command(['commit', '-m', message])
        if result['returncode'] == 0:
            return SessionResponse(
                success=True,
                message=f"Successfully committed: {message}",
                data={'commit_message': message},
                session_id=self.session_id
            )
        else:
            return SessionResponse(
                success=False,
                message="Git commit failed",
                error=result['stderr'],
                session_id=self.session_id
            )

    async def _git_push(self) -> SessionResponse:
        """Push changes."""
        result = await self._run_git_command(['push'])
        if result['returncode'] == 0:
            return SessionResponse(
                success=True,
                message="Successfully pushed changes",
                data={'output': result['stdout']},
                session_id=self.session_id
            )
        else:
            return SessionResponse(
                success=False,
                message="Git push failed",
                error=result['stderr'],
                session_id=self.session_id
            )

    async def _git_pull(self) -> SessionResponse:
        """Pull changes."""
        result = await self._run_git_command(['pull'])
        if result['returncode'] == 0:
            return SessionResponse(
                success=True,
                message="Successfully pulled changes",
                data={'output': result['stdout']},
                session_id=self.session_id
            )
        else:
            return SessionResponse(
                success=False,
                message="Git pull failed",
                error=result['stderr'],
                session_id=self.session_id
            )

    async def _git_branch(self) -> SessionResponse:
        """List branches."""
        result = await self._run_git_command(['branch', '-a'])
        if result['returncode'] == 0:
            return SessionResponse(
                success=True,
                message="Git branches retrieved",
                data={'branches': result['stdout']},
                session_id=self.session_id
            )
        else:
            return SessionResponse(
                success=False,
                message="Git branch failed",
                error=result['stderr'],
                session_id=self.session_id
            )

    async def _git_log(self, limit: int = 10) -> SessionResponse:
        """Get Git log."""
        result = await self._run_git_command(['log', '--oneline', f'-{limit}'])
        if result['returncode'] == 0:
            return SessionResponse(
                success=True,
                message="Git log retrieved",
                data={'commits': result['stdout']},
                session_id=self.session_id
            )
        else:
            return SessionResponse(
                success=False,
                message="Git log failed",
                error=result['stderr'],
                session_id=self.session_id
            )

    async def _run_git_command(self, args: list) -> dict[str, Any]:
        """Run Git command."""
        return await self._run_command(['git'] + args)

    async def _execute_terminal_command(self, command: str, cwd: str, timeout: int) -> dict[str, Any]:
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

            return {
                'command': command,
                'returncode': process.returncode,
                'stdout': stdout.decode('utf-8'),
                'stderr': stderr.decode('utf-8'),
                'success': process.returncode == 0
            }

        except TimeoutError:
            return {
                'command': command,
                'returncode': -1,
                'stdout': '',
                'stderr': f'Command timed out after {timeout} seconds',
                'success': False
            }
        except Exception as e:
            return {
                'command': command,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'success': False
            }

    async def _run_command(self, cmd: list, timeout: int = 60) -> dict[str, Any]:
        """Run a command asynchronously."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.workspace_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            return {
                'returncode': process.returncode,
                'stdout': stdout.decode('utf-8').strip(),
                'stderr': stderr.decode('utf-8').strip()
            }

        except TimeoutError:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': f'Command timed out after {timeout} seconds'
            }
        except Exception as e:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }

    async def _get_workspace_info(self) -> SessionResponse:
        """Get workspace information."""
        try:
            info = {
                'workspace_root': self.workspace_root,
                'git_repository': os.path.exists(os.path.join(self.workspace_root, '.git'))
            }

            # Get current branch if Git repo
            if info['git_repository']:
                result = await self._run_git_command(['branch', '--show-current'])
                if result['returncode'] == 0:
                    info['current_branch'] = result['stdout']

            # Count files
            file_count = 0
            for root, dirs, files in os.walk(self.workspace_root):
                # Skip restricted directories
                dirs[:] = [d for d in dirs if d not in self.restricted_paths]
                file_count += len(files)

            info['total_files'] = file_count

            return SessionResponse(
                success=True,
                message="Workspace information retrieved",
                data=info,
                session_id=self.session_id
            )

        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Failed to get workspace info: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )

    async def _search_files(self, pattern: str) -> SessionResponse:
        """Search for files matching pattern."""
        try:
            if not pattern:
                return SessionResponse(
                    success=False,
                    message="Search pattern required",
                    error="No pattern provided",
                    session_id=self.session_id
                )

            matches = []
            for root, dirs, files in os.walk(self.workspace_root):
                # Skip restricted directories
                dirs[:] = [d for d in dirs if d not in self.restricted_paths]

                for file in files:
                    if pattern.lower() in file.lower():
                        rel_path = os.path.relpath(os.path.join(root, file), self.workspace_root)
                        matches.append(rel_path)

            return SessionResponse(
                success=True,
                message=f"Search completed for pattern: {pattern}",
                data={'matches': matches[:50], 'total_matches': len(matches)},  # Limit to first 50
                session_id=self.session_id
            )

        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Search failed: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )

    async def _get_directory_tree(self, max_depth: int = 3) -> SessionResponse:
        """Get directory tree structure."""
        try:
            def build_tree(path: str, prefix: str = "", depth: int = 0) -> list:
                if depth >= max_depth:
                    return []

                items = []
                try:
                    entries = sorted(os.listdir(path))
                    entries = [e for e in entries if e not in self.restricted_paths]

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

            return SessionResponse(
                success=True,
                message="Directory tree generated",
                data={'tree': '\n'.join(tree_lines)},
                session_id=self.session_id
            )

        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Failed to build directory tree: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )
