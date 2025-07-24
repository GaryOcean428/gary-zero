# Remote Session Management Documentation


## Overview

The Remote Session Management system provides unified session management for tools that require persistent connections across local and remote environments. It enables agents to perform code editing, GUI automation, and shell commands securely while maintaining session state and connection pooling.


## Architecture

### Core Components

1. **SessionInterface** - Abstract base class for all session types
2. **RemoteSessionManager** - Central orchestrator for session management
3. **ConnectionPool** - Manages connection pooling and reuse
4. **SessionConfig** - Centralized configuration management
5. **Session Implementations** - Specific implementations for each tool type

### Session Types

- **CLI** - Command-line interface sessions (Gemini CLI)
- **HTTP** - HTTP-based service sessions (Kali service)
- **GUI** - GUI automation sessions (Anthropic Computer Use)
- **TERMINAL** - Terminal and file operations (Claude Code)
- **SSH** - SSH connections (future expansion)
- **WEBSOCKET** - WebSocket connections (E2B, future)


## Configuration

The session management system is configured through environment variables. All configuration is centralized in the `SessionConfig` class.

### General Session Settings

```bash
# Maximum sessions per type
SESSION_MAX_PER_TYPE=10

# Session timeout (seconds)
SESSION_TIMEOUT=300

# Connection retry settings
SESSION_RETRY_ATTEMPTS=3
SESSION_RETRY_DELAY=5

# Health check interval (seconds)
SESSION_HEALTH_CHECK_INTERVAL=60
```

### Connection Pooling

```bash
# Enable connection pooling
SESSION_ENABLE_POOLING=true

# Pool size per session type
SESSION_POOL_SIZE=5

# Maximum idle time before cleanup (seconds)
SESSION_MAX_IDLE_TIME=300
```

### Security and Approval

```bash
# Require approval for GUI actions
SESSION_REQUIRE_GUI_APPROVAL=true

# Require approval for terminal commands
SESSION_REQUIRE_TERMINAL_APPROVAL=true

# Require approval for external services
SESSION_REQUIRE_EXTERNAL_APPROVAL=true

# Approval timeout (seconds)
SESSION_APPROVAL_TIMEOUT=30
```

### Memory and Storage

```bash
# Store outputs in agent memory
SESSION_STORE_OUTPUTS=true

# Maximum output size (bytes)
SESSION_MAX_OUTPUT_SIZE=1048576

# Output retention time (seconds)
SESSION_OUTPUT_RETENTION=3600
```


## Tool-Specific Configuration

### Google Gemini CLI

```bash
# Enable Gemini CLI integration
GEMINI_CLI_ENABLED=true

# CLI path
GEMINI_CLI_PATH=gemini

# Approval mode: auto, suggest, manual
GEMINI_CLI_APPROVAL_MODE=suggest

# Auto-install CLI if missing
GEMINI_CLI_AUTO_INSTALL=false

# API configuration
GEMINI_API_KEY=your-api-key
GEMINI_LIVE_MODEL=models/gemini-2.5-flash-preview-native-audio-dialog
GEMINI_LIVE_VOICE=Zephyr
GEMINI_LIVE_RESPONSE_MODALITIES=AUDIO
```

### Anthropic Computer Use

```bash
# Enable Anthropic Computer Use
ANTHROPIC_COMPUTER_USE_ENABLED=true

# Require approval for GUI actions
ANTHROPIC_COMPUTER_USE_REQUIRE_APPROVAL=true

# Screenshot interval (seconds)
ANTHROPIC_COMPUTER_USE_SCREENSHOT_INTERVAL=1.0

# Maximum actions per session
ANTHROPIC_COMPUTER_USE_MAX_ACTIONS=50

# API key
ANTHROPIC_API_KEY=your-api-key
```

### Claude Code Tool

