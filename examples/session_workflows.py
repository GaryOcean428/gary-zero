"""
End-to-End Example Workflows for Remote Session Management.

Demonstrates the use of multiple tools in unified workflows using the
remote session management system.
"""

import asyncio
import json
import logging
from typing import Any

from framework.session import RemoteSessionManager, SessionType
from framework.session.integration import create_session_manager


class WorkflowExample:
    """Base class for workflow examples."""

    def __init__(self, session_manager: RemoteSessionManager):
        self.session_manager = session_manager
        self.logger = logging.getLogger(__name__)

    async def run(self) -> dict[str, Any]:
        """Run the workflow and return results."""
        raise NotImplementedError


class CodeGenerationWorkflow(WorkflowExample):
    """
    Example workflow: Generate code with Gemini CLI, test it via terminal,
    and capture screenshots via Anthropic Computer Use.
    """

    async def run(self) -> dict[str, Any]:
        """
        Execute the code generation workflow.

        Returns:
            Dictionary with workflow results
        """
        results = {"workflow": "code_generation", "steps": []}

        try:
            # Step 1: Generate code with Gemini CLI
            self.logger.info("Step 1: Generating code with Gemini CLI")

            gemini_message = self.session_manager.create_message(
                message_type="code_generation",
                payload={
                    "action": "code",
                    "task": "Create a simple Python web server using Flask",
                    "language": "python",
                },
            )

            gemini_response = await self.session_manager.execute_with_session(
                SessionType.CLI, gemini_message
            )

            results["steps"].append(
                {
                    "step": 1,
                    "description": "Code generation with Gemini CLI",
                    "success": gemini_response.success,
                    "output": gemini_response.data
                    if gemini_response.success
                    else gemini_response.error,
                }
            )

            if not gemini_response.success:
                return results

            # Step 2: Save generated code to file using Claude Code
            self.logger.info("Step 2: Saving generated code to file")

            generated_code = gemini_response.data.get("result", "")

            claude_message = self.session_manager.create_message(
                message_type="file_operation",
                payload={
                    "operation_type": "file",
                    "operation": "create",
                    "path": "app.py",
                    "content": generated_code,
                },
            )

            claude_response = await self.session_manager.execute_with_session(
                SessionType.TERMINAL, claude_message
            )

            results["steps"].append(
                {
                    "step": 2,
                    "description": "Save code to file with Claude Code",
                    "success": claude_response.success,
                    "output": claude_response.data
                    if claude_response.success
                    else claude_response.error,
                }
            )

            if not claude_response.success:
                return results

            # Step 3: Test the code by running it
            self.logger.info("Step 3: Testing the generated code")

            test_message = self.session_manager.create_message(
                message_type="terminal_command",
                payload={
                    "operation_type": "terminal",
                    "command": "python -m py_compile app.py",
                    "timeout": 10,
                },
            )

            test_response = await self.session_manager.execute_with_session(
                SessionType.TERMINAL, test_message
            )

            results["steps"].append(
                {
                    "step": 3,
                    "description": "Test code compilation",
                    "success": test_response.success,
                    "output": test_response.data
                    if test_response.success
                    else test_response.error,
                }
            )

            # Step 4: Take screenshot of the result (if GUI available)
            self.logger.info("Step 4: Taking screenshot")

            screenshot_message = self.session_manager.create_message(
                message_type="gui_action", payload={"action": "screenshot"}
            )

            screenshot_response = await self.session_manager.execute_with_session(
                SessionType.GUI, screenshot_message
            )

            results["steps"].append(
                {
                    "step": 4,
                    "description": "Take screenshot",
                    "success": screenshot_response.success,
                    "output": screenshot_response.data
                    if screenshot_response.success
                    else screenshot_response.error,
                }
            )

            results["success"] = all(step["success"] for step in results["steps"])

        except Exception as e:
            self.logger.error(f"Workflow error: {e}")
            results["error"] = str(e)
            results["success"] = False

        return results


