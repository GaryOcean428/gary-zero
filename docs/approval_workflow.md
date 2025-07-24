# Approval Workflow System Documentation


## Overview

The Gary Zero approval workflow system provides robust permissioning and approval frameworks that require explicit user confirmation for sensitive or irreversible operations. The system includes detailed audit logging, role-based access control, and flexible configuration options.


## Key Features

- **Risk-based Action Classification**: Actions are categorized by risk level (LOW, MEDIUM, HIGH, CRITICAL)
- **Role-based Access Control**: Users have roles (OWNER, ADMIN, USER, GUEST, SUBORDINATE_AGENT) with different permissions
- **Flexible Approval Policies**: ALWAYS_ASK, ASK_ONCE, NEVER_ASK, ROLE_BASED
- **Comprehensive Audit Logging**: All approval requests and decisions are logged
- **Timeout Management**: Configurable timeouts for approval requests
- **Runtime Configuration**: Policies can be updated without restart
- **Multiple Interface Support**: CLI and Web UI interfaces


## Quick Start

### Basic Setup

```python
from framework.security import (
    ApprovalWorkflow, UserRole, RiskLevel,
    set_global_approval_workflow, require_approval
)

# Create and configure workflow
workflow = ApprovalWorkflow()
workflow.set_user_role("admin_user", UserRole.ADMIN)
set_global_approval_workflow(workflow)

# Use decorator for automatic approval
@require_approval("file_write", RiskLevel.MEDIUM, "Write configuration file")
async def write_config(user_id: str, config_data: dict):
    # This function now requires approval before execution
    with open("config.json", "w") as f:
        json.dump(config_data, f)
    return "Configuration saved"

# Usage
result = await write_config("admin_user", {"setting": "value"})
```

### Manual Approval Requests

```python
# Request approval manually
approved = await workflow.request_approval(
    user_id="admin_user",
    action_type="shell_command",
    action_description="Install security updates",
    parameters={"command": "apt update && apt upgrade"},
    timeout_override=300
)

if approved:
    # Execute the action
    subprocess.run(["apt", "update"])
else:
    print("Action was not approved")
```


## High-Risk Actions

The system includes pre-configured high-risk actions:

### File Operations

- **file_write** (MEDIUM): Write or modify files
- **file_delete** (HIGH): Delete files or directories

### System Operations

- **shell_command** (HIGH): Execute shell commands
- **code_execution** (HIGH): Execute code in containers
- **config_change** (MEDIUM): Modify system configuration

### External Operations

- **external_api_call** (MEDIUM): Make external API calls
- **computer_control** (CRITICAL): Desktop/GUI automation
- **payment_transaction** (CRITICAL): Financial transactions


## Role-Based Permissions

### Role Hierarchy

1. **OWNER**: Full access to all actions
2. **ADMIN**: Access to most actions except critical ones
3. **USER**: Limited access to basic operations
4. **GUEST**: Very restricted access
5. **SUBORDINATE_AGENT**: Automated agents with minimal permissions

### Default Permissions

```python
role_permissions = {
    "owner": ["file_write", "file_delete", "shell_command", "external_api_call",
              "computer_control", "code_execution", "payment_transaction", "config_change"],
    "admin": ["file_write", "file_delete", "shell_command", "external_api_call",
              "code_execution", "config_change"],
    "user": ["file_write", "external_api_call", "config_change"],
    "guest": [],
    "subordinate_agent": []
}
```


## Approval Policies

### ALWAYS_ASK

Always requires user approval, no caching.

```python
workflow.configure_action("shell_command", approval_policy=ApprovalPolicy.ALWAYS_ASK)
```

### ASK_ONCE

Asks for approval once, then caches for 1 hour by default.

```python
workflow.configure_action("file_write", approval_policy=ApprovalPolicy.ASK_ONCE)
```

### NEVER_ASK

Auto-approves without user interaction.

```python
workflow.configure_action("config_read", approval_policy=ApprovalPolicy.NEVER_ASK)
```

