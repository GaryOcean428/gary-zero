#!/usr/bin/env python3
"""
AI Action Visualization System Demo.

This script demonstrates the comprehensive AI action visualization capabilities
across all supported providers and action types.
"""

import asyncio
import os

from framework.helpers.ai_action_interceptor import (
    AIAction,
    AIActionType,
    AIProvider,
    get_ai_action_manager,
)
from framework.helpers.ai_action_streaming import broadcast_action, get_streaming_service
from framework.helpers.ai_visualization_init import initialize_ai_visualization
from framework.helpers.log import Log


class AIActionVisualizationDemo:
    """Demo class for AI action visualization system."""

    def __init__(self):
        self.log = Log.Log()
        self.demo_actions = []

    async def run_demo(self):
        """Run the complete AI action visualization demo."""
        print("🎯 AI Action Visualization System Demo")
        print("=" * 60)

        # Initialize the system
        await self.initialize_system()

        # Run demo scenarios
        await self.demo_computer_use_actions()
        await self.demo_browser_automation()
        await self.demo_desktop_interactions()
        await self.demo_shell_commands()
        await self.demo_multi_provider_scenario()

        # Show system status
        await self.show_system_status()

        print("\n🎉 Demo complete! Check the UI for visualizations.")

    async def initialize_system(self):
        """Initialize the AI visualization system."""
        print("\n📦 Initializing AI Action Visualization System...")

        try:
            await initialize_ai_visualization()
            print("✅ System initialized successfully")

            # Give the streaming server a moment to start
            await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            raise

    async def demo_computer_use_actions(self):
        """Demo computer use actions from various providers."""
        print("\n🖥️ Demonstrating Computer Use Actions")
        print("-" * 40)

        # Claude Computer Use - Screenshot
        action1 = AIAction(
            provider=AIProvider.ANTHROPIC_CLAUDE,
            action_type=AIActionType.COMPUTER_USE,
            description="Claude taking screenshot for UI analysis",
            parameters={"action": "screenshot", "reason": "Analyzing current screen"},
            agent_name="Claude Computer Use Agent",
            session_id="claude_session_1"
        )
        await self.broadcast_and_update_action(action1, "completed", 1.2)

        # Claude Computer Use - Click action
        action2 = AIAction(
            provider=AIProvider.ANTHROPIC_CLAUDE,
            action_type=AIActionType.MOUSE_ACTION,
            description="Claude clicking on button element",
            parameters={"action": "click", "x": 450, "y": 200, "element": "submit_button"},
            agent_name="Claude Computer Use Agent",
            session_id="claude_session_2"
        )
        await self.broadcast_and_update_action(action2, "completed", 0.8)

        # OpenAI Operator - Desktop operation
        action3 = AIAction(
            provider=AIProvider.OPENAI_OPERATOR,
            action_type=AIActionType.DESKTOP_INTERACTION,
            description="OpenAI Operator managing application windows",
            parameters={"operation": "window_management", "target": "file_explorer"},
            agent_name="OpenAI Operator Agent",
            session_id="operator_session_1"
        )
        await self.broadcast_and_update_action(action3, "completed", 2.1)

    async def demo_browser_automation(self):
        """Demo browser automation actions."""
        print("\n🌐 Demonstrating Browser Automation")
        print("-" * 40)

        # Browser navigation
        action1 = AIAction(
            provider=AIProvider.BROWSER_USE,
            action_type=AIActionType.BROWSER_AUTOMATION,
            description="Navigating to target website for analysis",
            parameters={"url": "https://example.com", "action": "navigate"},
            agent_name="Browser Automation Agent",
            session_id="browser_session_1",
            ui_url="https://browser-preview.service.com/session/123"
        )
        await self.broadcast_and_update_action(action1, "completed", 3.2)

        # Form filling
        action2 = AIAction(
            provider=AIProvider.BROWSER_USE,
            action_type=AIActionType.BROWSER_AUTOMATION,
            description="Filling form with user data",
            parameters={"action": "fill_form", "fields": ["name", "email", "message"]},
            agent_name="Browser Automation Agent",
            session_id="browser_session_2"
        )
        await self.broadcast_and_update_action(action2, "completed", 1.8)

    async def demo_desktop_interactions(self):
        """Demo desktop interaction actions."""
        print("\n🖱️ Demonstrating Desktop Interactions")
        print("-" * 40)

        # File operations
        action1 = AIAction(
            provider=AIProvider.GOOGLE_AI,
            action_type=AIActionType.FILE_OPERATION,
            description="Google AI organizing project files",
            parameters={"operation": "organize", "path": "/projects", "files_count": 15},
            agent_name="Google AI File Manager",
            session_id="google_session_1"
        )
        await self.broadcast_and_update_action(action1, "completed", 4.5)

        # Visual computer task
        action2 = AIAction(
            provider=AIProvider.GOOGLE_AI,
            action_type=AIActionType.VISUAL_COMPUTER_TASK,
            description="Analyzing UI components for accessibility",
            parameters={"task": "accessibility_analysis", "elements_analyzed": 23},
            agent_name="Google AI Vision Agent",
            session_id="google_session_2",
            screenshot_path="/tmp/ui_analysis_screenshot.png"
        )
        await self.broadcast_and_update_action(action2, "completed", 6.3)

    async def demo_shell_commands(self):
        """Demo shell command execution."""
        print("\n🛡️ Demonstrating Shell Commands")
        print("-" * 40)

        # Security scan
        action1 = AIAction(
            provider=AIProvider.KALI_SHELL,
            action_type=AIActionType.SHELL_COMMAND,
            description="Running comprehensive security scan",
            parameters={"command": "nmap -sV -sC target.com", "tool": "nmap"},
            agent_name="Kali Security Agent",
            session_id="kali_session_1",
            ui_url="https://kali-linux-docker.up.railway.app/terminal/kali_session_1"
        )
        await self.broadcast_and_update_action(action1, "completed", 15.7)

        # Web vulnerability assessment
        action2 = AIAction(
            provider=AIProvider.KALI_SHELL,
            action_type=AIActionType.SHELL_COMMAND,
            description="Web application vulnerability assessment",
            parameters={"command": "nikto -h https://target.com", "tool": "nikto"},
            agent_name="Kali Security Agent",
            session_id="kali_session_2"
        )
        await self.broadcast_and_update_action(action2, "completed", 22.4)

    async def demo_multi_provider_scenario(self):
        """Demo a complex multi-provider scenario."""
        print("\n🎭 Demonstrating Multi-Provider Scenario")
        print("-" * 40)

        # Coordinated action sequence
        actions = [
            # 1. Claude takes screenshot
            AIAction(
                provider=AIProvider.ANTHROPIC_CLAUDE,
                action_type=AIActionType.SCREENSHOT,
                description="Initial screenshot for analysis",
                agent_name="Claude Coordinator",
                session_id="multi_scenario_1"
            ),

            # 2. Browser agent navigates
            AIAction(
                provider=AIProvider.BROWSER_USE,
                action_type=AIActionType.BROWSER_AUTOMATION,
                description="Navigate to target for investigation",
                agent_name="Browser Scout Agent",
                session_id="multi_scenario_2"
            ),

            # 3. Kali runs security check
            AIAction(
                provider=AIProvider.KALI_SHELL,
                action_type=AIActionType.SHELL_COMMAND,
                description="Security assessment of target",
                parameters={"command": "nmap -A target.com"},
                agent_name="Security Analyst Agent",
                session_id="multi_scenario_3"
            ),

            # 4. Google AI analyzes results
            AIAction(
                provider=AIProvider.GOOGLE_AI,
                action_type=AIActionType.VISUAL_COMPUTER_TASK,
                description="Analyzing security scan results",
                agent_name="AI Analysis Agent",
                session_id="multi_scenario_4"
            )
        ]

        # Execute actions in sequence with proper timing
        for i, action in enumerate(actions, 1):
            print(f"  Step {i}: {action.description}")
            await broadcast_action(action)
            await asyncio.sleep(1)  # Simulate processing time

            # Update with completion
            action.status = "completed"
            action.execution_time = 2.0 + i * 0.5
            await broadcast_action(action)
            await asyncio.sleep(0.5)

    async def broadcast_and_update_action(self, action: AIAction, final_status: str, execution_time: float):
        """Broadcast an action and then update it with completion status."""
        # Broadcast start
        print(f"  🚀 {action.description}")
        await broadcast_action(action)
        await asyncio.sleep(0.5)  # Brief pause for visualization

        # Simulate processing time
        await asyncio.sleep(min(2.0, execution_time * 0.3))

        # Broadcast completion
        action.status = final_status
        action.execution_time = execution_time
        action.result = {
            "success": final_status == "completed",
            "processing_time": execution_time,
            "demo_action": True
        }

        await broadcast_action(action)
        print(f"  ✅ Completed in {execution_time}s")

        self.demo_actions.append(action)

    async def show_system_status(self):
        """Show the current system status."""
        print("\n📊 System Status")
        print("-" * 40)

        # Get action manager status
        action_manager = get_ai_action_manager()
        print(f"Action Interception: {'🟢 Active' if action_manager.active else '🔴 Inactive'}")
        print(f"Intercepted Providers: {len(action_manager.interceptors)}")
        print(f"Total Actions Captured: {len(action_manager.action_history)}")

        # Get streaming service status
        streaming_service = get_streaming_service()
        print(f"Streaming Service: {'🟢 Active' if streaming_service.running else '🔴 Inactive'}")
        print(f"Connected Clients: {len(streaming_service.clients)}")
        print(f"Messages Sent: {streaming_service.stats['messages_sent']}")

        # Demo summary
        print(f"\nDemo Actions Created: {len(self.demo_actions)}")

        # Provider breakdown
        provider_counts = {}
        for action in self.demo_actions:
            provider = action.provider.value
            provider_counts[provider] = provider_counts.get(provider, 0) + 1

        print("\nActions by Provider:")
        for provider, count in provider_counts.items():
            print(f"  {provider}: {count}")


async def main():
    """Main demo function."""
    demo = AIActionVisualizationDemo()

    try:
        await demo.run_demo()

        # Keep running for a bit to allow visualization viewing
        print("\n⏳ Demo running for 30 seconds to allow visualization viewing...")
        print("🌐 Connect to the UI at http://localhost:8080 to see visualizations")
        print("🔗 WebSocket streaming at ws://localhost:8765")

        await asyncio.sleep(30)

    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        raise


if __name__ == "__main__":
    # Set environment variables for demo
    os.environ.setdefault("AI_VISUALIZATION_AUTO_START", "true")
    os.environ.setdefault("AI_STREAMING_AUTO_START", "true")
    os.environ.setdefault("AI_VISUALIZATION_DEBUG", "true")

    asyncio.run(main())