class SecurityAuditWorkflow(WorkflowExample):
    """
    Example workflow: Run security audit using Kali tools and document
    results using Claude Code.
    """

    async def run(self, target: str = "example.com") -> dict[str, Any]:
        """
        Execute the security audit workflow.

        Args:
            target: Target to audit

        Returns:
            Dictionary with workflow results
        """
        results = {"workflow": "security_audit", "target": target, "steps": []}

        try:
            # Step 1: Run comprehensive security audit with Kali
            self.logger.info(f"Step 1: Running security audit on {target}")

            audit_message = self.session_manager.create_message(
                message_type="security_audit",
                payload={"action": "audit", "target": target},
            )

            audit_response = await self.session_manager.execute_with_session(
                SessionType.HTTP, audit_message
            )

            results["steps"].append(
                {
                    "step": 1,
                    "description": "Security audit with Kali tools",
                    "success": audit_response.success,
                    "output": audit_response.data
                    if audit_response.success
                    else audit_response.error,
                }
            )

            if not audit_response.success:
                return results

            # Step 2: Generate audit report using Claude Code
            self.logger.info("Step 2: Generating audit report")

            audit_data = audit_response.data.get("audit_results", {})
            report_content = self._generate_audit_report(target, audit_data)

            report_message = self.session_manager.create_message(
                message_type="file_operation",
                payload={
                    "operation_type": "file",
                    "operation": "create",
                    "path": f"audit_report_{target.replace('.', '_')}.md",
                    "content": report_content,
                },
            )

            report_response = await self.session_manager.execute_with_session(
                SessionType.TERMINAL, report_message
            )

            results["steps"].append(
                {
                    "step": 2,
                    "description": "Generate audit report",
                    "success": report_response.success,
                    "output": report_response.data
                    if report_response.success
                    else report_response.error,
                }
            )

            # Step 3: Commit report to Git (if available)
            self.logger.info("Step 3: Committing report to Git")

            git_add_message = self.session_manager.create_message(
                message_type="git_operation",
                payload={
                    "operation_type": "git",
                    "operation": "add",
                    "files": [f"audit_report_{target.replace('.', '_')}.md"],
                },
            )

            git_add_response = await self.session_manager.execute_with_session(
                SessionType.TERMINAL, git_add_message
            )

            if git_add_response.success:
                git_commit_message = self.session_manager.create_message(
                    message_type="git_operation",
                    payload={
                        "operation_type": "git",
                        "operation": "commit",
                        "message": f"Add security audit report for {target}",
                    },
                )

                git_commit_response = await self.session_manager.execute_with_session(
                    SessionType.TERMINAL, git_commit_message
                )

                results["steps"].append(
                    {
                        "step": 3,
                        "description": "Commit report to Git",
                        "success": git_commit_response.success,
                        "output": git_commit_response.data
                        if git_commit_response.success
                        else git_commit_response.error,
                    }
                )
            else:
                results["steps"].append(
                    {
                        "step": 3,
                        "description": "Commit report to Git",
                        "success": False,
                        "output": "Git add failed",
                    }
                )

            results["success"] = all(
                step["success"] for step in results["steps"][:2]
            )  # Main steps

        except Exception as e:
            self.logger.error(f"Workflow error: {e}")
            results["error"] = str(e)
            results["success"] = False

        return results

    def _generate_audit_report(self, target: str, audit_data: dict[str, Any]) -> str:
        """Generate a markdown audit report."""
        report_lines = [
            f"# Security Audit Report for {target}",
            "",
            f"**Generated:** {audit_data.get('timestamp', 'Unknown')}",
            "",
            "## Executive Summary",
            "",
            "This report contains the results of automated security scanning and analysis.",
            "",
            "## Port Scan Results",
            "",
        ]

        port_scan = audit_data.get("port_scan", {})
        if port_scan and not port_scan.get("error"):
            report_lines.extend(
                [
                    "### Open Ports",
                    "",
                    "```",
                    port_scan.get("stdout", "No output"),
                    "```",
                    "",
                ]
            )

        web_scan = audit_data.get("web_scan", {})
        if web_scan and not web_scan.get("error"):
            report_lines.extend(
                [
                    "## Web Vulnerability Scan",
                    "",
                    "```",
                    web_scan.get("stdout", "No output"),
                    "```",
                    "",
                ]
            )

        ssl_check = audit_data.get("ssl_check", {})
        if ssl_check and not ssl_check.get("error"):
            report_lines.extend(
                [
                    "## SSL Certificate Analysis",
                    "",
                    "```",
                    ssl_check.get("stdout", "No output"),
                    "```",
                    "",
                ]
            )

        report_lines.extend(
            [
                "## Recommendations",
                "",
                "1. Review all open ports and ensure only necessary services are exposed",
                "2. Keep all software components up to date",
                "3. Implement proper SSL/TLS configuration",
                "4. Regular security monitoring and assessment",
                "",
                "---",
                "*This report was generated automatically by Gary-Zero security audit workflow.*",
            ]
        )

        return "\n".join(report_lines)


