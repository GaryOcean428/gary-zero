"""
AI Action Visualization System Initialization.

This module initializes the unified AI action visualization system,
integrating all components into the Gary-Zero architecture.
"""

import asyncio
import os
from typing import Any

from framework.helpers.ai_action_interceptor import (
    get_ai_action_manager,
)
from framework.helpers.ai_action_streaming import (
    get_streaming_service,
)
from framework.helpers.log import Log


class AIActionVisualizationSystem:
    """Main system controller for AI action visualization."""

    def __init__(self):
        self.initialized = False
        self.action_manager = None
        self.streaming_service = None
        self.streaming_task = None
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            "auto_start_interception": os.getenv(
                "AI_VISUALIZATION_AUTO_START", "true"
            ).lower()
            == "true",
            "auto_start_streaming": os.getenv("AI_STREAMING_AUTO_START", "true").lower()
            == "true",
            "streaming_host": os.getenv("AI_STREAMING_HOST", "localhost"),
            "streaming_port": int(os.getenv("AI_STREAMING_PORT", "8765")),
            "max_action_history": int(os.getenv("AI_MAX_ACTION_HISTORY", "1000")),
            "websocket_enabled": os.getenv("AI_WEBSOCKET_ENABLED", "true").lower()
            == "true",
            "debug_mode": os.getenv("AI_VISUALIZATION_DEBUG", "false").lower()
            == "true",
        }

    async def initialize(self):
        """Initialize the AI action visualization system."""
        if self.initialized:
            return

        Log.log().info("🎯 Initializing AI Action Visualization System")

        try:
            # Initialize action manager
            self.action_manager = get_ai_action_manager()

            # Initialize streaming service
            self.streaming_service = get_streaming_service()
            self.streaming_service.host = self.config["streaming_host"]
            self.streaming_service.port = self.config["streaming_port"]
            self.streaming_service.max_history_size = self.config["max_action_history"]

            # Auto-start interception if enabled
            if self.config["auto_start_interception"]:
                await self._start_interception()

            # Auto-start streaming if enabled
            if self.config["auto_start_streaming"] and self.config["websocket_enabled"]:
                await self._start_streaming()

            # Set up action broadcasting
            self._setup_action_broadcasting()

            self.initialized = True
            Log.log().info("✅ AI Action Visualization System initialized")

            # Log system status
            await self._log_system_status()

        except Exception as e:
            Log.log().error(
                f"🚨 Failed to initialize AI Action Visualization System: {e}"
            )
            raise

    async def _start_interception(self):
        """Start AI action interception."""
        try:
            if not self.action_manager.active:
                self.action_manager.start_interception()
                Log.log().info("🎯 AI Action Interception started")
        except Exception as e:
            Log.log().error(f"Failed to start interception: {e}")

    async def _start_streaming(self):
        """Start AI action streaming service."""
        try:
            if not self.streaming_service.running:
                # Start streaming in background task
                self.streaming_task = asyncio.create_task(
                    self.streaming_service.start_server()
                )
                # Give it a moment to start
                await asyncio.sleep(0.5)
                Log.log().info(
                    f"🌐 AI Action Streaming started on "
                    f"ws://{self.streaming_service.host}:{self.streaming_service.port}"
                )
        except Exception as e:
            Log.log().error(f"Failed to start streaming: {e}")

    def _setup_action_broadcasting(self):
        """Set up action broadcasting from interceptor to streaming."""
        if self.action_manager and self.streaming_service:
            # Add handler to broadcast intercepted actions
            self.action_manager.add_action_handler(self._broadcast_action_handler)

    async def _broadcast_action_handler(self, action):
        """Handler to broadcast actions to streaming service."""
        try:
            if self.streaming_service and self.streaming_service.running:
                await self.streaming_service.broadcast_action(action)
        except Exception as e:
            if self.config["debug_mode"]:
                Log.log().debug(f"Action broadcast failed: {e}")

    async def _log_system_status(self):
        """Log current system status."""
        status = {
            "interception_active": self.action_manager.active
            if self.action_manager
            else False,
            "streaming_active": self.streaming_service.running
            if self.streaming_service
            else False,
            "intercepted_providers": len(self.action_manager.interceptors)
            if self.action_manager
            else 0,
            "streaming_url": f"ws://{self.config['streaming_host']}:{self.config['streaming_port']}"
            if self.config["websocket_enabled"]
            else "disabled",
        }

        Log.log().info(f"📊 AI Visualization Status: {status}")

    async def shutdown(self):
        """Shutdown the AI action visualization system."""
        Log.log().info("🛑 Shutting down AI Action Visualization System")

        try:
            # Stop interception
            if self.action_manager and self.action_manager.active:
                self.action_manager.stop_interception()

            # Stop streaming
            if self.streaming_service and self.streaming_service.running:
                await self.streaming_service.stop_server()

            # Cancel streaming task
            if self.streaming_task and not self.streaming_task.done():
                self.streaming_task.cancel()
                try:
                    await self.streaming_task
                except asyncio.CancelledError:
                    pass

            self.initialized = False
            Log.log().info("✅ AI Action Visualization System shutdown complete")

        except Exception as e:
            Log.log().error(f"Error during shutdown: {e}")

    def get_status(self) -> dict[str, Any]:
        """Get current system status."""
        return {
            "initialized": self.initialized,
            "config": self.config,
            "interception": {
                "active": self.action_manager.active if self.action_manager else False,
                "providers": list(self.action_manager.interceptors.keys())
                if self.action_manager
                else [],
                "action_count": len(self.action_manager.action_history)
                if self.action_manager
                else 0,
            },
            "streaming": {
                "active": self.streaming_service.running
                if self.streaming_service
                else False,
                "url": f"ws://{self.config['streaming_host']}:{self.config['streaming_port']}",
                "client_count": len(self.streaming_service.clients)
                if self.streaming_service
                else 0,
                "stats": self.streaming_service.get_server_stats()
                if self.streaming_service
                else {},
            },
        }


