"""
Session Configuration Management.

Centralized configuration for all remote session types and environments.
"""

import os
from dataclasses import dataclass, field
from typing import Any

from .session_interface import SessionType


@dataclass
class SessionConfig:
    """Configuration for session management."""

    # General session settings
    max_sessions_per_type: int = 10
    session_timeout: int = 300  # seconds
    connection_retry_attempts: int = 3
    connection_retry_delay: int = 5  # seconds
    health_check_interval: int = 60  # seconds

    # Connection pooling
    enable_connection_pooling: bool = True
    pool_size_per_type: int = 5
    max_idle_time: int = 300  # seconds

    # Security and approval
    require_approval_for_gui: bool = True
    require_approval_for_terminal: bool = True
    require_approval_for_external: bool = True
    approval_timeout: int = 30  # seconds

    # Memory and storage
    store_outputs_in_memory: bool = True
    max_output_size: int = 1024 * 1024  # 1MB
    output_retention_time: int = 3600  # seconds

    # Environment-specific configurations
    gemini_cli_config: dict[str, Any] = field(default_factory=dict)
    anthropic_computer_use_config: dict[str, Any] = field(default_factory=dict)
    claude_code_config: dict[str, Any] = field(default_factory=dict)
    kali_service_config: dict[str, Any] = field(default_factory=dict)
    e2b_config: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_environment(cls) -> 'SessionConfig':
        """
        Create session configuration from environment variables.
        
        Returns:
            SessionConfig instance with values from environment
        """
        config = cls()

        # General settings
        config.max_sessions_per_type = int(os.getenv('SESSION_MAX_PER_TYPE', '10'))
        config.session_timeout = int(os.getenv('SESSION_TIMEOUT', '300'))
        config.connection_retry_attempts = int(os.getenv('SESSION_RETRY_ATTEMPTS', '3'))
        config.connection_retry_delay = int(os.getenv('SESSION_RETRY_DELAY', '5'))
        config.health_check_interval = int(os.getenv('SESSION_HEALTH_CHECK_INTERVAL', '60'))

        # Connection pooling
        config.enable_connection_pooling = os.getenv('SESSION_ENABLE_POOLING', 'true').lower() == 'true'
        config.pool_size_per_type = int(os.getenv('SESSION_POOL_SIZE', '5'))
        config.max_idle_time = int(os.getenv('SESSION_MAX_IDLE_TIME', '300'))

        # Security and approval
        config.require_approval_for_gui = os.getenv('SESSION_REQUIRE_GUI_APPROVAL', 'true').lower() == 'true'
        config.require_approval_for_terminal = os.getenv('SESSION_REQUIRE_TERMINAL_APPROVAL', 'true').lower() == 'true'
        config.require_approval_for_external = os.getenv('SESSION_REQUIRE_EXTERNAL_APPROVAL', 'true').lower() == 'true'
        config.approval_timeout = int(os.getenv('SESSION_APPROVAL_TIMEOUT', '30'))

        # Memory and storage
        config.store_outputs_in_memory = os.getenv('SESSION_STORE_OUTPUTS', 'true').lower() == 'true'
        config.max_output_size = int(os.getenv('SESSION_MAX_OUTPUT_SIZE', str(1024 * 1024)))
        config.output_retention_time = int(os.getenv('SESSION_OUTPUT_RETENTION', '3600'))

        # Tool-specific configurations
        config.gemini_cli_config = {
            'enabled': os.getenv('GEMINI_CLI_ENABLED', 'false').lower() == 'true',
            'cli_path': os.getenv('GEMINI_CLI_PATH', 'gemini'),
            'approval_mode': os.getenv('GEMINI_CLI_APPROVAL_MODE', 'suggest'),
            'auto_install': os.getenv('GEMINI_CLI_AUTO_INSTALL', 'false').lower() == 'true',
            'api_key': os.getenv('GEMINI_API_KEY', ''),
            'model': os.getenv('GEMINI_LIVE_MODEL', 'models/gemini-2.5-flash-preview-native-audio-dialog'),
            'voice': os.getenv('GEMINI_LIVE_VOICE', 'Zephyr'),
            'response_modalities': os.getenv('GEMINI_LIVE_RESPONSE_MODALITIES', 'AUDIO')
        }

        config.anthropic_computer_use_config = {
            'enabled': os.getenv('ANTHROPIC_COMPUTER_USE_ENABLED', 'false').lower() == 'true',
            'require_approval': os.getenv('ANTHROPIC_COMPUTER_USE_REQUIRE_APPROVAL', 'true').lower() == 'true',
            'screenshot_interval': float(os.getenv('ANTHROPIC_COMPUTER_USE_SCREENSHOT_INTERVAL', '1.0')),
            'max_actions_per_session': int(os.getenv('ANTHROPIC_COMPUTER_USE_MAX_ACTIONS', '50')),
            'api_key': os.getenv('ANTHROPIC_API_KEY', '')
        }

        config.claude_code_config = {
            'enabled': os.getenv('CLAUDE_CODE_ENABLED', 'false').lower() == 'true',
            'max_file_size': int(os.getenv('CLAUDE_CODE_MAX_FILE_SIZE', str(1024*1024))),
            'allowed_extensions': os.getenv('CLAUDE_CODE_ALLOWED_EXTENSIONS', '.py,.js,.ts,.html,.css,.json,.md,.txt,.yml,.yaml,.toml').split(','),
            'restricted_paths': os.getenv('CLAUDE_CODE_RESTRICTED_PATHS', '.git,node_modules,__pycache__,.venv,venv').split(','),
            'enable_git_ops': os.getenv('CLAUDE_CODE_ENABLE_GIT', 'true').lower() == 'true',
            'enable_terminal': os.getenv('CLAUDE_CODE_ENABLE_TERMINAL', 'true').lower() == 'true'
        }

        config.kali_service_config = {
            'enabled': os.getenv('KALI_SERVICE_ENABLED', 'false').lower() == 'true',
            'base_url': os.getenv('KALI_SHELL_URL', 'http://kali-linux-docker.railway.internal:8080'),
            'host': os.getenv('KALI_SHELL_HOST', 'kali-linux-docker.railway.internal'),
            'port': int(os.getenv('KALI_SHELL_PORT', '8080')),
            'username': os.getenv('KALI_USERNAME'),
            'password': os.getenv('KALI_PASSWORD'),
            'public_url': os.getenv('KALI_PUBLIC_URL', 'https://kali-linux-docker.up.railway.app'),
            'ssh_port': int(os.getenv('KALI_SSH_PORT', '22'))
        }

        config.e2b_config = {
            'enabled': os.getenv('E2B_ENABLED', 'false').lower() == 'true',
            'api_key': os.getenv('E2B_API_KEY', ''),
            'environment': os.getenv('E2B_ENVIRONMENT', 'Python3'),
            'timeout': int(os.getenv('E2B_TIMEOUT', '300'))
        }

        return config

    def get_tool_config(self, tool_name: str) -> dict[str, Any]:
        """
        Get configuration for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool-specific configuration dictionary
        """
        tool_configs = {
            'gemini_cli': self.gemini_cli_config,
            'anthropic_computer_use': self.anthropic_computer_use_config,
            'claude_code': self.claude_code_config,
            'kali_service': self.kali_service_config,
            'e2b': self.e2b_config
        }
        return tool_configs.get(tool_name, {})

    def is_tool_enabled(self, tool_name: str) -> bool:
        """
        Check if a specific tool is enabled.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            True if tool is enabled, False otherwise
        """
        tool_config = self.get_tool_config(tool_name)
        return tool_config.get('enabled', False)

    def get_session_config_for_type(self, session_type: SessionType) -> dict[str, Any]:
        """
        Get configuration specific to a session type.
        
        Args:
            session_type: Type of session
            
        Returns:
            Session type specific configuration
        """
        type_configs = {
            SessionType.CLI: self.gemini_cli_config,
            SessionType.GUI: self.anthropic_computer_use_config,
            SessionType.TERMINAL: self.claude_code_config,
            SessionType.HTTP: self.kali_service_config,
            SessionType.SSH: self.kali_service_config,
            SessionType.WEBSOCKET: self.e2b_config
        }
        return type_configs.get(session_type, {})

    def requires_approval(self, session_type: SessionType) -> bool:
        """
        Check if a session type requires approval.
        
        Args:
            session_type: Type of session
            
        Returns:
            True if approval is required, False otherwise
        """
        if session_type == SessionType.GUI:
            return self.require_approval_for_gui
        elif session_type == SessionType.TERMINAL:
            return self.require_approval_for_terminal
        elif session_type in [SessionType.HTTP, SessionType.SSH, SessionType.WEBSOCKET]:
            return self.require_approval_for_external
        else:
            return False
