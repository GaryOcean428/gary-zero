"""
Kali Linux Docker Service Integration for Gary-Zero.

This module provides integration with the Kali Linux Docker service deployed
on Railway, enabling secure code execution and penetration testing capabilities.
"""

import os
import time
import logging
import requests
from typing import Dict, Any, Optional, Union
from urllib.parse import urljoin

from framework.helpers.shell_ssh import SSHInteractiveSession
from framework.helpers.log import Log


class KaliServiceConnector:
    """
    Connector for Kali Linux Docker service running on Railway.
    
    Provides HTTP API access and SSH-like interactive session capabilities
    for executing commands in the Kali environment.
    """
    
    def __init__(self, logger: Optional[Log] = None):
        """
        Initialize Kali service connector.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or self._create_default_logger()
        self.base_url = os.getenv('KALI_SHELL_URL', 'http://kali-linux-docker.railway.internal:8080')
        self.host = os.getenv('KALI_SHELL_HOST', 'kali-linux-docker.railway.internal')
        self.port = int(os.getenv('KALI_SHELL_PORT', '8080'))
        self.username = os.getenv('KALI_USERNAME', 'GaryOcean')
        self.password = os.getenv('KALI_PASSWORD', 'I.Am.Dev.1')
        self.public_url = os.getenv('KALI_PUBLIC_URL', 'https://kali-linux-docker.up.railway.app')
        
        # Session for persistent HTTP connections
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Gary-Zero-Agent/1.0'
        })
        
        # SSH session for interactive shell access
        self._ssh_session: Optional[SSHInteractiveSession] = None
        
    def _create_default_logger(self) -> Log:
        """Create a default logger if none provided."""
        logging.basicConfig(level=logging.INFO)
        return Log()
    
    def is_available(self) -> bool:
        """
        Check if the Kali service is available and responding.
        
        Returns:
            bool: True if service is available, False otherwise
        """
        try:
            response = self.session.get(
                urljoin(self.base_url, '/health'),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Kali service health check failed: {e}")
            return False
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about the Kali service.
        
        Returns:
            Dict containing service information
        """
        try:
            response = self.session.get(
                urljoin(self.base_url, '/info'),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}", "available": False}
        except Exception as e:
            return {"error": str(e), "available": False}
    
    def execute_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute a command in the Kali environment via HTTP API.
        
        Args:
            command: Command to execute
            timeout: Execution timeout in seconds
            
        Returns:
            Dict containing execution results
        """
        try:
            payload = {
                "command": command,
                "timeout": timeout,
                "environment": "kali"
            }
            
            response = self.session.post(
                urljoin(self.base_url, '/execute'),
                json=payload,
                timeout=timeout + 10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "stdout": "",
                    "stderr": response.text
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": str(e)
            }
    
    async def get_interactive_session(self) -> Optional[SSHInteractiveSession]:
        """
        Get an SSH-like interactive session to the Kali service.
        
        Note: This assumes the Kali service supports SSH on port 22.
        If only HTTP is available, this will return None.
        
        Returns:
            SSHInteractiveSession if available, None otherwise
        """
        if self._ssh_session is not None:
            return self._ssh_session
            
        try:
            # Attempt SSH connection (assuming Kali service supports SSH)
            ssh_port = int(os.getenv('KALI_SSH_PORT', '22'))
            self._ssh_session = SSHInteractiveSession(
                logger=self.logger,
                hostname=self.host,
                port=ssh_port,
                username=self.username,
                password=self.password
            )
            
            await self._ssh_session.connect()
            self.logger.info(f"SSH connection established to Kali service at {self.host}:{ssh_port}")
            return self._ssh_session
            
        except Exception as e:
            self.logger.warning(f"SSH connection to Kali service failed: {e}")
            self.logger.info("Falling back to HTTP API for command execution")
            return None
    
    def run_security_scan(self, target: str, scan_type: str = "basic") -> Dict[str, Any]:
        """
        Run a security scan using Kali tools.
        
        Args:
            target: Target to scan (IP, domain, etc.)
            scan_type: Type of scan (basic, full, stealth)
            
        Returns:
            Dict containing scan results
        """
        scan_commands = {
            "basic": f"nmap -sV -sC {target}",
            "full": f"nmap -sS -sV -sC -O -A {target}",
            "stealth": f"nmap -sS -f -T2 {target}"
        }
        
        command = scan_commands.get(scan_type, scan_commands["basic"])
        return self.execute_command(command, timeout=300)  # 5 minute timeout for scans
    
    def get_kali_tools(self) -> Dict[str, Any]:
        """
        Get list of available Kali tools.
        
        Returns:
            Dict containing available tools
        """
        command = "ls /usr/bin/ | grep -E '(nmap|nikto|sqlmap|metasploit|burp|wireshark)' | head -20"
        return self.execute_command(command)
    
    def close(self):
        """Close all connections and cleanup resources."""
        if self._ssh_session:
            try:
                self._ssh_session.close()
            except Exception as e:
                self.logger.warning(f"Error closing SSH session: {e}")
            finally:
                self._ssh_session = None
        
        if self.session:
            self.session.close()


def get_kali_service() -> Optional[KaliServiceConnector]:
    """
    Factory function to get a Kali service connector if available.
    
    Returns:
        KaliServiceConnector if service is configured and available, None otherwise
    """
    # Check if Kali service is configured
    if not os.getenv('KALI_SHELL_URL'):
        return None
    
    try:
        connector = KaliServiceConnector()
        if connector.is_available():
            return connector
        else:
            return None
    except Exception:
        return None


def is_kali_service_available() -> bool:
    """
    Quick check if Kali service is available.
    
    Returns:
        bool: True if available, False otherwise
    """
    connector = get_kali_service()
    if connector:
        result = connector.is_available()
        connector.close()
        return result
    return False