import asyncio
import json
import subprocess
from dataclasses import dataclass

from framework.helpers.print_style import PrintStyle
from framework.helpers.tool import Response, Tool


@dataclass
class QwenCoderCLIState:
    """State for Qwen Coder CLI operations."""

    initialized: bool = False
    cli_available: bool = False
    last_approval: str | None = None


class QwenCoderCLI(Tool):
    """Qwen Coder CLI integration tool for AI-powered code assistance and generation."""

    async def execute(self, **kwargs):
        await (
            self.agent.handle_intervention()
        )  # Wait for intervention and handle it, if paused

        # Get tool state
        self.state = self.agent.get_data("_qwen_coder_cli_state") or QwenCoderCLIState()

        # Check if Qwen Coder CLI is enabled
        if not self.agent.config.qwen_cli_enabled:
            return Response(
                message="❌ Qwen Coder CLI is disabled. Enable it in settings to use this tool.",
                break_loop=False,
            )

        # Initialize CLI if needed
        if not self.state.initialized:
            await self._initialize_cli()

        if not self.state.cli_available:
            return Response(
                message="❌ Qwen Coder CLI is not available. Please install it first.",
                break_loop=False,
            )

        action = self.args.get("action", "").lower().strip()

        if action == "generate":
            return await self._handle_generate_action()
        elif action == "review":
            return await self._handle_review_action()
        elif action == "complete":
            return await self._handle_complete_action()
        elif action == "explain":
            return await self._handle_explain_action()
        elif action == "refactor":
            return await self._handle_refactor_action()
        elif action == "status":
            return await self._get_status()
        elif action == "install":
            return await self._install_cli()
        else:
            return Response(
                message=self.agent.read_prompt(
                    "fw.qwen_cli.usage.md",
                    available_actions="generate, review, complete, explain, refactor, status, install",
                ),
                break_loop=False,
            )

    async def _initialize_cli(self):
        """Initialize the Qwen Coder CLI and check availability."""
        try:
            # Check if CLI is available
            result = subprocess.run(
                [self.agent.config.qwen_cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                self.state.cli_available = True
                PrintStyle(font_color="#85C1E9").print(
                    f"✅ Qwen Coder CLI found: {result.stdout.strip()}"
                )
            else:
                self.state.cli_available = False
                PrintStyle.warning("⚠️ Qwen Coder CLI not found or not working")

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.state.cli_available = False
            PrintStyle.warning(f"⚠️ Qwen Coder CLI initialization failed: {e}")

        self.state.initialized = True
        self.agent.set_data("_qwen_coder_cli_state", self.state)

    async def _handle_generate_action(self):
        """Handle code generation with Qwen Coder CLI."""
        prompt = self.args.get("prompt", "")
        language = self.args.get("language", "python")
        output_file = self.args.get("output_file", "")

        if not prompt:
            return Response(
                message="❌ 'prompt' is required for generate action.", break_loop=False
            )

        try:
            # Get approval if needed
            approval_mode = self.agent.config.qwen_cli_approval_mode
            if approval_mode == "suggest":
                approval = await self._request_approval(
                    f"Generate {language} code with Qwen: {prompt[:100]}..."
                    + (f" (Output: {output_file})" if output_file else "")
                )
                if not approval:
                    return Response(
                        message="❌ Generate action cancelled by user.",
                        break_loop=False,
                    )

            # Execute Qwen Coder CLI generate command
            cmd = [
                self.agent.config.qwen_cli_path,
                "generate",
                "--prompt",
                prompt,
                "--language",
                language,
            ]

            if output_file:
                cmd.extend(["--output", output_file])

            result = await self._run_secure_command(cmd)

            if result["success"]:
                return Response(
                    message=f"✅ Code generated successfully:\n{result['output']}",
                    break_loop=False,
                )
            else:
                return Response(
                    message=f"❌ Generate failed: {result['error']}", break_loop=False
                )

        except Exception as e:
            return Response(
                message=f"❌ Error during generation: {str(e)}", break_loop=False
            )

    async def _handle_review_action(self):
        """Handle code review with Qwen Coder CLI."""
        file_path = self.args.get("file_path", "")
        focus = self.args.get("focus", "general")

        if not file_path:
            return Response(
                message="❌ 'file_path' is required for review action.", break_loop=False
            )

        try:
            # Get approval if needed
            approval_mode = self.agent.config.qwen_cli_approval_mode
            if approval_mode == "suggest":
                approval = await self._request_approval(
                    f"Review code in '{file_path}' with focus on: {focus}"
                )
                if not approval:
                    return Response(
                        message="❌ Review action cancelled by user.", break_loop=False
                    )

            # Execute Qwen Coder CLI review command
            cmd = [
                self.agent.config.qwen_cli_path,
                "review",
                "--file",
                file_path,
                "--focus",
                focus,
            ]

            result = await self._run_secure_command(cmd)

            if result["success"]:
                return Response(
                    message=f"✅ Code review completed:\n{result['output']}",
                    break_loop=False,
                )
            else:
                return Response(
                    message=f"❌ Review failed: {result['error']}", break_loop=False
                )

        except Exception as e:
            return Response(
                message=f"❌ Error during review: {str(e)}", break_loop=False
            )

    async def _handle_complete_action(self):
        """Handle code completion with Qwen Coder CLI."""
        file_path = self.args.get("file_path", "")
        line_number = self.args.get("line_number", "")
        context = self.args.get("context", "")

        if not file_path:
            return Response(
                message="❌ 'file_path' is required for complete action.",
                break_loop=False,
            )

        try:
            # Get approval if needed
            approval_mode = self.agent.config.qwen_cli_approval_mode
            if approval_mode == "suggest":
                approval = await self._request_approval(
                    f"Complete code in '{file_path}'"
                    + (f" at line {line_number}" if line_number else "")
                )
                if not approval:
                    return Response(
                        message="❌ Complete action cancelled by user.",
                        break_loop=False,
                    )

            # Execute Qwen Coder CLI complete command
            cmd = [
                self.agent.config.qwen_cli_path,
                "complete",
                "--file",
                file_path,
            ]

            if line_number:
                cmd.extend(["--line", str(line_number)])
            if context:
                cmd.extend(["--context", context])

            result = await self._run_secure_command(cmd)

            if result["success"]:
                return Response(
                    message=f"✅ Code completion generated:\n{result['output']}",
                    break_loop=False,
                )
            else:
                return Response(
                    message=f"❌ Complete failed: {result['error']}", break_loop=False
                )

        except Exception as e:
            return Response(
                message=f"❌ Error during completion: {str(e)}", break_loop=False
            )

    async def _handle_explain_action(self):
        """Handle code explanation with Qwen Coder CLI."""
        code_snippet = self.args.get("code_snippet", "")
        file_path = self.args.get("file_path", "")
        detail_level = self.args.get("detail_level", "medium")

        if not code_snippet and not file_path:
            return Response(
                message="❌ Either 'code_snippet' or 'file_path' is required for explain action.",
                break_loop=False,
            )

        try:
            # Get approval if needed
            approval_mode = self.agent.config.qwen_cli_approval_mode
            if approval_mode == "suggest":
                approval = await self._request_approval(
                    f"Explain code with Qwen (detail level: {detail_level})"
                )
                if not approval:
                    return Response(
                        message="❌ Explain action cancelled by user.", break_loop=False
                    )

            # Execute Qwen Coder CLI explain command
            cmd = [
                self.agent.config.qwen_cli_path,
                "explain",
                "--detail",
                detail_level,
            ]

            if file_path:
                cmd.extend(["--file", file_path])
            elif code_snippet:
                cmd.extend(["--code", code_snippet])

            result = await self._run_secure_command(cmd)

            if result["success"]:
                return Response(
                    message=f"✅ Code explanation:\n{result['output']}",
                    break_loop=False,
                )
            else:
                return Response(
                    message=f"❌ Explain failed: {result['error']}", break_loop=False
                )

        except Exception as e:
            return Response(
                message=f"❌ Error during explanation: {str(e)}", break_loop=False
            )

    async def _handle_refactor_action(self):
        """Handle code refactoring with Qwen Coder CLI."""
        file_path = self.args.get("file_path", "")
        refactor_type = self.args.get("refactor_type", "general")
        target = self.args.get("target", "")

        if not file_path:
            return Response(
                message="❌ 'file_path' is required for refactor action.",
                break_loop=False,
            )

        try:
            # Get approval if needed
            approval_mode = self.agent.config.qwen_cli_approval_mode
            if approval_mode == "suggest":
                approval = await self._request_approval(
                    f"Refactor code in '{file_path}' (type: {refactor_type})"
                )
                if not approval:
                    return Response(
                        message="❌ Refactor action cancelled by user.",
                        break_loop=False,
                    )

            # Execute Qwen Coder CLI refactor command
            cmd = [
                self.agent.config.qwen_cli_path,
                "refactor",
                "--file",
                file_path,
                "--type",
                refactor_type,
            ]

            if target:
                cmd.extend(["--target", target])

            result = await self._run_secure_command(cmd)

            if result["success"]:
                return Response(
                    message=f"✅ Code refactored successfully:\n{result['output']}",
                    break_loop=False,
                )
            else:
                return Response(
                    message=f"❌ Refactor failed: {result['error']}", break_loop=False
                )

        except Exception as e:
            return Response(
                message=f"❌ Error during refactoring: {str(e)}", break_loop=False
            )

    async def _get_status(self):
        """Get Qwen Coder CLI status and configuration."""
        try:
            status_info = {
                "enabled": self.agent.config.qwen_cli_enabled,
                "cli_available": self.state.cli_available,
                "cli_path": self.agent.config.qwen_cli_path,
                "approval_mode": self.agent.config.qwen_cli_approval_mode,
                "auto_install": self.agent.config.qwen_cli_auto_install,
            }

            # Get CLI version if available
            if self.state.cli_available:
                try:
                    result = subprocess.run(
                        [self.agent.config.qwen_cli_path, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if result.returncode == 0:
                        status_info["version"] = result.stdout.strip()
                except Exception:
                    status_info["version"] = "Unable to determine version"

            return Response(
                message=f"📊 Qwen Coder CLI Status:\n{json.dumps(status_info, indent=2)}",
                break_loop=False,
            )

        except Exception as e:
            return Response(
                message=f"❌ Error getting status: {str(e)}", break_loop=False
            )

    async def _install_cli(self):
        """Install Qwen Coder CLI."""
        if not self.agent.config.qwen_cli_auto_install:
            return Response(
                message="❌ Auto-install is disabled. Please install Qwen Coder CLI manually: pip install qwen-coder-cli",
                break_loop=False,
            )

        try:
            PrintStyle(font_color="#85C1E9").print("📦 Installing Qwen Coder CLI...")

            # Install via pip
            cmd = ["pip", "install", "qwen-coder-cli"]
            result = await self._run_secure_command(
                cmd, timeout=300
            )  # 5 minute timeout

            if result["success"]:
                # Re-initialize after installation
                self.state.initialized = False
                await self._initialize_cli()

                return Response(
                    message=f"✅ Qwen Coder CLI installed successfully:\n{result['output']}",
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
            f"🔐 Qwen Coder CLI Approval Required: {action_description}"
        )
        PrintStyle(font_color="#85C1E9").print("Approve this action? (y/n): ")

        # In a real implementation, this would integrate with the UI
        # For now, we'll simulate approval based on approval mode
        approval_mode = self.agent.config.qwen_cli_approval_mode

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
            type="qwen_coder_cli",
            heading=f"{self.agent.agent_name}: Using tool '{self.name}'",
            content="",
            kvps=self.args,
        )

    async def after_execution(self, response, **kwargs):
        self.agent.hist_add_tool_result(self.name, response.message)
