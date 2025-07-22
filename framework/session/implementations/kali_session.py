"""
Kali Service Session Implementation.

Provides session management for Kali Linux Docker service interactions.
"""

import asyncio
import uuid
from typing import Any, Dict, Optional
import requests
from urllib.parse import urljoin

from ..session_interface import SessionInterface, SessionType, SessionState, SessionMessage, SessionResponse


class KaliSession(SessionInterface):
    """Session implementation for Kali Linux Docker service."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Kali service session.
        
        Args:
            config: Configuration dictionary with Kali service settings
        """
        session_id = str(uuid.uuid4())
        super().__init__(session_id, SessionType.HTTP, config)
        
        self.base_url = config.get('base_url', 'http://kali-linux-docker.railway.internal:8080')
        self.username = config.get('username', 'GaryOcean')
        self.password = config.get('password', 'I.Am.Dev.1')
        
        # HTTP session for persistent connections
        self.http_session = requests.Session()
        self.http_session.auth = (self.username, self.password)
        self.http_session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Gary-Zero-Agent/1.0'
        })
        
        # State tracking
        self._connected = False
    
    async def connect(self) -> SessionResponse:
        """
        Establish connection to Kali service.
        
        Returns:
            SessionResponse indicating connection success or failure
        """
        try:
            await self.update_state(SessionState.INITIALIZING)
            
            # Test connection with health check
            response = self.http_session.get(
                urljoin(self.base_url, '/health'),
                timeout=10
            )
            
            if response.status_code == 200:
                self._connected = True
                await self.update_state(SessionState.CONNECTED)
                
                # Get service info
                try:
                    info_response = self.http_session.get(
                        urljoin(self.base_url, '/info'),
                        timeout=5
                    )
                    service_info = info_response.json() if info_response.status_code == 200 else {}
                except Exception:
                    service_info = {}
                
                return SessionResponse(
                    success=True,
                    message="Connected to Kali service",
                    data={'service_info': service_info},
                    session_id=self.session_id
                )
            else:
                await self.update_state(SessionState.ERROR, f"HTTP {response.status_code}")
                return SessionResponse(
                    success=False,
                    message=f"Connection failed: HTTP {response.status_code}",
                    error=response.text,
                    session_id=self.session_id
                )
                
        except Exception as e:
            await self.update_state(SessionState.ERROR, str(e))
            return SessionResponse(
                success=False,
                message=f"Connection failed: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )
    
    async def disconnect(self) -> SessionResponse:
        """
        Disconnect from Kali service.
        
        Returns:
            SessionResponse indicating disconnection status
        """
        try:
            self.http_session.close()
            self._connected = False
            await self.update_state(SessionState.DISCONNECTED)
            
            return SessionResponse(
                success=True,
                message="Disconnected from Kali service",
                session_id=self.session_id
            )
        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Disconnection error: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )
    
    async def execute(self, message: SessionMessage) -> SessionResponse:
        """
        Execute a command in the Kali environment.
        
        Args:
            message: Message containing the command to execute
            
        Returns:
            SessionResponse with command results
        """
        try:
            if not self._connected:
                return SessionResponse(
                    success=False,
                    message="Kali service not connected",
                    error="Service not connected",
                    session_id=self.session_id
                )
            
            await self.update_state(SessionState.ACTIVE)
            
            action = message.payload.get('action', 'execute')
            
            if action == 'execute':
                return await self._execute_command(message.payload)
            elif action == 'scan':
                return await self._run_scan(message.payload)
            elif action == 'tools':
                return await self._get_tools()
            elif action == 'audit':
                return await self._run_audit(message.payload)
            else:
                return SessionResponse(
                    success=False,
                    message=f"Unknown action: {action}",
                    error=f"Unsupported action: {action}",
                    session_id=self.session_id
                )
            
        except Exception as e:
            await self.update_state(SessionState.ERROR, str(e))
            return SessionResponse(
                success=False,
                message=f"Execution failed: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )
        finally:
            await self.update_state(SessionState.IDLE)
    
    async def health_check(self) -> SessionResponse:
        """
        Check if the Kali service session is healthy.
        
        Returns:
            SessionResponse indicating session health
        """
        try:
            if not self._connected:
                return SessionResponse(
                    success=False,
                    message="Service not connected",
                    session_id=self.session_id
                )
            
            response = self.http_session.get(
                urljoin(self.base_url, '/health'),
                timeout=5
            )
            
            if response.status_code == 200:
                return SessionResponse(
                    success=True,
                    message="Session healthy",
                    session_id=self.session_id
                )
            else:
                return SessionResponse(
                    success=False,
                    message=f"Health check failed: HTTP {response.status_code}",
                    error=response.text,
                    session_id=self.session_id
                )
                
        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Health check failed: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )
    
    async def _execute_command(self, payload: Dict[str, Any]) -> SessionResponse:
        """Execute a command in the Kali environment."""
        command = payload.get('command', '')
        timeout = payload.get('timeout', 30)
        
        if not command:
            return SessionResponse(
                success=False,
                message="No command provided",
                error="Missing command parameter",
                session_id=self.session_id
            )
        
        try:
            request_payload = {
                'command': command,
                'timeout': timeout,
                'environment': 'kali'
            }
            
            response = self.http_session.post(
                urljoin(self.base_url, '/execute'),
                json=request_payload,
                timeout=timeout + 10
            )
            
            if response.status_code == 200:
                result = response.json()
                return SessionResponse(
                    success=result.get('success', False),
                    message="Command executed",
                    data=result,
                    session_id=self.session_id
                )
            else:
                return SessionResponse(
                    success=False,
                    message=f"Command execution failed: HTTP {response.status_code}",
                    error=response.text,
                    session_id=self.session_id
                )
                
        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Command execution error: {str(e)}",
                error=str(e),
                session_id=self.session_id
            )
    
    async def _run_scan(self, payload: Dict[str, Any]) -> SessionResponse:
        """Run a security scan using Kali tools."""
        target = payload.get('target', '')
        scan_type = payload.get('scan_type', 'basic')
        
        if not target:
            return SessionResponse(
                success=False,
                message="No target provided for scan",
                error="Missing target parameter",
                session_id=self.session_id
            )
        
        # Define scan commands
        scan_commands = {
            'basic': f'nmap -sV -sC {target}',
            'full': f'nmap -sS -sV -sC -O -A {target}',
            'stealth': f'nmap -sS -f -T2 {target}',
            'ping': f'nmap -sn {target}',
            'port': f'nmap -p- {target}'
        }
        
        command = scan_commands.get(scan_type, scan_commands['basic'])
        
        return await self._execute_command({
            'command': command,
            'timeout': 300  # 5 minute timeout for scans
        })
    
    async def _get_tools(self) -> SessionResponse:
        """Get list of available Kali tools."""
        command = "ls /usr/bin/ | grep -E '(nmap|nikto|sqlmap|metasploit|burp|wireshark)' | head -20"
        
        return await self._execute_command({
            'command': command,
            'timeout': 10
        })
    
    async def _run_audit(self, payload: Dict[str, Any]) -> SessionResponse:
        """Run a comprehensive security audit."""
        target = payload.get('target', '')
        
        if not target:
            return SessionResponse(
                success=False,
                message="No target provided for audit",
                error="Missing target parameter",
                session_id=self.session_id
            )
        
        # Run multiple scan types and combine results
        results = {}
        
        # Basic port scan
        port_scan = await self._run_scan({'target': target, 'scan_type': 'basic'})
        results['port_scan'] = port_scan.data if port_scan.success else {'error': port_scan.error}
        
        # Check if web services are available for additional scans
        if port_scan.success and port_scan.data:
            stdout = port_scan.data.get('stdout', '')
            if any(port in stdout for port in ['80/tcp', '443/tcp', '8080/tcp']):
                # Web vulnerability scan
                nikto_result = await self._execute_command({
                    'command': f'nikto -h {target}',
                    'timeout': 180
                })
                results['web_scan'] = nikto_result.data if nikto_result.success else {'error': nikto_result.error}
            
            # SSL certificate check if HTTPS is available
            if '443/tcp' in stdout:
                ssl_result = await self._execute_command({
                    'command': f'echo | openssl s_client -connect {target}:443 2>/dev/null | openssl x509 -noout -text',
                    'timeout': 30
                })
                results['ssl_check'] = ssl_result.data if ssl_result.success else {'error': ssl_result.error}
        
        return SessionResponse(
            success=True,
            message="Security audit completed",
            data={'audit_results': results},
            session_id=self.session_id
        )