```bash
# Enable Claude Code tool
CLAUDE_CODE_ENABLED=true

# Maximum file size (bytes)
CLAUDE_CODE_MAX_FILE_SIZE=1048576

# Allowed file extensions (comma-separated)
CLAUDE_CODE_ALLOWED_EXTENSIONS=.py,.js,.ts,.html,.css,.json,.md,.txt,.yml,.yaml,.toml

# Restricted paths (comma-separated)
CLAUDE_CODE_RESTRICTED_PATHS=.git,node_modules,__pycache__,.venv,venv

# Enable Git operations
CLAUDE_CODE_ENABLE_GIT=true

# Enable terminal commands
CLAUDE_CODE_ENABLE_TERMINAL=true
```

### Kali Linux Service

```bash
# Enable Kali service integration
KALI_SERVICE_ENABLED=true

# Service connection details
KALI_SHELL_URL=http://kali-linux-docker.railway.internal:8080
KALI_SHELL_HOST=kali-linux-docker.railway.internal
KALI_SHELL_PORT=8080

# Authentication
KALI_USERNAME=GaryOcean
KALI_PASSWORD=I.Am.Dev.1

# Public URL for external access
KALI_PUBLIC_URL=https://kali-linux-docker.up.railway.app

# SSH port (if SSH access is available)
KALI_SSH_PORT=22
```

### E2B Sandbox (Future)

```bash
# Enable E2B integration
E2B_ENABLED=false

# API key
E2B_API_KEY=your-e2b-api-key

# Default environment
E2B_ENVIRONMENT=Python3

# Timeout (seconds)
E2B_TIMEOUT=300
```


## Usage Examples

### Basic Session Management

```python
from framework.session.integration import create_session_manager
from framework.session import SessionType

# Create session manager
session_manager = create_session_manager(agent)
await session_manager.start()

# Create a message
message = session_manager.create_message(
    message_type="code_generation",
    payload={
        'action': 'code',
        'task': 'Create a Python web server',
        'language': 'python'
    }
)

# Execute with session
response = await session_manager.execute_with_session(
    SessionType.CLI, message
)

print(f"Response: {response.message}")
if response.success:
    print(f"Data: {response.data}")

await session_manager.stop()
```

### File Operations with Claude Code

```python
# Create file operation message
file_message = session_manager.create_message(
    message_type="file_operation",
    payload={
        'operation_type': 'file',
        'operation': 'create',
        'path': 'hello.py',
        'content': 'print("Hello, World!")'
    }
)

# Execute file operation
response = await session_manager.execute_with_session(
    SessionType.TERMINAL, file_message
)
```

### GUI Automation with Anthropic Computer Use

```python
# Take screenshot
screenshot_message = session_manager.create_message(
    message_type="gui_action",
    payload={'action': 'screenshot'}
)

screenshot_response = await session_manager.execute_with_session(
    SessionType.GUI, screenshot_message
)

# Click at coordinates
click_message = session_manager.create_message(
    message_type="gui_action",
    payload={
        'action': 'click',
        'x': 100,
        'y': 200
    }
)

click_response = await session_manager.execute_with_session(
    SessionType.GUI, click_message
)
```

### Security Scanning with Kali Service

```python
# Run port scan
scan_message = session_manager.create_message(
    message_type="security_scan",
    payload={
        'action': 'scan',
        'target': 'example.com',
        'scan_type': 'basic'
    }
)

scan_response = await session_manager.execute_with_session(
    SessionType.HTTP, scan_message
)
```


## Advanced Features

### Session Persistence

Sessions can be reused across multiple operations for better performance:

```python
# Create specific session
session = await session_manager.create_session(SessionType.CLI)

# Use session multiple times
for task in tasks:
    message = session_manager.create_message("task", task)
    response = await session_manager.execute_with_session(
        SessionType.CLI, message, session_id=session.session_id
    )

# Session will be automatically returned to pool when done
```

### Connection Pooling

The system automatically pools connections to reduce latency:

```python
# Get pool statistics
stats = await session_manager.get_manager_stats()
print(f"Active sessions: {stats['pool_stats']['total_active_sessions']}")
print(f"Pooled sessions: {stats['pool_stats']['total_pooled_sessions']}")

# Manual cleanup
await session_manager.cleanup_resources()
```

### Approval Flows

