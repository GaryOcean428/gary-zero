"""
Session Manager Integration for Existing Tools.

This module provides session factories and integration helpers to connect
the new session management system with existing tool implementations.
"""

from ..session import RemoteSessionManager, SessionConfig, SessionType
from ..session.implementations import (
    AnthropicSession,
    ClaudeCodeSession,
    GeminiSession,
    KaliSession,
)


def create_session_manager(agent=None) -> RemoteSessionManager:
    """
    Create and configure a RemoteSessionManager with all session factories.

    Args:
        agent: Optional agent instance for integration

    Returns:
        Configured RemoteSessionManager
    """
    config = SessionConfig.from_environment()
    manager = RemoteSessionManager(config, agent)

    # Register session factories
    manager.register_session_factory(SessionType.CLI, create_gemini_session)
    manager.register_session_factory(SessionType.HTTP, create_kali_session)
    manager.register_session_factory(SessionType.GUI, create_anthropic_session)
    manager.register_session_factory(SessionType.TERMINAL, create_claude_code_session)

    # Register approval handlers if needed
    if agent:
        manager.register_approval_handler(
            SessionType.GUI, _create_gui_approval_handler(agent)
        )
        manager.register_approval_handler(
            SessionType.TERMINAL, _create_terminal_approval_handler(agent)
        )

    return manager


async def create_gemini_session(**kwargs) -> GeminiSession:
    """
    Factory function to create Gemini CLI sessions.

    Args:
        **kwargs: Additional configuration parameters

    Returns:
        GeminiSession instance
    """
    config = SessionConfig.from_environment()
    gemini_config = config.get_tool_config("gemini_cli")
    gemini_config.update(kwargs)
    return GeminiSession(gemini_config)


async def create_kali_session(**kwargs) -> KaliSession:
    """
    Factory function to create Kali service sessions.

    Args:
        **kwargs: Additional configuration parameters

    Returns:
        KaliSession instance
    """
    config = SessionConfig.from_environment()
    kali_config = config.get_tool_config("kali_service")
    kali_config.update(kwargs)
    return KaliSession(kali_config)


async def create_anthropic_session(**kwargs) -> AnthropicSession:
    """
    Factory function to create Anthropic Computer Use sessions.

    Args:
        **kwargs: Additional configuration parameters

    Returns:
        AnthropicSession instance
    """
    config = SessionConfig.from_environment()
    anthropic_config = config.get_tool_config("anthropic_computer_use")
    anthropic_config.update(kwargs)
    return AnthropicSession(anthropic_config)


async def create_claude_code_session(**kwargs) -> ClaudeCodeSession:
    """
    Factory function to create Claude Code sessions.

    Args:
        **kwargs: Additional configuration parameters

    Returns:
        ClaudeCodeSession instance
    """
    config = SessionConfig.from_environment()
    claude_config = config.get_tool_config("claude_code")
    claude_config.update(kwargs)
    return ClaudeCodeSession(claude_config)


def _create_gui_approval_handler(agent):
    """Create approval handler for GUI actions."""

    async def handle_gui_approval(session, message):
        """Handle approval for GUI automation actions."""
        try:
            action = message.payload.get("action", "unknown")
            action_desc = f"GUI Action: {action}"

            if action == "click":
                x, y = message.payload.get("x", 0), message.payload.get("y", 0)
                action_desc += f" at ({x}, {y})"
            elif action == "type":
                text = message.payload.get("text", "")[:50]
                action_desc += f" text: '{text}...'"
            elif action == "key":
                keys = message.payload.get("keys", "")
                action_desc += f" keys: '{keys}'"

            # Use agent's intervention system if available
            if hasattr(agent, "handle_intervention"):
                # This would integrate with the actual approval UI
                # For now, return True as a placeholder
                return True
            else:
                # Default approval logic
                return True

        except Exception:
            return False

    return handle_gui_approval


def _create_terminal_approval_handler(agent):
    """Create approval handler for terminal actions."""

    async def handle_terminal_approval(session, message):
        """Handle approval for terminal commands."""
        try:
            command = message.payload.get("command", "")
            operation_type = message.payload.get("operation_type", "")

            action_desc = f"Terminal {operation_type}: {command[:100]}"

            # Use agent's intervention system if available
            if hasattr(agent, "handle_intervention"):
                # This would integrate with the actual approval UI
                # For now, return True as a placeholder
                return True
            else:
                # Default approval logic - could implement command filtering here
                return True

        except Exception:
            return False

    return handle_terminal_approval


# Global session manager instance
_global_session_manager = None


def get_global_session_manager(agent=None) -> RemoteSessionManager:
    """
    Get or create the global session manager instance.

    Args:
        agent: Optional agent instance for first-time creation

    Returns:
        Global RemoteSessionManager instance
    """
    global _global_session_manager

    if _global_session_manager is None:
        _global_session_manager = create_session_manager(agent)

    return _global_session_manager


async def cleanup_global_session_manager():
    """Clean up the global session manager."""
    global _global_session_manager

    if _global_session_manager:
        await _global_session_manager.stop()
        _global_session_manager = None
