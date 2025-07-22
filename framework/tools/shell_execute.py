"""
Shell Execute Tool for Gary-Zero Kali Integration.

This tool provides secure execution of commands in the Kali Linux Docker service
with real-time UI feedback and comprehensive error handling.
"""

import os
import asyncio
import json
from typing import Dict, Any, Optional
from framework.tools.code_execution_tool import CodeExecutionTool
from framework.helpers.kali_executor import get_kali_executor, is_kali_execution_available
from framework.helpers.log import Log


class ShellExecuteTool(CodeExecutionTool):
    """
    Tool for executing commands in the Kali Linux shell environment.
    
    Extends the base CodeExecutionTool to provide specialized shell execution
    capabilities with UI integration and security tool access.
    """
    
    def __init__(self, **kwargs):
        """Initialize the shell execute tool."""
        super().__init__(**kwargs)
        self.executor = get_kali_executor()
        self.ui_events = []  # Store UI events for shell visualization
        
    def get_usage_docs(self) -> str:
        """Get usage documentation for the shell execute tool."""
        return """
# Shell Execute Tool

Execute commands in the Kali Linux security environment with real-time UI feedback.

## Usage Examples

### Basic Security Scan
```python
result = await shell_execute(
    command="nmap -sV target.com",
    description="Port scan with version detection",
    timeout=120
)
```

### Web Application Testing  
```python
result = await shell_execute(
    command="nikto -h https://target.com",
    description="Web vulnerability assessment",
    timeout=300
)
```

### SSL Certificate Analysis
```python
result = await shell_execute(
    command="echo | openssl s_client -connect target.com:443 2>/dev/null | openssl x509 -noout -text",
    description="SSL certificate detailed analysis",
    timeout=30
)
```

## Parameters
- `command`: Shell command to execute in Kali environment
- `description`: Purpose/description for logging and UI display  
- `timeout`: Maximum execution time in seconds (default: 30)
- `session_id`: Optional session identifier for stateful operations
- `show_ui`: Whether to show shell iframe to user (default: True)

## Returns
Dictionary with execution results:
- `success`: Boolean indicating if command succeeded
- `stdout`: Command output 
- `stderr`: Error output
- `exit_code`: Command exit code
- `ui_url`: URL for shell visualization iframe
- `execution_time`: Time taken in seconds
"""

    async def call(self, agent=None, **kwargs) -> Dict[str, Any]:
        """
        Execute a command in the Kali shell environment.
        
        Args:
            agent: Agent instance (for UI integration)
            **kwargs: Command parameters
            
        Returns:
            Dict containing execution results and UI information
        """
        command = kwargs.get('command', '')
        description = kwargs.get('description', 'Shell command execution')
        timeout = int(kwargs.get('timeout', 30))
        session_id = kwargs.get('session_id', 'default')
        show_ui = kwargs.get('show_ui', True)
        
        if not command:
            return {
                "success": False,
                "error": "No command provided",
                "stdout": "",
                "stderr": "Command parameter is required"
            }
        
        # Check if Kali service is available
        if not is_kali_execution_available():
            return {
                "success": False,
                "error": "Kali shell service not available",
                "stdout": "",
                "stderr": "Kali service not configured or unavailable. Check KALI_SHELL_URL environment variable.",
                "fallback_suggestion": "Consider using code_execution_tool for general command execution"
            }
        
        try:
            # Notify UI about shell operation start
            if show_ui and agent:
                await self._notify_ui_shell_start(agent, command, description, session_id)
            
            # Execute command in Kali environment
            result = await self.executor.execute_command(command, timeout)
            
            # Enhance result with UI information
            enhanced_result = {
                **result,
                "tool": "shell_execute",
                "command": command,
                "description": description,
                "session_id": session_id,
                "ui_url": self._get_shell_ui_url(session_id),
                "execution_time": result.get('execution_time', 0)
            }
            
            # Notify UI about completion
            if show_ui and agent:
                await self._notify_ui_shell_complete(agent, enhanced_result)
            
            return enhanced_result
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": f"Shell execution failed: {str(e)}",
                "stdout": "",
                "stderr": str(e),
                "command": command,
                "description": description
            }
            
            if show_ui and agent:
                await self._notify_ui_shell_error(agent, error_result)
            
            return error_result
    
    async def _notify_ui_shell_start(self, agent, command: str, description: str, session_id: str):
        """Notify UI that shell operation is starting."""
        event_data = {
            'type': 'shell_start',
            'command': command,
            'description': description,
            'session_id': session_id,
            'ui_url': self._get_shell_ui_url(session_id),
            'timestamp': self._get_timestamp()
        }
        
        await self._emit_ui_event(agent, 'shell_operation_start', event_data)
    
    async def _notify_ui_shell_complete(self, agent, result: Dict[str, Any]):
        """Notify UI that shell operation completed."""
        event_data = {
            'type': 'shell_complete',
            'success': result.get('success', False),
            'command': result.get('command', ''),
            'session_id': result.get('session_id', 'default'),
            'ui_url': result.get('ui_url', ''),
            'execution_time': result.get('execution_time', 0),
            'timestamp': self._get_timestamp()
        }
        
        await self._emit_ui_event(agent, 'shell_operation_complete', event_data)
    
    async def _notify_ui_shell_error(self, agent, error_result: Dict[str, Any]):
        """Notify UI about shell operation error."""
        event_data = {
            'type': 'shell_error',
            'error': error_result.get('error', 'Unknown error'),
            'command': error_result.get('command', ''),
            'timestamp': self._get_timestamp()
        }
        
        await self._emit_ui_event(agent, 'shell_operation_error', event_data)
    
    async def _emit_ui_event(self, agent, event_type: str, data: Dict[str, Any]):
        """Emit UI event for shell operations."""
        try:
            # Store event for later retrieval
            self.ui_events.append({
                'event_type': event_type,
                'data': data,
                'timestamp': self._get_timestamp()
            })
            
            # Try to emit via agent if available
            if hasattr(agent, 'emit_ui_event'):
                await agent.emit_ui_event(event_type, data)
            elif hasattr(agent, 'ui_state'):
                # Store in agent UI state as fallback
                if not agent.ui_state:
                    agent.ui_state = {}
                agent.ui_state['shell_events'] = self.ui_events[-5:]  # Keep last 5 events
                agent.ui_state['shell_active'] = (event_type == 'shell_operation_start')
                agent.ui_state['shell_url'] = data.get('ui_url', '')
                
        except Exception as e:
            # Log error but don't fail the main operation
            print(f"Warning: Failed to emit UI event: {e}")
    
    def _get_shell_ui_url(self, session_id: str) -> str:
        """Get the UI URL for shell visualization."""
        base_url = os.getenv('KALI_PUBLIC_URL', 'https://kali-linux-docker.up.railway.app')
        return f"{base_url}/terminal/{session_id}"
    
    def _get_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()