class MultiToolShowcaseWorkflow(WorkflowExample):
    """
    Example workflow showcasing all tools working together.
    """

    async def run(self) -> dict[str, Any]:
        """
        Execute the multi-tool showcase workflow.

        Returns:
            Dictionary with workflow results
        """
        results = {"workflow": "multi_tool_showcase", "steps": []}

        try:
            # Step 1: Get workspace information with Claude Code
            self.logger.info("Step 1: Getting workspace information")

            workspace_message = self.session_manager.create_message(
                message_type="workspace_info",
                payload={"operation_type": "workspace", "operation": "info"},
            )

            workspace_response = await self.session_manager.execute_with_session(
                SessionType.TERMINAL, workspace_message
            )

            results["steps"].append(
                {
                    "step": 1,
                    "description": "Get workspace information",
                    "success": workspace_response.success,
                    "output": workspace_response.data
                    if workspace_response.success
                    else workspace_response.error,
                }
            )

            # Step 2: Generate documentation with Gemini CLI
            self.logger.info("Step 2: Generating documentation")

            doc_message = self.session_manager.create_message(
                message_type="documentation",
                payload={
                    "action": "generate",
                    "prompt": "Create a README.md file for a remote session management system",
                    "format": "markdown",
                },
            )

            doc_response = await self.session_manager.execute_with_session(
                SessionType.CLI, doc_message
            )

            results["steps"].append(
                {
                    "step": 2,
                    "description": "Generate documentation",
                    "success": doc_response.success,
                    "output": doc_response.data
                    if doc_response.success
                    else doc_response.error,
                }
            )

            # Step 3: Test Kali tools availability
            self.logger.info("Step 3: Testing Kali tools")

            tools_message = self.session_manager.create_message(
                message_type="tools_check", payload={"action": "tools"}
            )

            tools_response = await self.session_manager.execute_with_session(
                SessionType.HTTP, tools_message
            )

            results["steps"].append(
                {
                    "step": 3,
                    "description": "Check Kali tools availability",
                    "success": tools_response.success,
                    "output": tools_response.data
                    if tools_response.success
                    else tools_response.error,
                }
            )

            # Step 4: Take final screenshot
            self.logger.info("Step 4: Taking final screenshot")

            final_screenshot_message = self.session_manager.create_message(
                message_type="final_screenshot", payload={"action": "screenshot"}
            )

            final_screenshot_response = await self.session_manager.execute_with_session(
                SessionType.GUI, final_screenshot_message
            )

            results["steps"].append(
                {
                    "step": 4,
                    "description": "Take final screenshot",
                    "success": final_screenshot_response.success,
                    "output": final_screenshot_response.data
                    if final_screenshot_response.success
                    else final_screenshot_response.error,
                }
            )

            results["success"] = any(step["success"] for step in results["steps"])

        except Exception as e:
            self.logger.error(f"Workflow error: {e}")
            results["error"] = str(e)
            results["success"] = False

        return results


async def run_example_workflows():
    """
    Run all example workflows to demonstrate the session management system.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("🚀 Starting Remote Session Management Example Workflows")

    # Create session manager
    session_manager = create_session_manager()
    await session_manager.start()

    try:
        # Run Code Generation Workflow
        logger.info("\n" + "=" * 60)
        logger.info("Running Code Generation Workflow")
        logger.info("=" * 60)

        code_workflow = CodeGenerationWorkflow(session_manager)
        code_results = await code_workflow.run()

        logger.info("Code Generation Workflow Results:")
        logger.info(json.dumps(code_results, indent=2))

        # Run Security Audit Workflow
        logger.info("\n" + "=" * 60)
        logger.info("Running Security Audit Workflow")
        logger.info("=" * 60)

        audit_workflow = SecurityAuditWorkflow(session_manager)
        audit_results = await audit_workflow.run("httpbin.org")  # Safe test target

        logger.info("Security Audit Workflow Results:")
        logger.info(json.dumps(audit_results, indent=2))

        # Run Multi-Tool Showcase Workflow
        logger.info("\n" + "=" * 60)
        logger.info("Running Multi-Tool Showcase Workflow")
        logger.info("=" * 60)

        showcase_workflow = MultiToolShowcaseWorkflow(session_manager)
        showcase_results = await showcase_workflow.run()

        logger.info("Multi-Tool Showcase Workflow Results:")
        logger.info(json.dumps(showcase_results, indent=2))

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("WORKFLOW SUMMARY")
        logger.info("=" * 60)
        logger.info(
            f"Code Generation: {'✅ SUCCESS' if code_results.get('success') else '❌ FAILED'}"
        )
        logger.info(
            f"Security Audit: {'✅ SUCCESS' if audit_results.get('success') else '❌ FAILED'}"
        )
        logger.info(
            f"Multi-Tool Showcase: {'✅ SUCCESS' if showcase_results.get('success') else '❌ FAILED'}"
        )

        # Get session manager stats
        stats = await session_manager.get_manager_stats()
        logger.info("\nSession Manager Statistics:")
        logger.info(json.dumps(stats, indent=2))

    finally:
        await session_manager.stop()
        logger.info("🏁 Example workflows completed")


if __name__ == "__main__":
    asyncio.run(run_example_workflows())
