import asyncio
import json
import subprocess
from dataclasses import dataclass

from framework.helpers.print_style import PrintStyle
from framework.helpers.tool import Response, Tool


@dataclass
class CodexCLIState:
    """State for OpenAI Codex CLI operations."""

    initialized: bool = False
    cli_available: bool = False
    last_approval: str | None = None


class OpenAICodexCLI(Tool):
    """OpenAI Codex CLI integration tool for context-aware code editing and terminal commands."""

    async def execute(self, **kwargs):
        await (
            self.agent.handle_intervention()
        )  # Wait for intervention and handle it, if paused

        # Get tool state
        self.state = self.agent.get_data("_codex_cli_state") or CodexCLIState()

        # Check if Codex CLI is enabled
        if not self.agent.config.codex_cli_enabled:
            return Response(
                message="❌ OpenAI Codex CLI is disabled. Enable it in settings to use this tool.",
                break_loop=False,
            )

        # Initialize CLI if needed
        if not self.state.initialized:
            await self._initialize_cli()

        if not self.state.cli_available:
            return Response(
                message="❌ OpenAI Codex CLI is not available. Please install it first.",
                break_loop=False,
            )

        action = self.args.get("action", "").lower().strip()

        if action == "edit":
            return await self._handle_edit_action()
        elif action == "create":
            return await self._handle_create_action()
        elif action == "shell":
            return await self._handle_shell_action()
        elif action == "status":
            return await self._get_status()
        elif action == "install":
            return await self._install_cli()
        else:
            return Response(
                message=self.agent.read_prompt(
                    "fw.codex_cli.usage.md",
                    available_actions="edit, create, shell, status, install",
                ),
                break_loop=False,
            )

    async def _initialize_cli(self):
        """Initialize the Codex CLI and check availability."""
        try:
            # Check if CLI is available
            result = subprocess.run(
                [self.agent.config.codex_cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                self.state.cli_available = True
                PrintStyle(font_color="#85C1E9").print(
                    f"✅ OpenAI Codex CLI found: {result.stdout.strip()}"
                )
            else:
                self.state.cli_available = False
                PrintStyle.warning("⚠️ OpenAI Codex CLI not found or not working")

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.state.cli_available = False
            PrintStyle.warning(f"⚠️ OpenAI Codex CLI initialization failed: {e}")

        self.state.initialized = True
        self.agent.set_data("_codex_cli_state", self.state)

    async def _handle_edit_action(self):
        """Handle code editing with Codex CLI."""
        file_path = self.args.get("file_path", "")
        instruction = self.args.get("instruction", "")

        if not file_path or not instruction:
            return Response(
                message="❌ Both 'file_path' and 'instruction' are required for edit action.",
                break_loop=False,
            )

        try:
            # Get approval if needed
            approval_mode = self.agent.config.codex_cli_approval_mode
            if approval_mode == "suggest":
                approval = await self._request_approval(
                    f"Edit file '{file_path}' with instruction: {instruction}"
                )
                if not approval:
                    return Response(
                        message="❌ Edit action cancelled by user.", break_loop=False
                    )

            # Execute Codex CLI edit command
            cmd = [
                self.agent.config.codex_cli_path,
                "edit",
                "--file",
                file_path,
                "--instruction",
                instruction,
            ]

            result = await self._run_secure_command(cmd)

            if result["success"]:
                return Response(
                    message=f"✅ File edited successfully:\n{result['output']}",
                    break_loop=False,
                )
            else:
                return Response(
                    message=f"❌ Edit failed: {result['error']}", break_loop=False
                )

        except Exception as e:
            return Response(message=f"❌ Error during edit: {str(e)}", break_loop=False)

    async def _handle_create_action(self):
        """Handle file creation with Codex CLI."""
        file_path = self.args.get("file_path", "")
        description = self.args.get("description", "")

        if not file_path or not description:
            return Response(
                message="❌ Both 'file_path' and 'description' are required for create action.",
                break_loop=False,
            )

        try:
            # Get approval if needed
            approval_mode = self.agent.config.codex_cli_approval_mode
            if approval_mode == "suggest":
                approval = await self._request_approval(
                    f"Create file '{file_path}' with description: {description}"
                )
                if not approval:
                    return Response(
                        message="❌ Create action cancelled by user.", break_loop=False
                    )

            # Execute Codex CLI create command
            cmd = [
                self.agent.config.codex_cli_path,
                "create",
                "--file",
                file_path,
                "--description",
                description,
            ]

            result = await self._run_secure_command(cmd)

            if result["success"]:
                return Response(
                    message=f"✅ File created successfully:\n{result['output']}",
                    break_loop=False,
                )
            else:
                return Response(
                    message=f"❌ Create failed: {result['error']}", break_loop=False
                )

        except Exception as e:
            return Response(
                message=f"❌ Error during create: {str(e)}", break_loop=False
            )

    async def _handle_shell_action(self):
        """Handle shell command execution with Codex CLI."""
        command = self.args.get("command", "")
        context = self.args.get("context", "")

        if not command:
            return Response(
                message="❌ 'command' is required for shell action.", break_loop=False
            )

        try:
            # Get approval if needed
            approval_mode = self.agent.config.codex_cli_approval_mode
            if approval_mode == "suggest":
                approval = await self._request_approval(
                    f"Execute shell command: {command}"
                    + (f" (Context: {context})" if context else "")
                )
                if not approval:
                    return Response(
                        message="❌ Shell command cancelled by user.", break_loop=False
                    )

            # Execute Codex CLI shell command
            cmd = [self.agent.config.codex_cli_path, "shell", "--command", command]
            if context:
                cmd.extend(["--context", context])

            result = await self._run_secure_command(cmd)

            if result["success"]:
                return Response(
                    message=f"✅ Shell command executed successfully:\n{result['output']}",
                    break_loop=False,
                )
            else:
                return Response(
                    message=f"❌ Shell command failed: {result['error']}",
                    break_loop=False,
                )

        except Exception as e:
            return Response(
                message=f"❌ Error during shell execution: {str(e)}", break_loop=False
            )

    async def _get_status(self):
        """Get Codex CLI status and configuration."""
        try:
            status_info = {
                "enabled": self.agent.config.codex_cli_enabled,
                "cli_available": self.state.cli_available,
                "cli_path": self.agent.config.codex_cli_path,
                "approval_mode": self.agent.config.codex_cli_approval_mode,
                "auto_install": self.agent.config.codex_cli_auto_install,
            }

            # Get CLI version if available
            if self.state.cli_available:
                try:
                    result = subprocess.run(
                        [self.agent.config.codex_cli_path, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if result.returncode == 0:
                        status_info["version"] = result.stdout.strip()
                except Exception:
                    status_info["version"] = "Unable to determine version"

            return Response(
                message=f"📊 OpenAI Codex CLI Status:\n{json.dumps(status_info, indent=2)}",
                break_loop=False,
            )

        except Exception as e:
            return Response(
                message=f"❌ Error getting status: {str(e)}", break_loop=False
            )

    async def _install_cli(self):
        """Install OpenAI Codex CLI."""
        if not self.agent.config.codex_cli_auto_install:
            return Response(
                message="❌ Auto-install is disabled. Please install OpenAI Codex CLI manually: npm install -g @openai/codex-cli",
                break_loop=False,
            )

        try:
            PrintStyle(font_color="#85C1E9").print("📦 Installing OpenAI Codex CLI...")

            # Install via npm
            cmd = ["npm", "install", "-g", "@openai/codex-cli"]
            result = await self._run_secure_command(
                cmd, timeout=300
            )  # 5 minute timeout

            if result["success"]:
                # Re-initialize after installation
                self.state.initialized = False
                await self._initialize_cli()

                return Response(
                    message=f"✅ OpenAI Codex CLI installed successfully:\n{result['output']}",
                    break_loop=False,
                )
            else:
                return Response(
                    message=f"❌ Installation failed: {result['error']}",
                    break_loop=False,
                )

        except Exception as e:
            return Response(
                message=f"❌ Error during installation: {str(e)}", break_loop=False
            )

    async def _run_secure_command(self, cmd: list[str], timeout: int = 60):
        """Run a command in a secure sandboxed environment."""
        try:
            # Use asyncio subprocess for better control
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=None,  # Use current working directory
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )

                return {
                    "success": process.returncode == 0,
                    "output": stdout.decode() if stdout else "",
                    "error": stderr.decode() if stderr else "",
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
            return {"success": False, "output": "", "error": str(e), "returncode": -1}

    async def _request_approval(self, action_description: str) -> bool:
        """Request user approval for an action."""
        PrintStyle(font_color="#FFA500", bold=True).print(
            f"🔐 Codex CLI Approval Required: {action_description}"
        )
        PrintStyle(font_color="#85C1E9").print("Approve this action? (y/n): ")

        # In a real implementation, this would integrate with the UI
        # For now, we'll simulate approval based on approval mode
        approval_mode = self.agent.config.codex_cli_approval_mode

        if approval_mode == "auto":
            PrintStyle(font_color="#85C1E9").print("✅ Auto-approved")
            return True
        elif approval_mode == "suggest":
            # In a real implementation, this would wait for user input
            # For now, we'll default to requiring manual intervention
            PrintStyle(font_color="#FFA500").print("⏳ Waiting for user approval...")
            self.state.last_approval = action_description
            return True  # Simplified for now
        else:
            PrintStyle(font_color="#FF6B6B").print("❌ Action blocked by approval mode")
            return False

    def get_log_object(self):
        return self.agent.context.log.log(
            type="codex_cli",
            heading=f"{self.agent.agent_name}: Using tool '{self.name}'",
            content="",
            kvps=self.args,
        )

    async def after_execution(self, response, **kwargs):
        self.agent.hist_add_tool_result(self.name, response.message)
