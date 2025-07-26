# OpenAI Agents SDK Integration for Gary-Zero

This document provides guidance on using the OpenAI Agents SDK integration in Gary-Zero, which adds standardized agent loops, guardrails, handoffs, and tracing capabilities.

## Overview

The OpenAI Agents SDK integration provides:

- **Standardized Agent Primitives**: Tasks, Actions, Sessions, and Agent loops
- **Guardrails System**: Input validation, output filtering, and safety evaluation
- **Tracing & Monitoring**: Enhanced logging and performance tracking
- **Agent Handoffs**: Coordinated task delegation between agents
- **Tool Compatibility**: Wrapper system for existing Gary-Zero tools
- **Backward Compatibility**: Graceful fallback to traditional Gary-Zero functionality

## Quick Start

### 1. Enable SDK Integration

The SDK integration is automatically initialized when Gary-Zero starts. You can check the status:

```python
from framework.helpers.sdk_integration import get_sdk_status

status = get_sdk_status()
print(f"SDK Status: {status['overall_status']}")
```

### 2. Create an SDK-Enhanced Agent

```python
from framework.helpers.sdk_integration import create_sdk_enabled_agent
from agent import AgentConfig, AgentContext

# Create configuration
config = AgentConfig(
    chat_model=ModelConfig("openai", "gpt-4"),
    # ... other config
)

context = AgentContext(config)

# Create SDK-enhanced agent
agent = create_sdk_enabled_agent(
    agent_config=config,
    agent_context=context,
    sdk_config={
        "name": "MyAgent",
        "model_provider": "openai",
        "model_name": "gpt-4",
        "enable_tracing": True,
        "enable_guardrails": True
    }
)
```

### 3. Migrate Existing Agent

```python
from framework.helpers.sdk_integration import migrate_existing_agent_to_sdk

# Migrate existing agent
results = migrate_existing_agent_to_sdk(
    agent=my_existing_agent,
    sdk_config={
        "enable_guardrails": True,
        "enable_tracing": True
    }
)
```

## Features

### Guardrails System

The guardrails system provides automatic safety checks:

```python
from framework.helpers.guardrails import get_guardrails_manager

manager = get_guardrails_manager()

# Enable strict mode for maximum safety
manager.enable_strict_mode()

# Check status
status = manager.get_status()
print(f"Guardrails enabled: {status['enabled']}")
```

**Input Guardrails:**
- Prompt injection detection
- Sensitive information (PII) redaction
- Length validation
- Content sanitization

**Output Guardrails:**
- Harmful content filtering
- PII detection and redaction
- Length validation
- Safety evaluation

### Tracing System

Enhanced tracing provides detailed monitoring:

```python
from framework.helpers.agent_tracing import get_agent_tracer

tracer = get_agent_tracer()

# Start tracing an operation
trace_id = tracer.start_agent_trace("MyAgent", task_id="task123")

# Add custom events
tracer.add_trace_event(
    trace_id,
    TraceEventType.TOOL_CALL,
    {"tool_name": "search", "query": "example"}
)

# End tracing
tracer.end_agent_trace(trace_id, success=True, result="Operation completed")
```

### SDK Agent Orchestration

Coordinate multiple agents with SDK primitives:

```python
from framework.helpers.agents_sdk_wrapper import get_sdk_orchestrator

orchestrator = get_sdk_orchestrator()

# Execute task with specific agent
result = await orchestrator.execute_with_agent(
    agent_id="sdk_agent_123",
    task_id="task456",
    message="Process this request"
)

# Coordinate handoff between agents
success = await orchestrator.coordinate_handoff(
    from_agent_id="agent1",
    to_agent_id="agent2",
    context={"reason": "specialized processing needed"}
)
```

## Configuration

### SDK Integration Settings

```python
# Initialize with custom settings
from framework.helpers.sdk_integration import initialize_sdk_integration

init_results = initialize_sdk_integration({
    "enable_tracing": True,
    "strict_mode": False,  # Start with permissive guardrails
    "gary_logger": logger  # Optional Gary-Zero logger
})
```

### Agent SDK Configuration

```python
from framework.helpers.agents_sdk_wrapper import SDKAgentConfig

config = SDKAgentConfig(
    name="MySpecializedAgent",
    model_provider="openai",
    model_name="gpt-4",
    instructions="Custom instructions for this agent",
    enable_tracing=True,
    enable_guardrails=True,
    max_turns=50
)
```

### Guardrails Configuration

```python
from framework.helpers.guardrails import GuardrailsManager

manager = GuardrailsManager()

# Enable/disable features
manager.enabled = True
manager.strict_mode = False  # or True for maximum safety

# Access individual validators
input_validator = manager.input_validator
output_validator = manager.output_validator
safety_evaluator = manager.safety_evaluator
```

## API Reference

### Core Classes

#### `GaryZeroSDKAgent`

Wrapper that adapts Gary-Zero agents to OpenAI Agents SDK.

**Methods:**
- `execute_task(task_id, message)` - Execute a task using SDK primitives
- `handle_handoff(to_agent, context)` - Handle agent handoff
- `get_session_data()` - Get current session information

#### `GuardrailsManager`

Central manager for safety and validation systems.

**Methods:**
- `process_input(message)` - Apply input guardrails
- `process_output(result)` - Apply output guardrails
- `evaluate_interaction(input, output)` - Safety evaluation
- `get_status()` - Get system status

#### `AgentTracer`

Enhanced tracing for agent operations.

