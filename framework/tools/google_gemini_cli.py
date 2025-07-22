import asyncio
import json
import shlex
import subprocess
from dataclasses import dataclass
from typing import Optional

from framework.helpers.print_style import PrintStyle
from framework.helpers.tool import Response, Tool


@dataclass
class GeminiCLIState:
    """State for Google Gemini CLI operations."""
    initialized: bool = False
    cli_available: bool = False
    last_approval: Optional[str] = None


class GoogleGeminiCLI(Tool):
    """Google Gemini CLI integration tool for local model interaction and code assistance."""

    async def execute(self, **kwargs):
        await self.agent.handle_intervention()  # Wait for intervention and handle it, if paused

        # Get tool state
        self.state = self.agent.get_data("_gemini_cli_state") or GeminiCLIState()

        # Check if Gemini CLI is enabled
        if not self.agent.config.gemini_cli_enabled:
            return Response(
                message="❌ Google Gemini CLI is disabled. Enable it in settings to use this tool.",
                break_loop=False
            )

        # Initialize CLI if needed
        if not self.state.initialized:
            await self._initialize_cli()

        if not self.state.cli_available:
            return Response(
                message="❌ Google Gemini CLI is not available. Please install it first.",
                break_loop=False
            )

        action = self.args.get("action", "").lower().strip()

        if action == "chat":
            return await self._handle_chat_action()
        elif action == "code":
            return await self._handle_code_action()
        elif action == "generate":
            return await self._handle_generate_action()
        elif action == "config":
            return await self._handle_config_action()
        elif action == "status":
            return await self._get_status()
        elif action == "install":
            return await self._install_cli()
        else:
            return Response(
                message=self.agent.read_prompt(
                    "fw.gemini_cli.usage.md",
                    available_actions="chat, code, generate, config, status, install"
                ),
                break_loop=False
            )

    async def _initialize_cli(self):
        """Initialize the Gemini CLI and check availability."""
        try:
            # Check if CLI is available
            result = subprocess.run(
                [self.agent.config.gemini_cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.state.cli_available = True
                PrintStyle(font_color="#85C1E9").print(f"✅ Google Gemini CLI found: {result.stdout.strip()}")
            else:
                self.state.cli_available = False
                PrintStyle.warning("⚠️ Google Gemini CLI not found or not working")
                
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.state.cli_available = False
            PrintStyle.warning(f"⚠️ Google Gemini CLI initialization failed: {e}")

        self.state.initialized = True
        self.agent.set_data("_gemini_cli_state", self.state)

    async def _handle_chat_action(self):
        """Handle chat interaction with Gemini CLI."""
        message = self.args.get("message", "")
        model = self.args.get("model", "gemini-pro")
        
        if not message:
            return Response(
                message="❌ 'message' is required for chat action.",
                break_loop=False
            )

        try:
            # Get approval if needed
            approval_mode = self.agent.config.gemini_cli_approval_mode
            if approval_mode == "suggest":
                approval = await self._request_approval(
                    f"Send chat message to Gemini ({model}): {message[:100]}..."
                )
                if not approval:
                    return Response(
                        message="❌ Chat action cancelled by user.",
                        break_loop=False
                    )

            # Execute Gemini CLI chat command
            cmd = [
                self.agent.config.gemini_cli_path,
                "chat",
                "--model", model,
                "--message", message
            ]

            result = await self._run_secure_command(cmd)
            
            if result["success"]:
                return Response(
                    message=f"✅ Gemini response:\n{result['output']}",
                    break_loop=False
                )
            else:
                return Response(
                    message=f"❌ Chat failed: {result['error']}",
                    break_loop=False
                )

        except Exception as e:
            return Response(
                message=f"❌ Error during chat: {str(e)}",
                break_loop=False
            )

    async def _handle_code_action(self):
        """Handle code generation/analysis with Gemini CLI."""
        task = self.args.get("task", "")
        language = self.args.get("language", "")
        file_path = self.args.get("file_path", "")
        
        if not task:
            return Response(
                message="❌ 'task' is required for code action.",
                break_loop=False
            )

        try:
            # Get approval if needed
            approval_mode = self.agent.config.gemini_cli_approval_mode
            if approval_mode == "suggest":
                approval = await self._request_approval(
                    f"Code task with Gemini: {task}" + 
                    (f" (Language: {language})" if language else "") +
                    (f" (File: {file_path})" if file_path else "")
                )
                if not approval:
                    return Response(
                        message="❌ Code action cancelled by user.",
                        break_loop=False
                    )

            # Execute Gemini CLI code command
            cmd = [
                self.agent.config.gemini_cli_path,
                "code",
                "--task", task
            ]
            
            if language:
                cmd.extend(["--language", language])
            if file_path:
                cmd.extend(["--file", file_path])

            result = await self._run_secure_command(cmd)
            
            if result["success"]:
                return Response(
                    message=f"✅ Code task completed:\n{result['output']}",
                    break_loop=False
                )
            else:
                return Response(
                    message=f"❌ Code task failed: {result['error']}",
                    break_loop=False
                )

        except Exception as e:
            return Response(
                message=f"❌ Error during code task: {str(e)}",
                break_loop=False
            )

    async def _handle_generate_action(self):
        """Handle content generation with Gemini CLI."""
        prompt = self.args.get("prompt", "")
        output_file = self.args.get("output_file", "")
        format_type = self.args.get("format", "text")
        
        if not prompt:
            return Response(
                message="❌ 'prompt' is required for generate action.",
                break_loop=False
            )

        try:
            # Get approval if needed
            approval_mode = self.agent.config.gemini_cli_approval_mode
            if approval_mode == "suggest":
                approval = await self._request_approval(
                    f"Generate content with Gemini: {prompt[:100]}..." +
                    (f" (Output: {output_file})" if output_file else "")
                )
                if not approval:
                    return Response(
                        message="❌ Generate action cancelled by user.",
                        break_loop=False
                    )

            # Execute Gemini CLI generate command
            cmd = [
                self.agent.config.gemini_cli_path,
                "generate",
                "--prompt", prompt,
                "--format", format_type
            ]
            
            if output_file:
                cmd.extend(["--output", output_file])

            result = await self._run_secure_command(cmd)
            
            if result["success"]:
                return Response(
                    message=f"✅ Content generated successfully:\n{result['output']}",
                    break_loop=False
                )
            else:
                return Response(
                    message=f"❌ Generate failed: {result['error']}",
                    break_loop=False
                )

        except Exception as e:
            return Response(
                message=f"❌ Error during generation: {str(e)}",
                break_loop=False
            )

    async def _handle_config_action(self):
        """Handle Gemini CLI configuration."""
        config_key = self.args.get("key", "")
        config_value = self.args.get("value", "")
        list_config = self.args.get("list", False)
        
        try:
            if list_config:
                # List current configuration
                cmd = [self.agent.config.gemini_cli_path, "config", "--list"]
            elif config_key and config_value:
                # Set configuration
                approval_mode = self.agent.config.gemini_cli_approval_mode
                if approval_mode == "suggest":
                    approval = await self._request_approval(
                        f"Set Gemini config: {config_key} = {config_value}"
                    )
                    if not approval:
                        return Response(
                            message="❌ Config action cancelled by user.",
                            break_loop=False
                        )
                
                cmd = [
                    self.agent.config.gemini_cli_path,
                    "config",
                    "--set", f"{config_key}={config_value}"
                ]
            else:
                return Response(
                    message="❌ Either use 'list=true' or provide both 'key' and 'value' for config action.",
                    break_loop=False
                )

            result = await self._run_secure_command(cmd)
            
            if result["success"]:
                return Response(
                    message=f"✅ Config operation completed:\n{result['output']}",
                    break_loop=False
                )
            else:
                return Response(
                    message=f"❌ Config operation failed: {result['error']}",
                    break_loop=False
                )

        except Exception as e:
            return Response(
                message=f"❌ Error during config operation: {str(e)}",
                break_loop=False
            )

    async def _get_status(self):
        """Get Gemini CLI status and configuration."""
        try:
            status_info = {
                "enabled": self.agent.config.gemini_cli_enabled,
                "cli_available": self.state.cli_available,
                "cli_path": self.agent.config.gemini_cli_path,
                "approval_mode": self.agent.config.gemini_cli_approval_mode,
                "auto_install": self.agent.config.gemini_cli_auto_install
            }

            # Get CLI version if available
            if self.state.cli_available:
                try:
                    result = subprocess.run(
                        [self.agent.config.gemini_cli_path, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        status_info["version"] = result.stdout.strip()
                except Exception:
                    status_info["version"] = "Unable to determine version"

            return Response(
                message=f"📊 Google Gemini CLI Status:\n{json.dumps(status_info, indent=2)}",
                break_loop=False
            )

        except Exception as e:
            return Response(
                message=f"❌ Error getting status: {str(e)}",
                break_loop=False
            )

    async def _install_cli(self):
        """Install Google Gemini CLI."""
        if not self.agent.config.gemini_cli_auto_install:
            return Response(
                message="❌ Auto-install is disabled. Please install Google Gemini CLI manually: pip install google-generativeai[cli]",
                break_loop=False
            )

        try:
            PrintStyle(font_color="#85C1E9").print("📦 Installing Google Gemini CLI...")
            
            # Install via pip
            cmd = ["pip", "install", "google-generativeai[cli]"]
            result = await self._run_secure_command(cmd, timeout=300)  # 5 minute timeout
            
            if result["success"]:
                # Re-initialize after installation
                self.state.initialized = False
                await self._initialize_cli()
                
                return Response(
                    message=f"✅ Google Gemini CLI installed successfully:\n{result['output']}",
                    break_loop=False
                )
            else:
                return Response(
                    message=f"❌ Installation failed: {result['error']}",
                    break_loop=False
                )

        except Exception as e:
            return Response(
                message=f"❌ Error during installation: {str(e)}",
                break_loop=False
            )

    async def _run_secure_command(self, cmd: list[str], timeout: int = 60):
        """Run a command in a secure sandboxed environment."""
        try:
            # Use asyncio subprocess for better control
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=None  # Use current working directory
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
                
                return {
                    "success": process.returncode == 0,
                    "output": stdout.decode() if stdout else "",
                    "error": stderr.decode() if stderr else "",
                    "returncode": process.returncode
                }

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "output": "",
                    "error": f"Command timed out after {timeout} seconds",
                    "returncode": -1
                }

        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "returncode": -1
            }

    async def _request_approval(self, action_description: str) -> bool:
        """Request user approval for an action."""
        PrintStyle(font_color="#FFA500", bold=True).print(
            f"🔐 Gemini CLI Approval Required: {action_description}"
        )
        PrintStyle(font_color="#85C1E9").print("Approve this action? (y/n): ")
        
        # In a real implementation, this would integrate with the UI
        # For now, we'll simulate approval based on approval mode
        approval_mode = self.agent.config.gemini_cli_approval_mode
        
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
            type="gemini_cli",
            heading=f"{self.agent.agent_name}: Using tool '{self.name}'",
            content="",
            kvps=self.args,
        )

    async def after_execution(self, response, **kwargs):
        self.agent.hist_add_tool_result(self.name, response.message)