### ROLE_BASED

Uses role-based rules for approval decisions.

```python
workflow.configure_action("admin_action", approval_policy=ApprovalPolicy.ROLE_BASED)
```


## Configuration Management

### Loading Configuration from File

```python
from framework.security import ApprovalConfigManager, setup_approval_workflow_from_config

# Setup from config file
workflow = setup_approval_workflow_from_config("approval_config.json")

# Or manually
config_manager = ApprovalConfigManager("approval_config.json")
workflow = ApprovalWorkflow()
config_manager.set_workflow(workflow)
config_manager.apply_config()
```

### Configuration File Format

```json
{
  "global_settings": {
    "default_timeout": 300,
    "max_pending_requests": 100,
    "cache_duration": 3600
  },
  "user_roles": {
    "admin_user": "admin",
    "regular_user": "user",
    "guest_user": "guest"
  },
  "action_policies": {
    "file_write": {
      "approval_policy": "ask_once",
      "timeout_seconds": 120,
      "required_roles": ["owner", "admin", "user"]
    },
    "shell_command": {
      "approval_policy": "always_ask",
      "timeout_seconds": 180,
      "required_roles": ["owner", "admin"]
    }
  }
}
```

### Runtime Configuration Updates

```python
# Update user role
config_manager.update_user_role("new_user", "admin")

# Update action policy
config_manager.update_action_policy("file_delete",
    approval_policy="always_ask",
    timeout_seconds=600
)

# Register custom action
config_manager.register_custom_action({
    "action_type": "custom_operation",
    "risk_level": "high",
    "description": "Custom high-risk operation",
    "required_roles": ["owner"],
    "approval_policy": "always_ask",
    "timeout_seconds": 300
})
```


## User Interfaces

### CLI Interface

```python
from framework.security.approval_interface import CLIApprovalInterface

cli_interface = CLIApprovalInterface(workflow)

# CLI commands available:
# approve <request_id> [note] - Approve a pending request
# reject <request_id> [reason] - Reject a pending request
# list - List all pending requests
# status - Show approval statistics
# help - Show help message
```

### Web UI Interface (Mock)

```python
from framework.security.approval_interface import WebUIApprovalInterface

web_interface = WebUIApprovalInterface(workflow)

# Get requests for UI display
pending_requests = web_interface.get_pending_requests_for_ui()

# Handle UI response
success = await web_interface.handle_ui_response(
    request_id="req_123",
    action="approve",
    user_id="approver",
    reason="Approved for maintenance"
)
```


## Integration with Tools

### Decorator Integration

```python
from framework.security import require_approval, RiskLevel

@require_approval("file_delete", RiskLevel.HIGH, "Delete system file")
async def delete_file(user_id: str, filepath: str):
    os.remove(filepath)
    return f"Deleted {filepath}"
```

### Manual Integration

```python
async def risky_operation(user_id: str, **kwargs):
    # Request approval first
    approved = await workflow.request_approval(
        user_id=user_id,
        action_type="custom_operation",
        action_description="Perform risky operation",
        parameters=kwargs
    )

    if not approved:
        raise PermissionError("Operation not approved")

    # Proceed with operation
    return perform_operation(**kwargs)
```

### Tool Class Integration

```python
from framework.security import make_tool_approval_aware, RiskLevel

# Make existing tool approval-aware
@make_tool_approval_aware("shell_command", RiskLevel.HIGH)
class ShellTool:
    async def execute(self, command: str, user_id: str):
        # Tool execution now requires approval
        return subprocess.run(command, shell=True)
```


## Audit Logging

All approval activities are automatically logged:

```python
# Get approval events from audit log
events = await audit_logger.get_events(
    event_type=AuditEventType.APPROVAL_REQUEST,
    start_time=time.time() - 3600  # Last hour
)

# Get security summary
summary = await audit_logger.get_security_summary(hours=24)
print(f"Approval rate: {summary.get('approval_rate', 0):.2%}")
```

### Audit Event Types

