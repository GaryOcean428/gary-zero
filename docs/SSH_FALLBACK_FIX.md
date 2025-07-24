# SSH Connection Failure Fix

This document describes the fix for SSH connection failures in Gary-Zero deployments.


## Problem

Gary-Zero was failing with `NoValidConnectionsError` when trying to connect to SSH on port 55022, particularly in Railway deployments where no SSH server is available.

```
NoValidConnectionsError: [Errno None] Unable to connect to port 55022 on 127.0.0.1 or ::1
```


## Root Cause

The default configuration enabled SSH execution (`code_exec_ssh_enabled: bool = True`) but no SSH server was running on the expected port 55022, causing the application to crash during code execution tool initialization.


## Solution

Implemented a graceful fallback mechanism that:

1. **Detects Environment**: Automatically detects Railway, Docker, or local environments
2. **Attempts SSH First**: When configured, tries SSH connection as before
3. **Falls Back Gracefully**: If SSH fails, automatically falls back to local execution
4. **Provides Configuration**: Allows explicit control via environment variables


## Configuration

### Environment Variables

- `CODE_EXECUTION_MODE=direct|ssh` - Explicitly set execution mode
- `DISABLE_SSH_EXECUTION=true` - Disable SSH execution entirely
- `RAILWAY_ENVIRONMENT` - Auto-detected in Railway deployments

### Railway Deployment

Railway deployments automatically use direct execution mode:

```toml
# railway.toml
[services.variables]
CODE_EXECUTION_MODE = "direct"
DISABLE_SSH_EXECUTION = "true"
```

### Local Development

Local development environments check SSH availability and fall back automatically:

```bash
# Enable SSH execution (if SSH server is available)
export CODE_EXECUTION_MODE=ssh

# Force direct execution
export CODE_EXECUTION_MODE=direct
export DISABLE_SSH_EXECUTION=true
```


## Implementation Details

### New Files

- `framework/helpers/execution_mode.py` - Environment detection and configuration utilities

### Modified Files

- `framework/tools/code_execution_tool.py` - Added fallback logic in `prepare_state()` and `terminal_session()`
- `railway.toml` - Added direct execution environment variables
- `.env.example` - Documented new configuration options

### Key Functions

```python
# Environment detection
detect_execution_environment() -> str
is_ssh_available(host, port) -> bool
should_use_ssh_execution() -> bool
get_execution_config() -> Dict[str, Any]

# Fallback logic in CodeExecution.prepare_state()
if use_ssh:
    try:
        # Attempt SSH connection
        shell = SSHInteractiveSession(...)
        await shell.connect()
    except Exception as ssh_error:
        # Fall back to local execution
        shell = LocalInteractiveSession()
```


## Testing

The fix includes comprehensive tests:

- `test_ssh_fallback.py` - Tests environment detection and fallback logic
- `test_ssh_issue_fix.py` - Simulates the original failure scenario


## Backward Compatibility

- ✅ Existing SSH functionality is preserved when SSH is available
- ✅ No configuration changes required for working SSH setups
- ✅ Secure execution framework integration maintained
- ✅ Docker container execution continues to work


## Verification

The fix ensures:

1. **No More Crashes**: `NoValidConnectionsError` is caught and handled gracefully
2. **Railway Compatibility**: Automatic detection and configuration for Railway deployments
3. **Flexibility**: Environment variables allow override of default behavior
4. **Clear Logging**: Users can see when fallback occurs and why


## Example Output

```
🔗 Attempting SSH connection: SSH execution on 127.0.0.1:55022 ❌ (environment: local)
❌ SSH connection failed: [Errno None] Unable to connect to port 55022 on 127.0.0.1
🔄 Falling back to local execution
🖥️  Using direct execution: Direct execution (environment: local)
```

This fix resolves issue #136 and ensures Gary-Zero works reliably across all deployment environments.
