"""Environment detection and execution mode configuration for Gary-Zero."""

import os
import socket
from typing import Dict, Any


def detect_execution_environment() -> str:
    """
    Detect the current execution environment.
    
    Returns:
        str: Environment type ('railway', 'docker', 'local')
    """
    # Check for Railway environment
    if os.getenv('RAILWAY_ENVIRONMENT'):
        return 'railway'
    
    # Check for Docker environment
    if os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER'):
        return 'docker'
    
    return 'local'


def is_ssh_available(host: str = '127.0.0.1', port: int = 55022, timeout: int = 3) -> bool:
    """
    Check if SSH is available on the specified host and port.
    
    Args:
        host: SSH host to check
        port: SSH port to check
        timeout: Connection timeout in seconds
        
    Returns:
        bool: True if SSH is available, False otherwise
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def should_use_ssh_execution() -> bool:
    """
    Determine if SSH execution should be used based on environment and availability.
    
    Returns:
        bool: True if SSH execution should be used, False otherwise
    """
    # Check if SSH is explicitly disabled
    if os.getenv('DISABLE_SSH_EXECUTION', '').lower() in ('true', '1', 'yes'):
        return False
    
    # Check if execution mode is explicitly set
    execution_mode = os.getenv('CODE_EXECUTION_MODE', '').lower()
    if execution_mode == 'direct':
        return False
    elif execution_mode == 'ssh':
        return True
    
    # Auto-detect based on environment
    env = detect_execution_environment()
    
    # In Railway, prefer direct execution unless SSH is explicitly enabled
    if env == 'railway':
        return False
    
    # In Docker, check if SSH is available
    if env == 'docker':
        return is_ssh_available()
    
    # For local development, check if SSH is available
    return is_ssh_available()


def get_execution_config() -> Dict[str, Any]:
    """
    Get the appropriate execution configuration based on environment.
    
    Returns:
        Dict[str, Any]: Execution configuration
    """
    if should_use_ssh_execution():
        return {
            'method': 'ssh',
            'host': os.getenv('CODE_EXEC_SSH_ADDR', '127.0.0.1'),
            'port': int(os.getenv('CODE_EXEC_SSH_PORT', '55022')),
            'username': os.getenv('CODE_EXEC_SSH_USER', 'root'),
            'password': os.getenv('CODE_EXEC_SSH_PASS', ''),
        }
    else:
        return {
            'method': 'direct',
            'shell': '/bin/bash',
            'environment': detect_execution_environment(),
        }


def get_execution_info() -> str:
    """
    Get human-readable information about the current execution configuration.
    
    Returns:
        str: Description of execution configuration
    """
    config = get_execution_config()
    env = detect_execution_environment()
    
    if config['method'] == 'ssh':
        ssh_available = "✅" if is_ssh_available(config['host'], config['port']) else "❌"
        return f"SSH execution on {config['host']}:{config['port']} {ssh_available} (environment: {env})"
    else:
        return f"Direct execution (environment: {env})"