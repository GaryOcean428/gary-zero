import asyncio
import re
import shlex
import time
from dataclasses import dataclass

from framework.helpers import rfc_exchange
from framework.helpers.docker import DockerContainerManager
from framework.helpers.execution_mode import get_execution_info, should_use_ssh_execution
from framework.helpers.messages import truncate_text
from framework.helpers.print_style import PrintStyle
from framework.helpers.shell_local import LocalInteractiveSession
from framework.helpers.shell_ssh import SSHInteractiveSession
from framework.helpers.tool import Response, Tool

# Import secure execution framework
try:
    from framework.executors.secure_manager import SecureCodeExecutionManager
    SECURE_EXECUTION_AVAILABLE = True
except ImportError:
    SECURE_EXECUTION_AVAILABLE = False
    print("⚠️  Secure execution framework not available, using legacy execution")


@dataclass
class State:
    shells: dict[int, LocalInteractiveSession | SSHInteractiveSession]
    docker: DockerContainerManager | None
    # Add secure execution manager
    secure_manager: SecureCodeExecutionManager | None = None
    secure_sessions: dict[int, str] = None  # Map session numbers to secure session IDs


class CodeExecution(Tool):

    async def execute(self, **kwargs):

        await self.agent.handle_intervention()  # wait for intervention and handle it, if paused

        await self.prepare_state()

        runtime = self.args.get("runtime", "").lower().strip()
        session = int(self.args.get("session", 0))

        # Add new runtime options for secure execution
        if runtime == "python":
            response = await self.execute_python_code(code=self.args["code"], session=session)
        elif runtime == "nodejs":
            response = await self.execute_nodejs_code(code=self.args["code"], session=session)
        elif runtime == "terminal":
            response = await self.execute_terminal_command(
                command=self.args["code"], session=session
            )
        elif runtime == "output":
            response = await self.get_terminal_output(
                session=session, first_output_timeout=60, between_output_timeout=5
            )
        elif runtime == "reset":
            response = await self.reset_terminal(session=session)
        elif runtime == "secure_info":
            response = await self.get_secure_info()
        elif runtime == "install":
            package = self.args.get("package", "")
            if not package:
                response = self.agent.read_prompt("fw.code.runtime_wrong.md", runtime="install (missing package name)")
            else:
                response = await self.install_package(package=package, session=session)
        else:
            response = self.agent.read_prompt("fw.code.runtime_wrong.md", runtime=runtime)

        if not response:
            response = self.agent.read_prompt(
                "fw.code.info.md", info=self.agent.read_prompt("fw.code.no_output.md")
            )
        return Response(message=response, break_loop=False)

    def get_log_object(self):
        return self.agent.context.log.log(
            type="code_exe",
            heading=f"{self.agent.agent_name}: Using tool '{self.name}'",
            content="",
            kvps=self.args,
        )

    async def after_execution(self, response, **kwargs):
        self.agent.hist_add_tool_result(self.name, response.message)

    async def prepare_state(self, reset=False, session=None):
        self.state = self.agent.get_data("_cet_state")
        if not self.state or reset:

            # Initialize secure execution manager if available
            secure_manager = None
            secure_sessions = {}
            if SECURE_EXECUTION_AVAILABLE:
                try:
                    secure_manager = SecureCodeExecutionManager()
                    PrintStyle(font_color="#85C1E9").print(f"🔒 Secure execution enabled: {secure_manager.get_executor_info()['description']}")
                except Exception as e:
                    PrintStyle.warning(f"Secure execution initialization failed: {e}")
                    secure_manager = None

            # initialize docker container if execution in docker is configured
            if not self.state and self.agent.config.code_exec_docker_enabled:
                docker = DockerContainerManager(
                    logger=self.agent.context.log,
                    name=self.agent.config.code_exec_docker_name,
                    image=self.agent.config.code_exec_docker_image,
                    ports=self.agent.config.code_exec_docker_ports,
                    volumes=self.agent.config.code_exec_docker_volumes,
                )
                docker.start_container()
            else:
                docker = self.state.docker if self.state else None

            # initialize shells dictionary if not exists
            shells = {} if not self.state else self.state.shells.copy()

            # Handle secure sessions
            if self.state and hasattr(self.state, 'secure_sessions'):
                secure_sessions = self.state.secure_sessions.copy() if self.state.secure_sessions else {}

            # Only reset the specified session if provided
            if session is not None and session in shells:
                shells[session].close()
                del shells[session]
                # Also clean up secure session if it exists
                if secure_manager and session in secure_sessions:
                    secure_manager.close_session(secure_sessions[session])
                    del secure_sessions[session]
            elif reset and not session:
                # Close all sessions if full reset requested
                for s in list(shells.keys()):
                    shells[s].close()
                shells = {}
                # Clean up all secure sessions
                if secure_manager:
                    secure_manager.cleanup_all()
                secure_sessions = {}

            # initialize local or remote interactive shell interface for session 0 if needed
            if 0 not in shells:
                shell = None

                # Determine if SSH should be used based on environment and availability
                use_ssh = self.agent.config.code_exec_ssh_enabled and should_use_ssh_execution()

                if use_ssh:
                    try:
                        PrintStyle(font_color="#85C1E9").print(f"🔗 Attempting SSH connection: {get_execution_info()}")
                        pswd = (
                            self.agent.config.code_exec_ssh_pass
                            if self.agent.config.code_exec_ssh_pass
                            else await rfc_exchange.get_root_password()
                        )
                        shell = SSHInteractiveSession(
                            self.agent.context.log,
                            self.agent.config.code_exec_ssh_addr,
                            self.agent.config.code_exec_ssh_port,
                            self.agent.config.code_exec_ssh_user,
                            pswd,
                        )
                        shells[0] = shell
                        await shell.connect()
                        PrintStyle(font_color="#85C1E9").print("✅ SSH connection established successfully")
                    except Exception as ssh_error:
                        PrintStyle.warning(f"❌ SSH connection failed: {ssh_error}")
                        PrintStyle.warning("🔄 Falling back to local execution")
                        shell = None  # Reset shell to force local execution

                # Fallback to local execution if SSH failed or wasn't attempted
                if shell is None:
                    PrintStyle(font_color="#85C1E9").print(f"🖥️  Using direct execution: {get_execution_info()}")
                    shell = LocalInteractiveSession()
                    shells[0] = shell
                    await shell.connect()

            self.state = State(shells=shells, docker=docker, secure_manager=secure_manager, secure_sessions=secure_sessions)
        self.agent.set_data("_cet_state", self.state)

    async def execute_python_code(self, session: int, code: str, reset: bool = False):
        # Prefer secure execution as primary path
        if self.state.secure_manager:
            if self.state.secure_manager.is_secure_execution_available():
                return await self._execute_secure_python(session, code, reset)
            else:
                PrintStyle.warning("🔄 Secure execution not available, falling back to terminal execution")

        # Fallback to legacy terminal execution
        escaped_code = shlex.quote(code)
        command = f"ipython -c {escaped_code}"
        return await self.terminal_session(session, command, reset)

    async def execute_nodejs_code(self, session: int, code: str, reset: bool = False):
        # Prefer secure execution as primary path
        if self.state.secure_manager:
            if self.state.secure_manager.is_secure_execution_available():
                return await self._execute_secure_nodejs(session, code, reset)
            else:
                PrintStyle.warning("🔄 Secure execution not available, falling back to terminal execution")

        # Fallback to legacy terminal execution
        escaped_code = shlex.quote(code)
        command = f"node /exe/node_eval.js {escaped_code}"
        return await self.terminal_session(session, command, reset)

    async def execute_terminal_command(self, session: int, command: str, reset: bool = False):
        # Prefer secure execution as primary path
        if self.state.secure_manager:
            if self.state.secure_manager.is_secure_execution_available():
                return await self._execute_secure_terminal(session, command, reset)
            else:
                PrintStyle.warning("🔄 Secure execution not available, falling back to terminal execution")

        # Fallback to legacy terminal execution
        return await self.terminal_session(session, command, reset)

    async def _execute_secure_python(self, session: int, code: str, reset: bool = False):
        """Execute Python code using secure execution framework."""
        try:
            # Get or create secure session
            secure_session_id = await self._get_or_create_secure_session(session, reset)

            PrintStyle(background_color="blue", font_color="white", bold=True).print(
                f"{self.agent.agent_name} secure Python execution"
            )

            result = self.state.secure_manager.execute_code(secure_session_id, code, "python")

            if result["success"]:
                output = result["stdout"]
                execution_time = result.get("execution_time", 0)

                if output:
                    PrintStyle(font_color="#85C1E9").print(output)

                response_parts = []
                if output:
                    response_parts.append(output)

                response_parts.append(f"✅ Execution completed in {execution_time:.2f}s using {result.get('executor_type', 'unknown')} executor")

                return "\n".join(response_parts)
            else:
                error_msg = result.get("error", "Unknown error")
                stderr = result.get("stderr", "")

                error_output = f"❌ Execution failed: {error_msg}"
                if stderr:
                    error_output += f"\nStderr: {stderr}"

                PrintStyle.error(error_output)
                return error_output

        except Exception as e:
            error_msg = f"❌ Secure execution error: {str(e)}"
            PrintStyle.error(error_msg)
            return error_msg

    async def _execute_secure_nodejs(self, session: int, code: str, reset: bool = False):
        """Execute Node.js code using secure execution framework."""
        try:
            # Get or create secure session
            secure_session_id = await self._get_or_create_secure_session(session, reset)

            PrintStyle(background_color="green", font_color="white", bold=True).print(
                f"{self.agent.agent_name} secure Node.js execution"
            )

            # For Node.js, we'll use shell execution with node command
            node_command = f"node -e '{code}'"
            result = self.state.secure_manager.execute_code(secure_session_id, node_command, "bash")

            if result["success"]:
                output = result["stdout"]
                execution_time = result.get("execution_time", 0)

                if output:
                    PrintStyle(font_color="#85C1E9").print(output)

                response = f"✅ Node.js execution completed in {execution_time:.2f}s"
                if output:
                    response = f"{output}\n{response}"

                return response
            else:
                error_msg = f"❌ Node.js execution failed: {result.get('error', 'Unknown error')}"
                PrintStyle.error(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"❌ Secure Node.js execution error: {str(e)}"
            PrintStyle.error(error_msg)
            return error_msg

    async def _execute_secure_terminal(self, session: int, command: str, reset: bool = False):
        """Execute terminal command using secure execution framework."""
        try:
            # Get or create secure session
            secure_session_id = await self._get_or_create_secure_session(session, reset)

            PrintStyle(background_color="black", font_color="white", bold=True).print(
                f"{self.agent.agent_name} secure terminal execution"
            )

            result = self.state.secure_manager.execute_code(secure_session_id, command, "bash")

            if result["success"]:
                output = result["stdout"]
                execution_time = result.get("execution_time", 0)

                if output:
                    PrintStyle(font_color="#85C1E9").print(output)

                response = f"✅ Command completed in {execution_time:.2f}s"
                if output:
                    response = f"{output}\n{response}"

                return response
            else:
                error_msg = f"❌ Command failed: {result.get('error', 'Unknown error')}"
                stderr = result.get("stderr", "")
                if stderr:
                    error_msg += f"\nStderr: {stderr}"

                PrintStyle.error(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"❌ Secure terminal execution error: {str(e)}"
            PrintStyle.error(error_msg)
            return error_msg

    async def _get_or_create_secure_session(self, session: int, reset: bool = False) -> str:
        """Get or create a secure session for the given session number."""
        if not self.state.secure_sessions:
            self.state.secure_sessions = {}

        if reset and session in self.state.secure_sessions:
            # Close existing session
            self.state.secure_manager.close_session(self.state.secure_sessions[session])
            del self.state.secure_sessions[session]

        if session not in self.state.secure_sessions:
            # Create new secure session
            secure_session_id = self.state.secure_manager.create_session()
            self.state.secure_sessions[session] = secure_session_id

        return self.state.secure_sessions[session]

    async def install_package(self, package: str, session: int = 0) -> str:
        """Install a package in the execution environment."""
        try:
            if self.state.secure_manager and self.state.secure_manager.is_secure_execution_available():
                secure_session_id = await self._get_or_create_secure_session(session)

                PrintStyle(background_color="yellow", font_color="black", bold=True).print(
                    f"{self.agent.agent_name} secure package installation"
                )

                result = self.state.secure_manager.install_package(secure_session_id, package)

                if result["success"]:
                    execution_time = result.get("execution_time", 0)
                    response = f"✅ Package '{package}' installed successfully in {execution_time:.2f}s"
                    PrintStyle(font_color="#85C1E9").print(response)
                    return response
                else:
                    error_msg = f"❌ Package installation failed: {result.get('error', 'Unknown error')}"
                    PrintStyle.error(error_msg)
                    return error_msg
            else:
                # Fallback to pip install via terminal
                command = f"pip install {package}"
                return await self.execute_terminal_command(session, command)

        except Exception as e:
            error_msg = f"❌ Package installation error: {str(e)}"
            PrintStyle.error(error_msg)
            return error_msg

    async def get_secure_info(self) -> str:
        """Get information about the secure execution environment."""
        try:
            if self.state.secure_manager:
                info = self.state.secure_manager.get_executor_info()

                response_parts = [
                    "🔒 Secure Code Execution Environment Information:",
                    f"Executor Type: {info['type']}",
                    f"Security Level: {'High' if info['secure'] == 'True' else 'Low (Host execution)'}",
                    f"Description: {info['description']}"
                ]

                if info['secure'] == 'True':
                    response_parts.append("✅ Code execution is isolated and secure")
                else:
                    response_parts.append("⚠️  Warning: Code execution may not be isolated")

                response = "\n".join(response_parts)
                PrintStyle(font_color="#85C1E9").print(response)
                return response
            else:
                response = "⚠️  Secure execution framework not available - using legacy execution"
                PrintStyle.warning(response)
                return response

        except Exception as e:
            error_msg = f"❌ Error getting executor info: {str(e)}"
            PrintStyle.error(error_msg)
            return error_msg

    async def terminal_session(self, session: int, command: str, reset: bool = False):

        await self.agent.handle_intervention()  # wait for intervention and handle it, if paused
        # try again on lost connection
        for i in range(2):
            try:

                if reset:
                    await self.reset_terminal()

                if session not in self.state.shells:
                    shell = None

                    # Determine if SSH should be used based on environment and availability
                    use_ssh = self.agent.config.code_exec_ssh_enabled and should_use_ssh_execution()

                    if use_ssh:
                        try:
                            pswd = (
                                self.agent.config.code_exec_ssh_pass
                                if self.agent.config.code_exec_ssh_pass
                                else await rfc_exchange.get_root_password()
                            )
                            shell = SSHInteractiveSession(
                                self.agent.context.log,
                                self.agent.config.code_exec_ssh_addr,
                                self.agent.config.code_exec_ssh_port,
                                self.agent.config.code_exec_ssh_user,
                                pswd,
                            )
                            self.state.shells[session] = shell
                            await shell.connect()
                        except Exception as ssh_error:
                            PrintStyle.warning(f"SSH connection failed: {ssh_error}, falling back to local execution")
                            shell = None  # Reset to force local execution

                    # Fallback to local execution if SSH failed or wasn't attempted
                    if shell is None:
                        shell = LocalInteractiveSession()
                        self.state.shells[session] = shell
                        await shell.connect()

                self.state.shells[session].send_command(command)

                PrintStyle(background_color="white", font_color="#1B4F72", bold=True).print(
                    f"{self.agent.agent_name} code execution output"
                )
                return await self.get_terminal_output(session)

            except Exception as e:
                if i == 1:
                    # try again on lost connection
                    PrintStyle.error(str(e))
                    await self.prepare_state(reset=True)
                    continue
                else:
                    raise e

    async def get_terminal_output(
        self,
        session=0,
        reset_full_output=True,
        first_output_timeout=30,  # Wait up to x seconds for first output
        between_output_timeout=15,  # Wait up to x seconds between outputs
        max_exec_timeout=180,  # hard cap on total runtime
        sleep_time=0.1,
    ):
        # Common shell prompt regex patterns (add more as needed)
        prompt_patterns = [
            re.compile(r"\\(venv\\).+[$#] ?$"),  # (venv) ...$ or (venv) ...#
            re.compile(r"root@[^:]+:[^#]+# ?$"),  # root@container:~#
            re.compile(r"[a-zA-Z0-9_.-]+@[^:]+:[^$#]+[$#] ?$"),  # user@host:~$
        ]

        start_time = time.time()
        last_output_time = start_time
        full_output = ""
        truncated_output = ""
        got_output = False

        while True:
            await asyncio.sleep(sleep_time)
            full_output, partial_output = await self.state.shells[session].read_output(
                timeout=3, reset_full_output=reset_full_output
            )
            reset_full_output = False  # only reset once

            await self.agent.handle_intervention()

            now = time.time()
            if partial_output:
                PrintStyle(font_color="#85C1E9").stream(partial_output)
                # full_output += partial_output # Append new output
                truncated_output = truncate_text(
                    agent=self.agent, output=full_output, threshold=10000
                )
                self.log.update(content=truncated_output)
                last_output_time = now
                got_output = True

                # Check for shell prompt at the end of output
                last_lines = truncated_output.splitlines()[-3:] if truncated_output else []
                for line in last_lines:
                    for pat in prompt_patterns:
                        if pat.search(line.strip()):
                            PrintStyle.info("Detected shell prompt, returning output early.")
                            return truncated_output

            # Check for max execution time
            if now - start_time > max_exec_timeout:
                sysinfo = self.agent.read_prompt("fw.code.max_time.md", timeout=max_exec_timeout)
                response = self.agent.read_prompt("fw.code.info.md", info=sysinfo)
                if truncated_output:
                    response = truncated_output + "\n\n" + response
                PrintStyle.warning(sysinfo)
                self.log.update(content=response)
                return response

            # Waiting for first output
            if not got_output:
                if now - start_time > first_output_timeout:
                    sysinfo = self.agent.read_prompt(
                        "fw.code.no_out_time.md", timeout=first_output_timeout
                    )
                    response = self.agent.read_prompt("fw.code.info.md", info=sysinfo)
                    PrintStyle.warning(sysinfo)
                    self.log.update(content=response)
                    return response
            else:
                # Waiting for more output after first output
                if now - last_output_time > between_output_timeout:
                    sysinfo = self.agent.read_prompt(
                        "fw.code.pause_time.md", timeout=between_output_timeout
                    )
                    response = self.agent.read_prompt("fw.code.info.md", info=sysinfo)
                    if truncated_output:
                        response = truncated_output + "\n\n" + response
                    PrintStyle.warning(sysinfo)
                    self.log.update(content=response)
                    return response

    async def reset_terminal(self, session=0, reason: str | None = None):
        # Print the reason for the reset to the console if provided
        if reason:
            PrintStyle(font_color="#FFA500", bold=True).print(
                f"Resetting session {session}... Reason: {reason}"
            )
        else:
            PrintStyle(font_color="#FFA500", bold=True).print(
                f"Resetting session {session}..."
            )

        # Reset both secure and legacy sessions
        if (self.state.secure_manager and
            self.state.secure_sessions and
            session in self.state.secure_sessions):
            # Reset secure session
            secure_session_id = self.state.secure_sessions[session]
            self.state.secure_manager.close_session(secure_session_id)
            del self.state.secure_sessions[session]
            PrintStyle(font_color="#85C1E9").print(f"🔒 Secure session {session} reset")

        # Only reset the specified legacy session while preserving others
        await self.prepare_state(reset=True, session=session)
        response = self.agent.read_prompt(
            "fw.code.info.md", info=self.agent.read_prompt("fw.code.reset.md")
        )
        self.log.update(content=response)
        return response
