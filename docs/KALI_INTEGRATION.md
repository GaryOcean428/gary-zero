# Kali Linux Docker Service Integration

This document describes the integration between Gary-Zero and the Kali Linux Docker service deployed on Railway, enabling secure penetration testing and security analysis capabilities.

## Overview

The Kali integration allows Gary-Zero to:
- Execute security tools (nmap, nikto, sqlmap, etc.) in a controlled Kali Linux environment
- Perform penetration testing and vulnerability assessments
- Access a comprehensive suite of security analysis tools
- Maintain secure service-to-service communication within Railway's private network

## Configuration

### Railway Environment Variables

The following Railway reference variables are configured in `railway.toml`:

```toml
# Kali Shell Service Configuration (Railway inter-service communication)
KALI_SHELL_URL = "http://${{kali-linux-docker.RAILWAY_PRIVATE_DOMAIN}}:${{kali-linux-docker.PORT}}"
KALI_SHELL_HOST = "${{kali-linux-docker.RAILWAY_PRIVATE_DOMAIN}}"
KALI_SHELL_PORT = "${{kali-linux-docker.PORT}}"
KALI_USERNAME = "${{kali-linux-docker.USERNAME}}"
KALI_PASSWORD = "${{kali-linux-docker.PASSWORD}}"
KALI_PUBLIC_URL = "https://${{kali-linux-docker.RAILWAY_PUBLIC_DOMAIN}}"
```

### Development Environment

For local development, set these environment variables in your `.env` file:

```bash
# Kali Shell Service Configuration
KALI_SHELL_URL=http://kali-linux-docker.railway.internal:8080
KALI_SHELL_HOST=kali-linux-docker.railway.internal
KALI_SHELL_PORT=8080
KALI_USERNAME=GaryOcean
KALI_PASSWORD=I.Am.Dev.1
KALI_PUBLIC_URL=https://kali-linux-docker.up.railway.app

# Optional: Set execution mode to use Kali service
CODE_EXECUTION_MODE=kali
```

## Usage

### Basic Command Execution

```python
from framework.helpers.kali_executor import execute_in_kali

# Execute a command in Kali environment
result = await execute_in_kali("nmap -sV google.com")
if result['success']:
    print(result['stdout'])
else:
    print(f"Error: {result['error']}")
```

### Using the Kali Code Executor

```python
from framework.helpers.kali_executor import KaliCodeExecutor

executor = KaliCodeExecutor()

# Initialize connection
if await executor.initialize():
    # Run an Nmap scan
    scan_result = await executor.run_nmap_scan("target.com", "basic")
    
    # Run a web vulnerability scan
    web_result = await executor.run_nikto_scan("https://target.com")
    
    # Perform comprehensive security audit
    audit_result = await executor.run_security_audit("target.com")
    
    # Close connection
    executor.close()
```

### Direct Service Integration

```python
from framework.helpers.kali_service import get_kali_service

# Get Kali service connector
kali = get_kali_service()

if kali and kali.is_available():
    # Execute custom command
    result = kali.execute_command("whoami && pwd")
    
    # Get service information
    info = kali.get_service_info()
    
    # Get available tools
    tools = kali.get_kali_tools()
    
    # Close connection
    kali.close()
```

## Available Security Tools

The Kali integration provides access to common security tools:

### Network Scanning
- **Nmap**: Network discovery and port scanning
- **Masscan**: High-speed port scanner
- **Zmap**: Internet-wide network scanner

### Web Application Testing
- **Nikto**: Web vulnerability scanner
- **SQLMap**: SQL injection testing tool
- **Burp Suite**: Web application security testing
- **OWASP ZAP**: Web application security scanner

### Penetration Testing
- **Metasploit**: Penetration testing framework
- **Aircrack-ng**: Wireless security auditing
- **John the Ripper**: Password cracking tool
- **Hashcat**: Advanced password recovery

### SSL/TLS Analysis
- **OpenSSL**: SSL/TLS analysis and certificate inspection
- **SSLyze**: SSL configuration scanner
- **testssl.sh**: SSL/TLS security assessment

## API Reference

### KaliServiceConnector

Main connector class for interacting with the Kali service.

#### Methods