**Methods:**
- `start_agent_trace(agent_name, task_id)` - Start tracing
- `end_agent_trace(trace_id, success, result)` - End tracing
- `add_trace_event(trace_id, event_type, data)` - Add custom event
- `get_trace_summary(trace_id)` - Get trace summary

### Utility Functions

```python
# Check SDK availability
from framework.helpers.sdk_integration import is_sdk_available, get_sdk_version

available = is_sdk_available()  # Returns True/False
version = get_sdk_version()     # Returns version string

# Test integration
from framework.helpers.sdk_integration import test_sdk_integration

results = test_sdk_integration()  # Comprehensive test results
```

## Error Handling

The SDK integration includes comprehensive error handling:

```python
from framework.helpers.guardrails import ErrorHandler

handler = ErrorHandler()

# Handle errors with appropriate strategies
error_record = await handler.handle_error(
    error=exception,
    context={"agent_id": "agent123", "task_id": "task456"}
)

# Check if retry is suggested
if error_record["retry_suggested"]:
    delay = error_record.get("retry_delay", 5)
    # Implement retry logic
```

## Monitoring and Debugging

### Check Integration Status

```python
from framework.helpers.sdk_integration import get_sdk_status

status = get_sdk_status()
print(f"Overall Status: {status['overall_status']}")

for component, details in status['components'].items():
    print(f"{component}: {details['status']}")
```

### Performance Monitoring

```python
from framework.helpers.agent_tracing import get_logging_integration

integration = get_logging_integration(logger)
metrics = integration.performance_monitor.get_metrics()

print(f"Success Rate: {metrics['error_rate']:.2%}")
print(f"Avg Duration: {metrics['average_duration_ms']:.1f}ms")
```

### Guardrails Monitoring

```python
from framework.helpers.guardrails import get_guardrails_manager

manager = get_guardrails_manager()

# Check recent violations
input_violations = manager.input_validator.get_violations()
output_violations = manager.output_validator.get_violations()

print(f"Recent input violations: {len(input_violations)}")
print(f"Recent output violations: {len(output_violations)}")
```

## Best Practices

### 1. Gradual Migration

- Start with SDK integration disabled for critical agents
- Test with non-production workloads first
- Monitor guardrails violations and adjust settings

### 2. Error Handling

- Always check if SDK features are available before using them
- Implement fallback logic for when SDK features fail
- Monitor trace and guardrail logs for issues

### 3. Performance

- Use tracing to identify bottlenecks
- Monitor guardrails impact on response times
- Adjust batch sizes for parallel agent operations

### 4. Safety

- Start with strict guardrails in production
- Regularly review safety evaluation results
- Implement custom guardrails for domain-specific risks

## Troubleshooting

### Common Issues

1. **Import Errors**

   ```python
   # Check if SDK is properly installed
   try:
       import agents
       print("✓ OpenAI Agents SDK available")
   except ImportError:
       print("✗ OpenAI Agents SDK not installed")
   ```

2. **Guardrails Not Working**

   ```python
   # Check guardrails status
   from framework.helpers.guardrails import get_guardrails_manager
   manager = get_guardrails_manager()
   print(f"Enabled: {manager.enabled}")
   ```

3. **Tracing Issues**

   ```python
   # Verify tracing initialization
   from framework.helpers.agent_tracing import get_agent_tracer
   tracer = get_agent_tracer()
   print(f"Active traces: {len(tracer.active_traces)}")
   ```

### Debug Mode

```python
# Enable verbose logging for debugging
from framework.helpers.sdk_integration import test_sdk_integration

# Run comprehensive test
results = test_sdk_integration()
print(json.dumps(results, indent=2))
```

## Migration from Legacy System

### Step 1: Enable SDK Integration

Update your agent initialization to use SDK features:

```python
# Before (legacy)
agent = Agent(0, config, context)

# After (SDK-enhanced)
agent = create_sdk_enabled_agent(config, context, sdk_config)
```

### Step 2: Update Tool Usage

Tools will automatically work with SDK wrappers, but you can optimize:

```python
# Tools are automatically wrapped and available through SDK
# No code changes needed for basic tool usage
```

### Step 3: Add Safety Checks

Implement guardrails gradually:

```python
# Start with permissive settings
manager = get_guardrails_manager()
manager.strict_mode = False  # Allow sanitized content through

# Monitor violations and adjust
violations = manager.input_validator.get_violations()
if len(violations) > threshold:
    # Adjust guardrail settings
    pass
```

## Advanced Usage

### Custom Guardrails

```python
from framework.helpers.guardrails import InputValidator

class CustomInputValidator(InputValidator):
    def __init__(self):
        super().__init__()
        # Add custom patterns
        self.banned_patterns.append(r'custom_pattern')

    async def validate_and_sanitize(self, message):
        # Custom validation logic
        message = await super().validate_and_sanitize(message)
        # Additional processing
        return message
```

### Custom Tracing Events

```python
from framework.helpers.agent_tracing import TraceEventType

# Add custom event types and processing
tracer.add_trace_event(
    trace_id,
    TraceEventType.CUSTOM,
    {
        "custom_metric": value,
        "processing_stage": "analysis",
        "confidence": 0.95
    }
)
```

## Support

For issues with the OpenAI Agents SDK integration:

1. Check the status with `get_sdk_status()`
2. Run diagnostic tests with `test_sdk_integration()`
3. Review trace logs for detailed error information
4. Check guardrails violations for safety issues

The integration is designed to gracefully degrade, so core Gary-Zero functionality will continue to work even if SDK features are unavailable.