For sensitive operations, the system can require approval:

```python
# Register custom approval handler
async def custom_approval_handler(session, message):
    # Custom approval logic
    print(f"Approval needed for: {message.message_type}")
    return True  # or False to deny

session_manager.register_approval_handler(
    SessionType.GUI, custom_approval_handler
)
```


## Example Workflows

### Code Generation and Testing

```python
from examples.session_workflows import CodeGenerationWorkflow

workflow = CodeGenerationWorkflow(session_manager)
results = await workflow.run()

print(f"Workflow success: {results['success']}")
for step in results['steps']:
    print(f"Step {step['step']}: {step['description']} - {'✅' if step['success'] else '❌'}")
```

### Security Audit

```python
from examples.session_workflows import SecurityAuditWorkflow

audit = SecurityAuditWorkflow(session_manager)
results = await audit.run(target="example.com")

print(f"Audit results: {results}")
```


## Error Handling

The session management system provides comprehensive error handling:

```python
try:
    response = await session_manager.execute_with_session(
        SessionType.CLI, message
    )

    if not response.success:
        print(f"Error: {response.error}")

except Exception as e:
    print(f"Execution failed: {e}")
```


## Monitoring and Debugging

### Session Statistics

```python
stats = await session_manager.get_manager_stats()
print(json.dumps(stats, indent=2))
```

### Active Session Monitoring

```python
active_sessions = await session_manager.list_active_sessions()
for session in active_sessions:
    print(f"Session {session.session_id}: {session.state}")
```

### Health Checks

Sessions automatically perform health checks, but you can also trigger them manually:

```python
session = await session_manager.create_session(SessionType.CLI)
health = await session.health_check()
print(f"Session health: {health.success}")
```


## Railway Deployment Configuration

For Railway deployment, ensure these environment variables are preserved:

```bash
# Keep existing Railway configuration
KALI_SHELL_HOST=kali-linux-docker.railway.internal
KALI_SHELL_PORT=8080
KALI_SHELL_PASSWORD=I.Am.Dev.1
E2B_API_KEY=your-e2b-api-key
GEMINI_API_KEY=your-gemini-api-key
```


## Security Considerations

1. **Approval Requirements** - Configure approval for sensitive operations
2. **Path Restrictions** - Restrict file access to safe directories
3. **Output Size Limits** - Prevent memory exhaustion from large outputs
4. **Session Timeouts** - Automatically cleanup idle sessions
5. **Error Isolation** - Errors in one session don't affect others


## Troubleshooting

### Common Issues

1. **Session Creation Failures**
   - Check tool availability (CLI installed, service running)
   - Verify configuration and credentials
   - Check network connectivity

2. **Approval Timeouts**
   - Increase `SESSION_APPROVAL_TIMEOUT`
   - Check approval handler implementation

3. **Pool Exhaustion**
   - Increase `SESSION_POOL_SIZE`
   - Check for session leaks
   - Monitor session cleanup

4. **Memory Issues**
   - Reduce `SESSION_MAX_OUTPUT_SIZE`
   - Decrease `SESSION_OUTPUT_RETENTION`
   - Enable output cleanup

### Debugging Commands

```python
# Check configuration
config = SessionConfig.from_environment()
print(f"Pooling enabled: {config.enable_connection_pooling}")

# Monitor pool status
stats = await session_manager.get_manager_stats()
print(f"Pool stats: {stats['pool_stats']}")

# Force cleanup
await session_manager.cleanup_resources(max_idle_time=60)
```


## Performance Optimization

1. **Enable Connection Pooling** - Reuse sessions for better performance
2. **Tune Pool Sizes** - Match pool sizes to your workload
3. **Optimize Timeouts** - Balance responsiveness with resource usage
4. **Monitor Resource Usage** - Track session counts and memory usage
5. **Cleanup Strategy** - Regular cleanup of idle sessions and old outputs


## Future Enhancements

- E2B sandbox integration
- WebSocket session support
- Advanced session routing
- Load balancing across multiple services
- Session migration and failover
- Enhanced monitoring and metrics
