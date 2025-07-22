"""
Session-Enhanced Tool Integration.

This module shows how to integrate the new session management system
with existing tools to provide enhanced functionality.
"""

from framework.helpers.tool import Response, Tool
from framework.session import SessionType
from framework.session.integration import get_global_session_manager


class SessionEnhancedGeminiCLI(Tool):
    """Enhanced Google Gemini CLI tool using session management."""

    async def execute(self, **kwargs):
        """Execute Gemini CLI command using session management."""
        await self.agent.handle_intervention()

        # Get the global session manager
        session_manager = get_global_session_manager(self.agent)

        try:
            # Create message from tool arguments
            message = session_manager.create_message(
                message_type="gemini_cli",
                payload=self.args
            )

            # Execute with session management
            response = await session_manager.execute_with_session(
                SessionType.CLI, message
            )

            if response.success:
                return Response(
                    message=response.message,
                    break_loop=False
                )
            else:
                return Response(
                    message=f"❌ Gemini CLI error: {response.error}",
                    break_loop=False
                )

        except Exception as e:
            return Response(
                message=f"❌ Session management error: {str(e)}",
                break_loop=False
            )

    def get_log_object(self):
        return self.agent.context.log.log(
            type="session_gemini_cli",
            heading=f"{self.agent.agent_name}: Using session-enhanced Gemini CLI",
            content="",
            kvps=self.args,
        )


class SessionEnhancedAnthropicComputerUse(Tool):
    """Enhanced Anthropic Computer Use tool using session management."""

    async def execute(self, **kwargs):
        """Execute GUI automation using session management."""
        await self.agent.handle_intervention()

        session_manager = get_global_session_manager(self.agent)

        try:
            message = session_manager.create_message(
                message_type="anthropic_computer_use",
                payload=self.args
            )

            response = await session_manager.execute_with_session(
                SessionType.GUI, message
            )

            if response.success:
                return Response(
                    message=response.message,
                    break_loop=False
                )
            else:
                return Response(
                    message=f"❌ Computer Use error: {response.error}",
                    break_loop=False
                )

        except Exception as e:
            return Response(
                message=f"❌ Session management error: {str(e)}",
                break_loop=False
            )

    def get_log_object(self):
        return self.agent.context.log.log(
            type="session_computer_use",
            heading=f"{self.agent.agent_name}: Using session-enhanced Computer Use",
            content="",
            kvps=self.args,
        )


class SessionEnhancedClaudeCode(Tool):
    """Enhanced Claude Code tool using session management."""

    async def execute(self, **kwargs):
        """Execute code operations using session management."""
        await self.agent.handle_intervention()

        session_manager = get_global_session_manager(self.agent)

        try:
            message = session_manager.create_message(
                message_type="claude_code",
                payload=self.args
            )

            response = await session_manager.execute_with_session(
                SessionType.TERMINAL, message
            )

            if response.success:
                return Response(
                    message=response.message,
                    break_loop=False
                )
            else:
                return Response(
                    message=f"❌ Claude Code error: {response.error}",
                    break_loop=False
                )

        except Exception as e:
            return Response(
                message=f"❌ Session management error: {str(e)}",
                break_loop=False
            )

    def get_log_object(self):
        return self.agent.context.log.log(
            type="session_claude_code",
            heading=f"{self.agent.agent_name}: Using session-enhanced Claude Code",
            content="",
            kvps=self.args,
        )


class SessionEnhancedKaliService(Tool):
    """Enhanced Kali service tool using session management."""

    async def execute(self, **kwargs):
        """Execute security operations using session management."""
        await self.agent.handle_intervention()

        session_manager = get_global_session_manager(self.agent)

        try:
            message = session_manager.create_message(
                message_type="kali_service",
                payload=self.args
            )

            response = await session_manager.execute_with_session(
                SessionType.HTTP, message
            )

            if response.success:
                return Response(
                    message=response.message,
                    break_loop=False
                )
            else:
                return Response(
                    message=f"❌ Kali service error: {response.error}",
                    break_loop=False
                )

        except Exception as e:
            return Response(
                message=f"❌ Session management error: {str(e)}",
                break_loop=False
            )

    def get_log_object(self):
        return self.agent.context.log.log(
            type="session_kali_service",
            heading=f"{self.agent.agent_name}: Using session-enhanced Kali Service",
            content="",
            kvps=self.args,
        )