- **APPROVAL_REQUEST**: When approval is requested
- **APPROVAL_DECISION**: When approval is granted/denied
- **SECURITY_VIOLATION**: When unauthorized access is attempted


## Security Considerations

### Bypass Prevention

- All high-risk tools are wrapped with approval decorators
- Role-based permissions are enforced before approval requests
- Approval cache has configurable expiration
- Audit logs cannot be disabled for approval events

### Timeout Handling

- Requests automatically expire after timeout
- Expired requests are logged as denied
- Configurable timeouts per action type
- Global timeout limits prevent indefinite hanging

### Environment Variables

The system avoids exposing sensitive environment variables:

- `PORT`, `WEB_UI_HOST`, `SEARXNG_URL` are protected
- API keys and credentials are filtered from logs
- Parameter values are truncated in audit logs


## Statistics and Monitoring

```python
# Get approval statistics
stats = workflow.get_approval_statistics()

print(f"Total requests: {stats['total_requests']}")
print(f"Approval rate: {stats['approval_rate']:.2%}")
print(f"Average response time: {stats['average_response_time']:.1f}s")

# View requests by action type
for action, count in stats['requests_by_action_type'].items():
    print(f"{action}: {count} requests")
```


## Testing

### Unit Tests

```python
import pytest
from framework.security import ApprovalWorkflow, UserRole, RiskLevel

@pytest.mark.asyncio
async def test_approval_workflow():
    workflow = ApprovalWorkflow()
    workflow.set_user_role("test_user", UserRole.ADMIN)

    # Test auto-approval
    workflow.configure_action("test_action", approval_policy="never_ask")
    approved = await workflow.request_approval(
        user_id="test_user",
        action_type="test_action",
        action_description="Test",
        parameters={}
    )
    assert approved is True
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_decorator_integration():
    workflow = ApprovalWorkflow()
    set_global_approval_workflow(workflow)

    @require_approval("test_op", RiskLevel.LOW)
    async def test_function(user_id: str):
        return "success"

    # Configure for auto-approval
    workflow.register_action(ActionDefinition(...))

    result = await test_function("test_user")
    assert result == "success"
```


## Best Practices

### 1. Risk Level Assignment

- Use CRITICAL for irreversible system changes
- Use HIGH for potentially dangerous operations
- Use MEDIUM for operations affecting user data
- Use LOW for safe, informational operations

### 2. Role Design

- Assign minimum necessary permissions
- Use SUBORDINATE_AGENT role for automated processes
- Regularly review and update role assignments

### 3. Approval Policies

- Use ALWAYS_ASK for critical operations
- Use ASK_ONCE for frequent, medium-risk operations
- Avoid NEVER_ASK except for safe operations
- Configure appropriate timeouts based on operation urgency

### 4. Configuration Management

- Store configuration in version control
- Use environment-specific config files
- Regularly backup approval logs
- Monitor approval statistics for anomalies

### 5. User Interface

- Provide clear descriptions for approval requests
- Show relevant parameters (but sanitize sensitive data)
- Implement timeout warnings
- Log all approval decisions with reasoning


## Troubleshooting

### Common Issues

**Approval requests hang indefinitely**
- Check timeout configuration
- Verify user interface is responding to requests
- Check if user has required role permissions

**Auto-approval not working**
- Verify approval policy is set to NEVER_ASK
- Check if user role has permission for the action
- Ensure action type is registered correctly

**Configuration not loading**
- Validate JSON format of config file
- Check file permissions and path
- Review error logs for validation messages

**Audit logs missing approval events**
- Verify audit logger is properly configured
- Check if logging is enabled in global settings
- Ensure log file permissions allow writing

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger("gary_zero.audit").setLevel(logging.DEBUG)

# Get detailed workflow state
print("Action definitions:", list(workflow.action_definitions.keys()))
print("User roles:", workflow.user_roles)
print("Pending requests:", len(workflow.get_pending_requests()))
```

This documentation provides comprehensive guidance for implementing and using the approval workflow system in Gary Zero.