class ShellSessionTool(CodeExecutionTool):
    """Tool for managing interactive shell sessions."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.executor = get_kali_executor()
        self.active_sessions = {}
    
    async def call(self, agent=None, **kwargs) -> Dict[str, Any]:
        """Start or manage a shell session."""
        action = kwargs.get('action', 'start')  # start, stop, list
        session_id = kwargs.get('session_id', f"session_{int(time.time())}")
        session_type = kwargs.get('session_type', 'interactive')
        purpose = kwargs.get('purpose', 'Interactive shell session')
        
        if action == 'start':
            return await self._start_session(session_id, session_type, purpose, agent)
        elif action == 'stop':
            return await self._stop_session(session_id, agent)
        elif action == 'list':
            return self._list_sessions()
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "available_actions": ["start", "stop", "list"]
            }
    
    async def _start_session(self, session_id: str, session_type: str, purpose: str, agent) -> Dict[str, Any]:
        """Start a new shell session."""
        if not is_kali_execution_available():
            return {
                "success": False,
                "error": "Kali shell service not available"
            }
        
        try:
            # Initialize session
            session_info = {
                'id': session_id,
                'type': session_type,
                'purpose': purpose,
                'started_at': self._get_timestamp(),
                'ui_url': f"{os.getenv('KALI_PUBLIC_URL', '')}/terminal/{session_id}"
            }
            
            self.active_sessions[session_id] = session_info
            
            # Notify UI
            if agent:
                await self._emit_session_event(agent, 'session_start', session_info)
            
            return {
                "success": True,
                "session_id": session_id,
                "session_info": session_info,
                "message": f"Shell session '{session_id}' started successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start session: {str(e)}"
            }
    
    async def _stop_session(self, session_id: str, agent) -> Dict[str, Any]:
        """Stop a shell session."""
        if session_id not in self.active_sessions:
            return {
                "success": False,
                "error": f"Session '{session_id}' not found"
            }
        
        session_info = self.active_sessions.pop(session_id)
        
        # Notify UI
        if agent:
            await self._emit_session_event(agent, 'session_stop', session_info)
        
        return {
            "success": True,
            "session_id": session_id,
            "message": f"Session '{session_id}' stopped successfully"
        }
    
    def _list_sessions(self) -> Dict[str, Any]:
        """List active shell sessions."""
        return {
            "success": True,
            "active_sessions": list(self.active_sessions.keys()),
            "session_details": self.active_sessions,
            "total_sessions": len(self.active_sessions)
        }
    
    async def _emit_session_event(self, agent, event_type: str, session_info: Dict[str, Any]):
        """Emit session management events."""
        try:
            if hasattr(agent, 'emit_ui_event'):
                await agent.emit_ui_event(f'shell_{event_type}', session_info)
        except Exception as e:
            print(f"Warning: Failed to emit session event: {e}")
    
    def _get_timestamp(self) -> float:
        import time
        return time.time()


# Tool definitions for registration
SHELL_EXECUTE_TOOL = {
    "name": "shell_execute",
    "description": "Execute commands in Kali Linux security environment with real-time UI feedback",
    "class": ShellExecuteTool,
    "parameters": {
        "command": "Shell command to execute in Kali environment",
        "description": "Purpose/description for logging and UI display",
        "timeout": "Maximum execution time in seconds (default: 30)",
        "session_id": "Optional session identifier for stateful operations",
        "show_ui": "Whether to show shell iframe to user (default: True)"
    }
}

SHELL_SESSION_TOOL = {
    "name": "shell_session",
    "description": "Manage interactive shell sessions in Kali environment",
    "class": ShellSessionTool,
    "parameters": {
        "action": "Action to perform (start, stop, list)",
        "session_id": "Session identifier",
        "session_type": "Type of session (interactive, batch)",
        "purpose": "Purpose description for the session"
    }
}