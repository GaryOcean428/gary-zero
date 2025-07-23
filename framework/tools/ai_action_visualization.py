"""
AI Action Visualization Tool Integration.

This module provides tools for integrating the unified AI action visualization
system with the existing Gary-Zero tool framework. It enables agents to trigger
and control action visualizations through standard tool calls.
"""

import asyncio
import os
from datetime import datetime
from typing import Any

from framework.helpers.ai_action_interceptor import (
    AIAction,
    AIActionType,
    AIProvider,
    get_ai_action_manager,
)
from framework.helpers.ai_action_streaming import broadcast_action, get_streaming_service
from framework.helpers.log import Log
from framework.tools.code_execution_tool import CodeExecutionTool


class AIActionVisualizationTool(CodeExecutionTool):
    """
    Tool for controlling and triggering AI action visualizations.
    
    Provides high-level interface for agents to create, update, and manage
    action visualizations across all AI providers and action types.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.action_manager = get_ai_action_manager()
        self.streaming_service = get_streaming_service()
        self.ui_events = []

    def get_usage_docs(self) -> str:
        """Get usage documentation for the AI action visualization tool."""
        return """
# AI Action Visualization Tool

Control and trigger unified AI action visualizations for transparency and monitoring.

## Usage Examples

### Trigger Computer Use Visualization
```python
result = await ai_action_visualize(
    provider="anthropic_claude",
    action_type="computer_use",
    description="Taking screenshot for analysis",
    parameters={"action": "screenshot"},
    session_id="claude_session_1"
)
```

### Create Browser Automation Visualization
```python
result = await ai_action_visualize(
    provider="browser_use",
    action_type="browser_automation",
    description="Navigating to target website",
    parameters={"url": "https://example.com"},
    ui_url="https://browser-preview.service.com/session/123"
)
```

### Start Desktop Interaction Monitoring
```python
result = await ai_action_visualize(
    provider="openai_operator",
    action_type="desktop_interaction",
    description="Operator performing file operations",
    parameters={"operation": "file_management"},
    status="started"
)
```

### Update Action Status
```python
result = await ai_action_update(
    action_id="existing_action_id",
    status="completed",
    execution_time=2.5,
    result={"success": True, "files_processed": 5}
)
```

## Parameters
- `provider`: AI provider (anthropic_claude, openai_operator, google_ai, etc.)
- `action_type`: Type of action (computer_use, browser_automation, etc.)
- `description`: Human-readable description of the action
- `parameters`: Action-specific parameters
- `session_id`: Session identifier for grouping actions
- `ui_url`: URL for action-specific interface
- `status`: Action status (started, completed, failed, error)
- `agent_name`: Name of the executing agent
- `screenshot_path`: Path to action screenshot
- `metadata`: Additional metadata