# Global system instance
_ai_visualization_system = None


def get_ai_visualization_system() -> AIActionVisualizationSystem:
    """Get the global AI visualization system."""
    global _ai_visualization_system
    if _ai_visualization_system is None:
        _ai_visualization_system = AIActionVisualizationSystem()
    return _ai_visualization_system


async def initialize_ai_visualization():
    """Initialize the AI action visualization system."""
    system = get_ai_visualization_system()
    await system.initialize()


async def shutdown_ai_visualization():
    """Shutdown the AI action visualization system."""
    system = get_ai_visualization_system()
    await system.shutdown()


def register_ui_integration():
    """Register UI integration for the visualization system."""
    # This function will be called by the main UI to ensure
    # the JavaScript components are loaded
    ui_scripts = ["/js/ai-action-visualization.js"]

    return {
        "scripts": ui_scripts,
        "websocket_url": f"ws://localhost:{get_ai_visualization_system().config['streaming_port']}",
        "features": [
            "real_time_streaming",
            "multi_provider_support",
            "action_interception",
            "morphism_visualization",
        ],
    }


# Integration hooks for Gary-Zero startup
async def on_gary_zero_startup():
    """Hook called during Gary-Zero startup."""
    try:
        await initialize_ai_visualization()
    except Exception as e:
        Log.log().error(f"Failed to initialize AI visualization during startup: {e}")


async def on_gary_zero_shutdown():
    """Hook called during Gary-Zero shutdown."""
    try:
        await shutdown_ai_visualization()
    except Exception as e:
        Log.log().error(f"Failed to shutdown AI visualization during shutdown: {e}")


# Tool registration integration
def get_visualization_tools():
    """Get all AI action visualization tools for registration."""
    from framework.tools.ai_action_visualization import (
        AI_ACTION_INTERCEPTION_TOOL,
        AI_ACTION_STREAMING_TOOL,
        AI_ACTION_UPDATE_TOOL,
        AI_ACTION_VISUALIZATION_TOOL,
    )

    return [
        AI_ACTION_VISUALIZATION_TOOL,
        AI_ACTION_UPDATE_TOOL,
        AI_ACTION_STREAMING_TOOL,
        AI_ACTION_INTERCEPTION_TOOL,
    ]


# Agent prompt integration
def get_agent_prompt_additions():
    """Get additional prompt content for agents about AI action visualization."""
    return """

## AI Action Visualization System

You now have access to a comprehensive AI action visualization system that provides real-time transparency 
for all AI provider actions including Claude Computer Use, OpenAI Operator, Google AI, browser automation, 
desktop interactions, and visual computer tasks.

### Available Visualization Tools:

1. **ai_action_visualize** - Create action visualizations
   - Use for any significant AI action that users should see
   - Supports all major AI providers and action types
   - Automatically creates real-time UI displays

2. **ai_action_update** - Update existing visualizations  
   - Update status, execution time, results
   - Add screenshots or additional data

3. **ai_action_streaming** - Control real-time streaming
   - Start/stop WebSocket streaming service
   - Get streaming statistics and status

4. **ai_action_interception** - Control action interception
   - Enable/disable automatic action detection
   - Monitor intercepted provider actions

### When to Use Visualizations:

- **Computer Use Actions**: Screenshots, clicks, keyboard input
- **Browser Automation**: Web navigation, form filling, scraping
- **Desktop Interactions**: File operations, window management
- **Shell Commands**: Terminal operations, security tools
- **Code Execution**: Long-running processes, compilations
- **Visual Tasks**: Image analysis, screenshot comparisons

### Example Usage:

```python
# Visualize a computer use action
await ai_action_visualize(
    provider="anthropic_claude",
    action_type="computer_use", 
    description="Taking screenshot for UI analysis",
    parameters={"action": "screenshot"},
    session_id="claude_session_1"
)

# Update when completed
await ai_action_update(
    session_id="claude_session_1",
    status="completed", 
    execution_time=1.2,
    screenshot_path="/tmp/screenshot_123.png"
)
```

The system automatically detects and visualizes actions from integrated AI providers. 
All visualizations appear in real-time with morphism effects and provider-specific styling.
"""
