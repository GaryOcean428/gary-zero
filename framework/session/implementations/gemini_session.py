"""
Gemini CLI Session Implementation.

Provides session management for Google Gemini CLI interactions.
"""

import asyncio
import uuid
from typing import Any

from ..session_interface import (
    SessionInterface,
    SessionMessage,
    SessionResponse,
    SessionState,
    SessionType,
)


class GeminiSession(SessionInterface):
    """Session implementation for Google Gemini CLI."""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize Gemini CLI session.
        
        Args:
            config: Configuration dictionary with Gemini CLI settings
        """
        session_id = str(uuid.uuid4())
        super().__init__(session_id, SessionType.CLI, config)

        self.cli_path = config.get('cli_path', 'gemini')
        self.api_key = config.get('api_key', '')
        self.model = config.get('model', 'gemini-2.0-flash')
        self.auto_install = config.get('auto_install', False)

        # State tracking
        self._cli_available = False
        self._initialized = False

    async def connect(self) -> SessionResponse:
        """
        Establish connection to Gemini CLI.
        
        Returns:
            SessionResponse indicating connection success or failure
        """
        try:
            await self.update_state(SessionState.INITIALIZING)

            # Check if CLI is available
            result = await self._run_command([self.cli_path, '--version'], timeout=10)

            if result['returncode'] == 0:
                self._cli_available = True
                await self.update_state(SessionState.CONNECTED)
                return SessionResponse(
                    success=True,
                    message=f"Connected to Gemini CLI: {result['stdout'].strip()}",
                    session_id=self.session_id
                )
            else:
                # Try auto-install if enabled
                if self.auto_install:
                    install_result = await self._install_cli()
                    if install_result.success:
                        return await self.connect()  # Retry connection

                await self.update_state(SessionState.ERROR, f"CLI not available: {result['stderr']}")
                return SessionResponse(
                    success=False,
                    message="Gemini CLI not available",
                    error=result['stderr'],
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
        Disconnect from Gemini CLI.
        
        Returns:
            SessionResponse indicating disconnection status
        """
        await self.update_state(SessionState.DISCONNECTED)
        return SessionResponse(
            success=True,
            message="Disconnected from Gemini CLI",
            session_id=self.session_id
        )

    async def execute(self, message: SessionMessage) -> SessionResponse:
        """
        Execute a Gemini CLI command.
        
        Args:
            message: Message containing the command to execute
            
        Returns:
            SessionResponse with command results
        """
        try:
            if not self._cli_available:
                return SessionResponse(
                    success=False,
                    message="Gemini CLI not available",
                    error="CLI not connected",
                    session_id=self.session_id
                )

            await self.update_state(SessionState.ACTIVE)

            action = message.payload.get('action', 'chat')

            if action == 'chat':
                return await self._handle_chat(message.payload)
            elif action == 'code':
                return await self._handle_code(message.payload)
            elif action == 'generate':
                return await self._handle_generate(message.payload)
            elif action == 'config':
                return await self._handle_config(message.payload)
            else:
                return SessionResponse(
                    success=False,
                    message=f"Unknown action: {action}",
                    error=f"Unsupported action: {action}",
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
        Check if the Gemini CLI session is healthy.
        
        Returns:
            SessionResponse indicating session health
        """
        try:
            if not self._cli_available:
                return SessionResponse(
                    success=False,
                    message="CLI not available",
                    session_id=self.session_id
                )

            # Simple version check to verify CLI is working
            result = await self._run_command([self.cli_path, '--version'], timeout=5)

            if result['returncode'] == 0:
                return SessionResponse(
                    success=True,
                    message="Session healthy",
                    session_id=self.session_id
                )
            else:
                return SessionResponse(
                    success=False,
                    message="CLI health check failed",
                    error=result['stderr'],
                    session_id=self.session_id
                )

        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Health check failed: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )

    async def _handle_chat(self, payload: dict[str, Any]) -> SessionResponse:
        """Handle chat action."""
        message_text = payload.get('message', '')
        model = payload.get('model', self.model)

        if not message_text:
            return SessionResponse(
                success=False,
                message="No message provided for chat",
                error="Missing message parameter",
                session_id=self.session_id
            )

        cmd = [self.cli_path, 'chat', '--model', model, '--message', message_text]
        result = await self._run_command(cmd, timeout=60)

        if result['returncode'] == 0:
            return SessionResponse(
                success=True,
                message="Chat completed successfully",
                data={'response': result['stdout']},
                session_id=self.session_id
            )
        else:
            return SessionResponse(
                success=False,
                message="Chat failed",
                error=result['stderr'],
                session_id=self.session_id
            )

    async def _handle_code(self, payload: dict[str, Any]) -> SessionResponse:
        """Handle code action."""
        task = payload.get('task', '')
        language = payload.get('language', '')
        file_path = payload.get('file_path', '')

        if not task:
            return SessionResponse(
                success=False,
                message="No task provided for code action",
                error="Missing task parameter",
                session_id=self.session_id
            )

        cmd = [self.cli_path, 'code', '--task', task]
        if language:
            cmd.extend(['--language', language])
        if file_path:
            cmd.extend(['--file', file_path])

        result = await self._run_command(cmd, timeout=120)

        if result['returncode'] == 0:
            return SessionResponse(
                success=True,
                message="Code task completed successfully",
                data={'result': result['stdout']},
                session_id=self.session_id
            )
        else:
            return SessionResponse(
                success=False,
                message="Code task failed",
                error=result['stderr'],
                session_id=self.session_id
            )

    async def _handle_generate(self, payload: dict[str, Any]) -> SessionResponse:
        """Handle generate action."""
        prompt = payload.get('prompt', '')
        output_file = payload.get('output_file', '')
        format_type = payload.get('format', 'text')

        if not prompt:
            return SessionResponse(
                success=False,
                message="No prompt provided for generate action",
                error="Missing prompt parameter",
                session_id=self.session_id
            )

        cmd = [self.cli_path, 'generate', '--prompt', prompt, '--format', format_type]
        if output_file:
            cmd.extend(['--output', output_file])

        result = await self._run_command(cmd, timeout=120)

        if result['returncode'] == 0:
            return SessionResponse(
                success=True,
                message="Content generated successfully",
                data={'content': result['stdout']},
                session_id=self.session_id
            )
        else:
            return SessionResponse(
                success=False,
                message="Generation failed",
                error=result['stderr'],
                session_id=self.session_id
            )

    async def _handle_config(self, payload: dict[str, Any]) -> SessionResponse:
        """Handle config action."""
        list_config = payload.get('list', False)
        config_key = payload.get('key', '')
        config_value = payload.get('value', '')

        if list_config:
            cmd = [self.cli_path, 'config', '--list']
        elif config_key and config_value:
            cmd = [self.cli_path, 'config', '--set', f'{config_key}={config_value}']
        else:
            return SessionResponse(
                success=False,
                message="Invalid config parameters",
                error="Either use list=true or provide key and value",
                session_id=self.session_id
            )

        result = await self._run_command(cmd, timeout=30)

        if result['returncode'] == 0:
            return SessionResponse(
                success=True,
                message="Config operation completed",
                data={'output': result['stdout']},
                session_id=self.session_id
            )
        else:
            return SessionResponse(
                success=False,
                message="Config operation failed",
                error=result['stderr'],
                session_id=self.session_id
            )

    async def _install_cli(self) -> SessionResponse:
        """Install Gemini CLI via pip."""
        try:
            cmd = ['pip', 'install', 'google-generativeai[cli]']
            result = await self._run_command(cmd, timeout=300)

            if result['returncode'] == 0:
                self._cli_available = False  # Reset to trigger re-check
                return SessionResponse(
                    success=True,
                    message="Gemini CLI installed successfully",
                    data={'install_output': result['stdout']},
                    session_id=self.session_id
                )
            else:
                return SessionResponse(
                    success=False,
                    message="CLI installation failed",
                    error=result['stderr'],
                    session_id=self.session_id
                )

        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Installation error: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )

    async def _run_command(self, cmd: list, timeout: int = 60) -> dict[str, Any]:
        """
        Run a command asynchronously.
        
        Args:
            cmd: Command to run
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with command results
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            return {
                'returncode': process.returncode,
                'stdout': stdout.decode('utf-8') if stdout else '',
                'stderr': stderr.decode('utf-8') if stderr else ''
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