class UnifiedRemoteSessionTool(Tool):
    """
    Unified tool that can execute operations across all remote session types.
    
    This tool demonstrates how multiple session types can be coordinated
    in a single tool interface.
    """

    async def execute(self, **kwargs):
        """Execute unified remote session operations."""
        await self.agent.handle_intervention()

        session_manager = get_global_session_manager(self.agent)

        try:
            operation_type = self.args.get("operation_type", "")

            if operation_type == "code_generation_workflow":
                return await self._code_generation_workflow(session_manager)
            elif operation_type == "security_audit_workflow":
                return await self._security_audit_workflow(session_manager)
            elif operation_type == "multi_tool_demo":
                return await self._multi_tool_demo(session_manager)
            elif operation_type == "session_stats":
                return await self._get_session_stats(session_manager)
            else:
                return Response(
                    message=f"❌ Unknown operation type: {operation_type}. Available: code_generation_workflow, security_audit_workflow, multi_tool_demo, session_stats",
                    break_loop=False
                )

        except Exception as e:
            return Response(
                message=f"❌ Unified session tool error: {str(e)}",
                break_loop=False
            )

    async def _code_generation_workflow(self, session_manager):
        """Execute code generation workflow."""
        from examples.session_workflows import CodeGenerationWorkflow

        workflow = CodeGenerationWorkflow(session_manager)
        results = await workflow.run()

        success_count = sum(1 for step in results['steps'] if step['success'])
        total_steps = len(results['steps'])

        return Response(
            message=f"✅ Code generation workflow completed: {success_count}/{total_steps} steps successful",
            break_loop=False
        )

    async def _security_audit_workflow(self, session_manager):
        """Execute security audit workflow."""
        from examples.session_workflows import SecurityAuditWorkflow

        target = self.args.get("target", "example.com")
        workflow = SecurityAuditWorkflow(session_manager)
        results = await workflow.run(target)

        success_count = sum(1 for step in results['steps'] if step['success'])
        total_steps = len(results['steps'])

        return Response(
            message=f"✅ Security audit workflow for {target} completed: {success_count}/{total_steps} steps successful",
            break_loop=False
        )

    async def _multi_tool_demo(self, session_manager):
        """Execute multi-tool demonstration."""
        from examples.session_workflows import MultiToolShowcaseWorkflow

        workflow = MultiToolShowcaseWorkflow(session_manager)
        results = await workflow.run()

        success_count = sum(1 for step in results['steps'] if step['success'])
        total_steps = len(results['steps'])

        return Response(
            message=f"✅ Multi-tool showcase completed: {success_count}/{total_steps} steps successful",
            break_loop=False
        )

    async def _get_session_stats(self, session_manager):
        """Get session management statistics."""
        stats = await session_manager.get_manager_stats()

        message_lines = [
            "📊 Session Management Statistics:",
            f"   Running: {stats['running']}",
            f"   Registered Factories: {len(stats['registered_factories'])}",
            f"   Active Sessions: {stats['pool_stats']['total_active_sessions']}",
            f"   Pooled Sessions: {stats['pool_stats']['total_pooled_sessions']}",
            f"   Pooling Enabled: {stats['config']['pooling_enabled']}"
        ]

        return Response(
            message="\n".join(message_lines),
            break_loop=False
        )

    def get_log_object(self):
        return self.agent.context.log.log(
            type="unified_remote_session",
            heading=f"{self.agent.agent_name}: Using unified remote session tool",
            content="",
            kvps=self.args,
        )
