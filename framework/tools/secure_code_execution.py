"""
Enhanced secure code execution tool using isolated environments.
This tool replaces the existing code execution with secure sandboxed execution.
"""
import asyncio
from dataclasses import dataclass
from typing import Dict, Any, Optional

from framework.helpers.tool import Response, Tool
from framework.helpers.print_style import PrintStyle
from framework.executors.secure_manager import SecureCodeExecutionManager


@dataclass
class SecureState:
    manager: SecureCodeExecutionManager
    user_sessions: Dict[str, str]  # Maps user_id to session_id


class SecureCodeExecution(Tool):
    """Secure code execution tool using E2B or Docker isolation."""

    async def execute(self, **kwargs):
        await self.agent.handle_intervention()
        await self.prepare_state()

        runtime = self.args.get("runtime", "").lower().strip()
        user_id = self.args.get("user_id", "default")

        if runtime == "python":
            response = await self.execute_python_code(
                code=self.args["code"], user_id=user_id
            )
        elif runtime == "nodejs":
            response = await self.execute_nodejs_code(
                code=self.args["code"], user_id=user_id
            )
        elif runtime == "terminal":
            response = await self.execute_terminal_command(
                command=self.args["code"], user_id=user_id
            )
        elif runtime == "info":
            response = await self.get_executor_info()
        elif runtime == "reset":
            response = await self.reset_session(user_id=user_id)
        elif runtime == "install":
            package = self.args.get("package", "")
            if not package:
                response = self.agent.read_prompt("fw.code.runtime_wrong.md", runtime="install (missing package name)")
            else:
                response = await self.install_package(package=package, user_id=user_id)
        else:
            response = self.agent.read_prompt("fw.code.runtime_wrong.md", runtime=runtime)

        if not response:
            response = self.agent.read_prompt(
                "fw.code.info.md", info=self.agent.read_prompt("fw.code.no_output.md")
            )
        return Response(message=response, break_loop=False)

    def get_log_object(self):
        return self.agent.context.log.log(
            type="secure_code_exe",
            heading=f"{self.agent.agent_name}: Using secure tool '{self.name}'",
            content="",
            kvps=self.args,
        )

    async def after_execution(self, response, **kwargs):
        self.agent.hist_add_tool_result(self.name, response.message)

    async def prepare_state(self, reset=False):
        """Prepare the secure execution state."""
        self.state = self.agent.get_data("_secure_cet_state")
        if not self.state or reset:
            manager = SecureCodeExecutionManager()
            user_sessions = {} if not self.state else self.state.user_sessions.copy()
            
            if reset:
                # Clean up existing sessions
                if self.state and self.state.manager:
                    self.state.manager.cleanup_all()
                user_sessions = {}

            self.state = SecureState(manager=manager, user_sessions=user_sessions)
        
        self.agent.set_data("_secure_cet_state", self.state)

    def _get_or_create_session(self, user_id: str) -> str:
        """Get or create a session for the user."""
        if user_id not in self.state.user_sessions:
            session_id = self.state.manager.create_session()
            self.state.user_sessions[user_id] = session_id
            print(f"✅ Created new session for user {user_id}: {session_id}")
        return self.state.user_sessions[user_id]

    async def execute_python_code(self, code: str, user_id: str = "default") -> str:
        """Execute Python code in secure environment."""
        try:
            session_id = self._get_or_create_session(user_id)
            
            PrintStyle(background_color="blue", font_color="white", bold=True).print(
                f"{self.agent.agent_name} secure Python execution"
            )
            
            # Show executor info for transparency
            executor_info = self.state.manager.get_executor_info()
            PrintStyle(font_color="#85C1E9").print(
                f"Execution environment: {executor_info['description']}"
            )
            
            result = self.state.manager.execute_code(session_id, code, "python")
            
            if result["success"]:
                output = result["stdout"]
                execution_time = result.get("execution_time", 0)
                
                if output:
                    PrintStyle(font_color="#85C1E9").print(output)
                
                response_parts = []
                if output:
                    response_parts.append(f"Output:\n{output}")
                
                response_parts.append(f"✅ Execution completed in {execution_time:.2f}s using {result.get('executor_type', 'unknown')} executor")
                
                # Add any rich results if available (E2B)
                if "results" in result and result["results"]:
                    response_parts.append(f"Rich outputs: {len(result['results'])} items generated")
                
                return "\n\n".join(response_parts)
            else:
                error_msg = result.get("error", "Unknown error")
                stderr = result.get("stderr", "")
                
                error_output = f"❌ Execution failed: {error_msg}"
                if stderr:
                    error_output += f"\nStderr: {stderr}"
                
                if "security_warning" in result:
                    error_output += f"\n⚠️  Security Warning: {result['security_warning']}"
                
                PrintStyle.error(error_output)
                return error_output
                
        except Exception as e:
            error_msg = f"❌ Secure execution error: {str(e)}"
            PrintStyle.error(error_msg)
            return error_msg

    async def execute_nodejs_code(self, code: str, user_id: str = "default") -> str:
        """Execute Node.js code in secure environment."""
        try:
            session_id = self._get_or_create_session(user_id)
            
            PrintStyle(background_color="green", font_color="white", bold=True).print(
                f"{self.agent.agent_name} secure Node.js execution"
            )
            
            # For Node.js, we'll use shell execution with node command
            node_command = f"node -e '{code}'"
            result = self.state.manager.execute_code(session_id, node_command, "bash")
            
            if result["success"]:
                output = result["stdout"]
                execution_time = result.get("execution_time", 0)
                
                if output:
                    PrintStyle(font_color="#85C1E9").print(output)
                
                response = f"✅ Node.js execution completed in {execution_time:.2f}s"
                if output:
                    response = f"Output:\n{output}\n\n{response}"
                
                return response
            else:
                error_msg = f"❌ Node.js execution failed: {result.get('error', 'Unknown error')}"
                PrintStyle.error(error_msg)
                return error_msg
                
        except Exception as e:
            error_msg = f"❌ Secure Node.js execution error: {str(e)}"
            PrintStyle.error(error_msg)
            return error_msg

    async def execute_terminal_command(self, command: str, user_id: str = "default") -> str:
        """Execute terminal command in secure environment."""
        try:
            session_id = self._get_or_create_session(user_id)
            
            PrintStyle(background_color="black", font_color="white", bold=True).print(
                f"{self.agent.agent_name} secure terminal execution"
            )
            
            result = self.state.manager.execute_code(session_id, command, "bash")
            
            if result["success"]:
                output = result["stdout"]
                execution_time = result.get("execution_time", 0)
                
                if output:
                    PrintStyle(font_color="#85C1E9").print(output)
                
                response = f"✅ Command completed in {execution_time:.2f}s"
                if output:
                    response = f"Output:\n{output}\n\n{response}"
                
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

    async def install_package(self, package: str, user_id: str = "default") -> str:
        """Install a package in the secure environment."""
        try:
            session_id = self._get_or_create_session(user_id)
            
            PrintStyle(background_color="yellow", font_color="black", bold=True).print(
                f"{self.agent.agent_name} secure package installation"
            )
            
            result = self.state.manager.install_package(session_id, package)
            
            if result["success"]:
                execution_time = result.get("execution_time", 0)
                response = f"✅ Package '{package}' installed successfully in {execution_time:.2f}s"
                PrintStyle(font_color="#85C1E9").print(response)
                return response
            else:
                error_msg = f"❌ Package installation failed: {result.get('error', 'Unknown error')}"
                PrintStyle.error(error_msg)
                return error_msg
                
        except Exception as e:
            error_msg = f"❌ Package installation error: {str(e)}"
            PrintStyle.error(error_msg)
            return error_msg

    async def get_executor_info(self) -> str:
        """Get information about the current execution environment."""
        try:
            info = self.state.manager.get_executor_info()
            
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
            
        except Exception as e:
            error_msg = f"❌ Error getting executor info: {str(e)}"
            PrintStyle.error(error_msg)
            return error_msg

    async def reset_session(self, user_id: str = "default") -> str:
        """Reset the execution session for a user."""
        try:
            if user_id in self.state.user_sessions:
                session_id = self.state.user_sessions[user_id]
                self.state.manager.close_session(session_id)
                del self.state.user_sessions[user_id]
                
                response = f"✅ Session reset for user {user_id}"
            else:
                response = f"ℹ️  No existing session found for user {user_id}"
            
            PrintStyle(font_color="#FFA500", bold=True).print(response)
            return response
            
        except Exception as e:
            error_msg = f"❌ Error resetting session: {str(e)}"
            PrintStyle.error(error_msg)
            return error_msg