- `is_available() -> bool`: Check service availability
- `get_service_info() -> Dict`: Get service information
- `execute_command(command: str, timeout: int = 30) -> Dict`: Execute command
- `run_security_scan(target: str, scan_type: str = "basic") -> Dict`: Run security scan
- `get_kali_tools() -> Dict`: List available tools
- `close()`: Close connection

### KaliCodeExecutor

High-level executor for security operations.

#### Methods

- `initialize() -> bool`: Initialize service connection
- `execute_command(command: str, timeout: int = 30) -> Dict`: Execute command
- `run_nmap_scan(target: str, scan_type: str = "basic") -> Dict`: Run Nmap scan
- `run_nikto_scan(target: str) -> Dict`: Run Nikto web scan
- `run_sqlmap_test(url: str, params: str = "") -> Dict`: Run SQLMap test
- `check_ssl_certificate(domain: str) -> Dict`: Check SSL certificate
- `run_security_audit(target: str) -> Dict`: Comprehensive security audit
- `get_available_tools() -> Dict`: List available tools
- `close()`: Close connection

## Execution Modes

The Gary-Zero framework supports multiple execution modes:

1. **Direct**: Execute commands locally (default)
2. **SSH**: Execute commands via SSH connection
3. **Kali**: Execute commands in Kali Linux environment

### Setting Execution Mode

```bash
# Use Kali service for all executions
export CODE_EXECUTION_MODE=kali

# Use direct execution (default)
export CODE_EXECUTION_MODE=direct

# Use SSH execution
export CODE_EXECUTION_MODE=ssh
```

### Auto-Detection

If `CODE_EXECUTION_MODE` is not set, the system will auto-detect based on:
1. Available services (Kali, SSH)
2. Environment (Railway, Docker, local)
3. Service availability

## Security Considerations

### Network Communication
- Uses Railway's private network (`railway.internal`) for internal communication
- Authentication via username/password credentials
- HTTPS for external access when needed

### Access Control
- Service-to-service communication restricted to Railway project
- Credentials managed via Railway's environment variable system
- No hardcoded credentials in source code

### Execution Safety
- Commands executed in isolated Kali container
- Timeouts prevent runaway processes
- Error handling and logging for audit trails

## Troubleshooting

### Common Issues

1. **Service Unavailable**
   ```python
   # Check if service is configured
   from framework.helpers.kali_service import is_kali_service_available
   print(f"Kali service available: {is_kali_service_available()}")
   ```

2. **Connection Timeout**
   - Increase timeout values for long-running scans
   - Check Railway service status and logs

3. **Authentication Failed**
   - Verify KALI_USERNAME and KALI_PASSWORD environment variables
   - Ensure Railway reference variables are correctly configured

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from framework.helpers.kali_service import KaliServiceConnector
connector = KaliServiceConnector()
```

### Testing Connection

```python
from framework.helpers.execution_mode import get_execution_info
print(get_execution_info())
```

## Example Use Cases

### 1. Website Security Assessment

```python
async def assess_website(domain):
    executor = KaliCodeExecutor()
    await executor.initialize()
    
    # Comprehensive audit
    results = await executor.run_security_audit(domain)
    
    # Additional SSL check
    ssl_info = await executor.check_ssl_certificate(domain)
    
    executor.close()
    return results, ssl_info
```

### 2. Network Reconnaissance

```python
async def network_recon(target_network):
    executor = KaliCodeExecutor()
    await executor.initialize()
    
    # Host discovery
    hosts = await executor.run_nmap_scan(target_network, "ping")
    
    # Port scanning for discovered hosts
    for host in parse_discovered_hosts(hosts):
        scan = await executor.run_nmap_scan(host, "full")
        process_scan_results(scan)
    
    executor.close()
```

### 3. Custom Security Tool

```python
async def custom_security_scan(target, tools):
    kali = get_kali_service()
    
    if not kali or not kali.is_available():
        return {"error": "Kali service not available"}
    
    results = {}
    for tool, command in tools.items():
        result = kali.execute_command(command.format(target=target))
        results[tool] = result
    
    kali.close()
    return results
```

## Future Enhancements

- Interactive terminal sessions via WebSocket
- Real-time command output streaming
- Integration with vulnerability databases
- Automated report generation
- Custom tool configuration and deployment