## Returns
Dictionary with visualization results:
- `success`: Boolean indicating if visualization was created
- `action_id`: Unique identifier for the action
- `visualization_url`: URL for viewing the visualization
- `streaming_enabled`: Whether real-time streaming is active
"""

    async def call(self, agent=None, **kwargs) -> dict[str, Any]:
        """
        Create or update an AI action visualization.
        
        Args:
            agent: Agent instance (for UI integration)
            **kwargs: Action parameters
            
        Returns:
            Dict containing visualization results
        """
        action_type = kwargs.get('action_type', 'code_execution')
        provider = kwargs.get('provider', 'gary_zero_native')
        description = kwargs.get('description', 'AI action visualization')
        parameters = kwargs.get('parameters', {})
        session_id = kwargs.get('session_id', f"viz_{int(datetime.now().timestamp())}")
        ui_url = kwargs.get('ui_url')
        status = kwargs.get('status', 'started')
        agent_name = kwargs.get('agent_name', 'Unknown Agent')
        screenshot_path = kwargs.get('screenshot_path')
        metadata = kwargs.get('metadata', {})

        try:
            # Create AI action
            action = AIAction(
                provider=AIProvider(provider),
                action_type=AIActionType(action_type),
                description=description,
                parameters=parameters,
                metadata=metadata,
                session_id=session_id,
                agent_name=agent_name,
                status=status,
                ui_url=ui_url,
                screenshot_path=screenshot_path
            )

            # Ensure interception is started
            if not self.action_manager.active:
                self.action_manager.start_interception()

            # Broadcast action for visualization
            await broadcast_action(action)

            # Emit UI event for immediate visualization
            if agent:
                await self._emit_visualization_event(agent, action)

            result = {
                "success": True,
                "action_id": action.action_id,
                "session_id": session_id,
                "visualization_created": True,
                "streaming_enabled": self.streaming_service.running,
                "visualization_url": self._get_visualization_url(action),
                "timestamp": action.timestamp.isoformat()
            }

            return result

        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid parameter: {str(e)}",
                "valid_providers": [p.value for p in AIProvider],
                "valid_action_types": [t.value for t in AIActionType]
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Visualization failed: {str(e)}"
            }

    async def _emit_visualization_event(self, agent, action: AIAction):
        """Emit UI event for visualization."""
        try:
            event_data = {
                'type': 'ai_action_visualization',
                'action_id': action.action_id,
                'provider': action.provider.value,
                'action_type': action.action_type.value,
                'description': action.description,
                'session_id': action.session_id,
                'status': action.status,
                'ui_url': action.ui_url,
                'screenshot_path': action.screenshot_path,
                'timestamp': action.timestamp.isoformat()
            }

            # Try to emit via agent
            if hasattr(agent, 'emit_ui_event'):
                await agent.emit_ui_event('ai_action_detected', event_data)
            elif hasattr(agent, 'ui_state'):
                # Store in agent UI state as fallback
                if not agent.ui_state:
                    agent.ui_state = {}
                agent.ui_state['ai_actions'] = agent.ui_state.get('ai_actions', [])
                agent.ui_state['ai_actions'].append(event_data)
                # Keep only last 10 actions
                agent.ui_state['ai_actions'] = agent.ui_state['ai_actions'][-10:]

        except Exception as e:
            Log.log().warning(f"Failed to emit visualization event: {e}")

    def _get_visualization_url(self, action: AIAction) -> str:
        """Get the URL for viewing the visualization."""
        base_url = os.getenv('GARY_ZERO_UI_URL', 'http://localhost:8080')
        return f"{base_url}/visualizations/{action.session_id}"


class AIActionUpdateTool(CodeExecutionTool):
    """Tool for updating existing AI action visualizations."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.streaming_service = get_streaming_service()

    async def call(self, agent=None, **kwargs) -> dict[str, Any]:
        """Update an existing AI action visualization."""
        action_id = kwargs.get('action_id')
        session_id = kwargs.get('session_id')
        status = kwargs.get('status')
        execution_time = kwargs.get('execution_time')
        result = kwargs.get('result')
        screenshot_path = kwargs.get('screenshot_path')

        if not action_id and not session_id:
            return {
                "success": False,
                "error": "Either action_id or session_id is required"
            }

        try:
            # Create update action
            update_action = AIAction(
                action_id=action_id or f"update_{int(datetime.now().timestamp())}",
                session_id=session_id or action_id,
                description=f"Action update: {status}",
                status=status or "updated",
                execution_time=execution_time,
                result=result,
                screenshot_path=screenshot_path
            )

            # Broadcast update
            await broadcast_action(update_action)

            return {
                "success": True,
                "action_id": update_action.action_id,
                "updated": True,
                "timestamp": update_action.timestamp.isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Update failed: {str(e)}"
            }


