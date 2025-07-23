"""
Kali Code Execution Tool for Gary-Zero.

This module provides a code execution tool that leverages the Kali Linux Docker
service for secure execution of penetration testing and security analysis commands.
"""

import asyncio
import os
from typing import Any

from framework.helpers.execution_mode import should_use_kali_service
from framework.helpers.kali_service import KaliServiceConnector, get_kali_service


class KaliCodeExecutor:
    """
    Code executor that runs commands in the Kali Linux environment.
    
    This class provides a secure way to execute penetration testing tools
    and security analysis commands through the Kali Linux Docker service.
    """

    def __init__(self):
        """Initialize the Kali code executor."""
        self.connector: KaliServiceConnector | None = None
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Initialize the Kali service connection.
        
        Returns:
            bool: True if initialized successfully, False otherwise
        """
        if self._initialized:
            return True

        try:
            self.connector = get_kali_service()
            if self.connector and self.connector.is_available():
                self._initialized = True
                return True
            else:
                return False
        except Exception as e:
            print(f"Failed to initialize Kali service: {e}")
            return False

    def is_available(self) -> bool:
        """
        Check if Kali service is available for execution.
        
        Returns:
            bool: True if available, False otherwise
        """
        return self._initialized and self.connector is not None

    async def execute_command(self, command: str, timeout: int = 30) -> dict[str, Any]:
        """
        Execute a command in the Kali environment.
        
        Args:
            command: Command to execute
            timeout: Execution timeout in seconds
            
        Returns:
            Dict containing execution results
        """
        if not await self.initialize():
            return {
                "success": False,
                "error": "Kali service not available",
                "stdout": "",
                "stderr": "Kali service connection failed"
            }

        return self.connector.execute_command(command, timeout)

    async def run_nmap_scan(self, target: str, scan_type: str = "basic") -> dict[str, Any]:
        """
        Run an Nmap scan against a target.
        
        Args:
            target: Target to scan (IP, domain, etc.)
            scan_type: Scan type (basic, full, stealth, ping)
            
        Returns:
            Dict containing scan results
        """
        if not await self.initialize():
            return {"success": False, "error": "Kali service not available"}

        scan_commands = {
            "basic": f"nmap -sV -sC {target}",
            "full": f"nmap -sS -sV -sC -O -A {target}",
            "stealth": f"nmap -sS -f -T2 {target}",
            "ping": f"nmap -sn {target}",
            "port": f"nmap -p- {target}"
        }

        command = scan_commands.get(scan_type, scan_commands["basic"])
        return await self.execute_command(command, timeout=300)

    async def run_nikto_scan(self, target: str) -> dict[str, Any]:
        """
        Run a Nikto web vulnerability scan.
        
        Args:
            target: Web target to scan
            
        Returns:
            Dict containing scan results
        """
        command = f"nikto -h {target}"
        return await self.execute_command(command, timeout=180)

    async def run_sqlmap_test(self, url: str, params: str = "") -> dict[str, Any]:
        """
        Run SQLMap for SQL injection testing.
        
        Args:
            url: Target URL
            params: Additional parameters
            
        Returns:
            Dict containing test results
        """
        command = f"sqlmap -u '{url}' --batch --random-agent {params}"
        return await self.execute_command(command, timeout=300)

    async def check_ssl_certificate(self, domain: str) -> dict[str, Any]:
        """
        Check SSL certificate information.
        
        Args:
            domain: Domain to check
            
        Returns:
            Dict containing certificate info
        """
        command = f"echo | openssl s_client -connect {domain}:443 2>/dev/null | openssl x509 -noout -text"
        return await self.execute_command(command, timeout=30)

    async def get_available_tools(self) -> dict[str, Any]:
        """
        Get list of available security tools in Kali.
        
        Returns:
            Dict containing tool information
        """
        if not await self.initialize():
            return {"success": False, "error": "Kali service not available"}

        return self.connector.get_kali_tools()

    async def run_security_audit(self, target: str) -> dict[str, Any]:
        """
        Run a comprehensive security audit on a target.
        
        Args:
            target: Target to audit
            
        Returns:
            Dict containing audit results
        """
        results = {}

        # Basic port scan
        print(f"Running port scan on {target}...")
        results['port_scan'] = await self.run_nmap_scan(target, 'basic')

        # Check if web services are available
        if 'port_scan' in results and results['port_scan'].get('success'):
            stdout = results['port_scan'].get('stdout', '')
            if '80/tcp' in stdout or '443/tcp' in stdout or '8080/tcp' in stdout:
                # Web vulnerability scan
                print(f"Running web vulnerability scan on {target}...")
                results['web_scan'] = await self.run_nikto_scan(target)

        # SSL certificate check (if HTTPS is available)
        if '443/tcp' in results.get('port_scan', {}).get('stdout', ''):
            print(f"Checking SSL certificate for {target}...")
            results['ssl_check'] = await self.check_ssl_certificate(target)

        return results

    def close(self):
        """Close the Kali service connection."""
        if self.connector:
            self.connector.close()
            self.connector = None
        self._initialized = False


# Global executor instance
_kali_executor = None


def get_kali_executor() -> KaliCodeExecutor:
    """
    Get the global Kali code executor instance.
    
    Returns:
        KaliCodeExecutor: Global executor instance
    """
    global _kali_executor
    if _kali_executor is None:
        _kali_executor = KaliCodeExecutor()
    return _kali_executor


def is_kali_execution_available() -> bool:
    """
    Check if Kali execution is available and configured.
    
    Returns:
        bool: True if available, False otherwise
    """
    return should_use_kali_service() and os.getenv('KALI_SHELL_URL') is not None


async def execute_in_kali(command: str, timeout: int = 30) -> dict[str, Any]:
    """
    Execute a command in the Kali environment.
    
    Args:
        command: Command to execute
        timeout: Execution timeout in seconds
        
    Returns:
        Dict containing execution results
    """
    executor = get_kali_executor()
    return await executor.execute_command(command, timeout)


# Example usage functions
async def demo_kali_integration():
    """Demonstrate Kali service integration."""
    print("🔐 Gary-Zero Kali Service Integration Demo")
    print("=" * 50)

    if not is_kali_execution_available():
        print("❌ Kali service not available or not configured")
        print("Please ensure KALI_SHELL_URL and related environment variables are set")
        return

    executor = get_kali_executor()

    # Test basic connectivity
    print("🔗 Testing Kali service connectivity...")
    if await executor.initialize():
        print("✅ Connected to Kali service")
    else:
        print("❌ Failed to connect to Kali service")
        return

    # Get available tools
    print("\n🛠️  Getting available tools...")
    tools_result = await executor.get_available_tools()
    if tools_result.get('success'):
        print("Available security tools:")
        tools = tools_result.get('stdout', '').strip().split('\n')
        for tool in tools[:5]:  # Show first 5 tools
            if tool.strip():
                print(f"  • {tool.strip()}")

    # Test basic command
    print("\n💻 Testing basic command execution...")
    result = await executor.execute_command("whoami && pwd && uname -a")
    if result.get('success'):
        print("Command output:")
        print(result.get('stdout', ''))
    else:
        print(f"Command failed: {result.get('error', 'Unknown error')}")

    print("\n✅ Kali integration demo completed")
    executor.close()


if __name__ == "__main__":
    # Run demo if executed directly
    asyncio.run(demo_kali_integration())
