# Kali Shell Access Guide


## Available Shell Service

You have access to a dedicated Kali Linux shell environment for advanced security testing and analysis:

- **Service**: `kali-linux-docker` (Railway deployment)
- **Purpose**: Advanced security testing, penetration testing, network analysis, vulnerability assessments
- **Authentication**: HTTP Basic Auth (credentials automatically configured via Railway env vars)
- **Access Methods**: Both private Railway network and public endpoints available
- **Real-time UI**: Shell operations are automatically displayed to users via dynamic iframe


## Shell Access Methods

### 1. Direct Shell Commands

Use the `shell_execute` tool when you need specialized security tools not available in standard environments:

```python
# Example: Network discovery scan
await shell_execute(
    command="nmap -sn 192.168.1.0/24",
    description="Network discovery scan to identify active hosts",
    timeout=60
)

# Example: Web vulnerability scan
await shell_execute(
    command="nikto -h https://target.com",
    description="Web application vulnerability assessment",
    timeout=180
)
```

### 2. Security Tool Integration

Access to comprehensive Kali Linux security toolkit:

**Network Analysis:**
- `nmap` - Network mapping and port scanning
- `masscan` - High-speed port scanner
- `zmap` - Internet-wide network scanner

**Web Application Testing:**
- `nikto` - Web vulnerability scanner
- `sqlmap` - SQL injection testing tool
- `dirb/gobuster` - Directory/file enumeration

**Penetration Testing:**
- `metasploit` - Exploitation framework
- `john` - Password cracking tool
- `aircrack-ng` - WiFi security auditing

**SSL/TLS Analysis:**
- `openssl` - SSL/TLS certificate analysis
- `sslyze` - SSL configuration scanner
- `testssl.sh` - SSL/TLS vulnerability testing

### 3. Interactive Shell Sessions

For multi-step operations requiring shell state persistence:

```python
# Start interactive session for complex workflows
session_id = await start_shell_session(
    session_type="interactive",
    purpose="Multi-step penetration testing workflow"
)

# Execute commands in session context
await shell_execute(
    command="cd /tmp && wget https://example.com/tool.tar.gz",
    session_id=session_id
)
```

### 4. File Operations

Transfer files between environments when needed:

```python
# Upload analysis target
await shell_file_upload(
    local_path="/tmp/target_config.txt",
    remote_path="/kali/analysis/config.txt"
)

# Download scan results
await shell_file_download(
    remote_path="/kali/results/scan_output.xml",
    local_path="/tmp/scan_results.xml"
)
```


## When to Use Shell vs E2B

**Use Kali Shell for:**
- Security analysis and vulnerability assessments
- Network penetration testing and reconnaissance
- Specialized Linux security tool requirements
- Long-running security scans (up to 10 minutes)
- SSL/TLS certificate analysis
- Web application security testing
- Password cracking and hash analysis

**Use E2B for:**
- Standard development and coding tasks
- Data analysis and processing
- Web scraping and automation
- General computational work
- Quick script execution
- File manipulation and parsing


## Security Considerations

- **Isolation**: All shell operations run in isolated Kali Linux container
- **Logging**: Shell actions are automatically logged and visible to users
- **Authentication**: Secure Railway-managed authentication (no hardcoded credentials)
- **Network**: Uses Railway private network for internal communication
- **Transparency**: Real-time iframe displays all shell operations to users
- **Timeout**: Commands have reasonable timeouts to prevent resource abuse


## User Visibility & Transparency

When you execute shell commands, users automatically see:

- **Dynamic Iframe**: Real-time terminal interface appears in the UI
- **Command Execution**: Live output and progress of security operations
- **Interactive Sessions**: Full terminal access for complex workflows
- **File Transfers**: Visual feedback on file upload/download operations
- **Session Management**: Clear indication of active shell sessions

This ensures complete transparency for all security operations and builds user trust.


## Common Usage Patterns

### Network Security Assessment

```python
# Comprehensive network scan
results = await shell_execute(
    command="nmap -sS -sV -sC -O target.com",
    description="Full TCP SYN scan with version detection",
    timeout=300
)

# Follow up with specific service scans
if "80/tcp open" in results.get('stdout', ''):
    web_scan = await shell_execute(
        command="nikto -h http://target.com",
        description="Web application vulnerability scan"
    )
```

### SSL/TLS Security Analysis

```python
# Certificate analysis
cert_info = await shell_execute(
    command="echo | openssl s_client -connect target.com:443 -servername target.com 2>/dev/null | openssl x509 -noout -text",
    description="SSL certificate detailed analysis"
)

# SSL configuration testing
ssl_test = await shell_execute(
    command="testssl.sh --quiet --color 0 target.com",
    description="Comprehensive SSL/TLS security assessment",
    timeout=120
)
```

### Web Application Security Testing

```python
# Directory enumeration
dir_scan = await shell_execute(
    command="gobuster dir -u https://target.com -w /usr/share/wordlists/dirb/common.txt",
    description="Web directory enumeration"
)

# SQL injection testing
sql_test = await shell_execute(
    command="sqlmap -u 'https://target.com/page?id=1' --batch --random-agent",
    description="Automated SQL injection testing",
    timeout=300
)
```


## Error Handling

The shell service includes robust error handling:

- **Service Unavailable**: Graceful fallback to E2B when Kali service is down
- **Command Timeout**: Automatic termination of long-running commands
- **Authentication Errors**: Clear error messages for configuration issues
- **Network Issues**: Retry logic for temporary connectivity problems


## Best Practices

1. **Purpose Documentation**: Always provide clear descriptions for shell commands
2. **Appropriate Timeouts**: Set realistic timeouts based on expected execution time
3. **User Communication**: Explain security operations to users before execution
4. **Resource Management**: Close sessions when multi-step operations complete
5. **Error Validation**: Check command results before proceeding with dependent operations

Remember: The shell service provides powerful security testing capabilities. Use responsibly and ensure all testing activities are authorized and ethical.