class AIActionStreamingControlTool(CodeExecutionTool):
    """Tool for controlling the AI action streaming service."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.streaming_service = get_streaming_service()

    async def call(self, agent=None, **kwargs) -> dict[str, Any]:
        """Control the AI action streaming service."""
        action = kwargs.get('action', 'status')  # start, stop, status, stats

        try:
            if action == 'start':
                if not self.streaming_service.running:
                    # Start streaming in background
                    asyncio.create_task(self.streaming_service.start_server())
                    await asyncio.sleep(1)  # Give it time to start

                return {
                    "success": True,
                    "action": "start",
                    "streaming_active": self.streaming_service.running,
                    "server_url": f"ws://{self.streaming_service.host}:{self.streaming_service.port}"
                }

            elif action == 'stop':
                if self.streaming_service.running:
                    await self.streaming_service.stop_server()

                return {
                    "success": True,
                    "action": "stop",
                    "streaming_active": self.streaming_service.running
                }

            elif action == 'status':
                return {
                    "success": True,
                    "streaming_active": self.streaming_service.running,
                    "server_url": f"ws://{self.streaming_service.host}:{self.streaming_service.port}",
                    "client_count": len(self.streaming_service.clients),
                    "stats": self.streaming_service.get_server_stats()
                }

            elif action == 'stats':
                return {
                    "success": True,
                    "stats": self.streaming_service.get_server_stats(),
                    "recent_actions": len(self.streaming_service.message_history)
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": ["start", "stop", "status", "stats"]
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Streaming control failed: {str(e)}"
            }


class AIActionInterceptionControlTool(CodeExecutionTool):
    """Tool for controlling AI action interception."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.action_manager = get_ai_action_manager()

    async def call(self, agent=None, **kwargs) -> dict[str, Any]:
        """Control AI action interception."""
        action = kwargs.get('action', 'status')  # start, stop, status

        try:
            if action == 'start':
                if not self.action_manager.active:
                    self.action_manager.start_interception()

                return {
                    "success": True,
                    "action": "start",
                    "interception_active": self.action_manager.active,
                    "intercepted_providers": list(self.action_manager.interceptors.keys())
                }

            elif action == 'stop':
                if self.action_manager.active:
                    self.action_manager.stop_interception()

                return {
                    "success": True,
                    "action": "stop",
                    "interception_active": self.action_manager.active
                }

            elif action == 'status':
                return {
                    "success": True,
                    "interception_active": self.action_manager.active,
                    "intercepted_providers": [p.value for p in self.action_manager.interceptors.keys()],
                    "recent_actions": len(self.action_manager.action_history),
                    "total_actions": len(self.action_manager.action_history)
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": ["start", "stop", "status"]
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Interception control failed: {str(e)}"
            }


# Tool definitions for registration
AI_ACTION_VISUALIZATION_TOOL = {
    "name": "ai_action_visualize",
    "description": "Create AI action visualizations for transparency and monitoring across all providers",
    "class": AIActionVisualizationTool,
    "parameters": {
        "provider": "AI provider (anthropic_claude, openai_operator, google_ai, etc.)",
        "action_type": "Type of action (computer_use, browser_automation, etc.)",
        "description": "Human-readable description of the action",
        "parameters": "Action-specific parameters (dict)",
        "session_id": "Session identifier for grouping actions",
        "ui_url": "URL for action-specific interface",
        "status": "Action status (started, completed, failed, error)",
        "agent_name": "Name of the executing agent",
        "screenshot_path": "Path to action screenshot",
        "metadata": "Additional metadata (dict)"
    }
}

AI_ACTION_UPDATE_TOOL = {
    "name": "ai_action_update",
    "description": "Update existing AI action visualizations with status, results, or additional data",
    "class": AIActionUpdateTool,
    "parameters": {
        "action_id": "Unique action identifier",
        "session_id": "Session identifier (alternative to action_id)",
        "status": "Updated status (completed, failed, error)",
        "execution_time": "Action execution time in seconds",
        "result": "Action result data (dict)",
        "screenshot_path": "Path to updated screenshot"
    }
}

AI_ACTION_STREAMING_TOOL = {
    "name": "ai_action_streaming",
    "description": "Control real-time AI action streaming service",
    "class": AIActionStreamingControlTool,
    "parameters": {
        "action": "Control action (start, stop, status, stats)"
    }
}

AI_ACTION_INTERCEPTION_TOOL = {
    "name": "ai_action_interception",
    "description": "Control AI action interception across all providers",
    "class": AIActionInterceptionControlTool,
    "parameters": {
        "action": "Control action (start, stop, status)"
    }
}
