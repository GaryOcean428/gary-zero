# Gary-Zero: Agent2Agent (A2A) Protocol Setup Guide

This guide explains how to configure and use the Agent2Agent (A2A) protocol implementation in Gary-Zero for multi-agent interoperability.


## What is A2A Protocol?

The Agent2Agent (A2A) protocol enables standardized communication between AI agents across different vendors and platforms. Gary-Zero's A2A implementation allows it to:

- **Discover other agents** and their capabilities
- **Negotiate protocol parameters** for secure communication
- **Exchange messages** with external agents
- **Share MCP tools** and resources
- **Receive push notifications** from other agents
- **Stream real-time data** via WebSocket connections


## A2A Protocol Components

### 1. Agent Card (`/.well-known/agent.json`)

Gary-Zero exposes its capabilities and endpoints through a standardized agent card:

```json
{
  "id": "gary-zero-abc123",
  "name": "Gary-Zero",
  "version": "1.0.0",
  "description": "General-purpose AI assistant with multi-agent coordination",
  "capabilities": [
    {"name": "code_execution", "description": "Execute code in multiple languages"},
    {"name": "file_management", "description": "Create, read, update, delete files"},
    {"name": "web_browsing", "description": "Browse websites and extract content"},
    // ... more capabilities
  ],
  "endpoints": [
    {"name": "discover", "path": "/a2a/discover", "method": "POST"},
    {"name": "negotiate", "path": "/a2a/negotiate", "method": "POST"},
    // ... more endpoints
  ],
  "protocols": ["a2a", "mcp", "json-rpc", "websocket"],
  "base_url": "http://localhost:8000"
}
```

### 2. Core A2A Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/.well-known/agent.json` | GET | Agent card discovery |
| `/a2a/discover` | POST | Capability discovery |
| `/a2a/negotiate` | POST | Protocol negotiation |
| `/a2a/message` | POST | Agent-to-agent messaging |
| `/a2a/notify` | POST | Push notifications |
| `/a2a/stream` | WebSocket | Real-time streaming |
| `/a2a/mcp/tools` | GET | MCP tools discovery |
| `/a2a/mcp/execute` | POST | MCP tool execution |


## Configuration

### Method 1: Web UI Configuration

1. Navigate to the A2A configuration page in Gary-Zero's web interface
2. Configure your agent settings:
   - **Agent Name**: Display name for your agent
   - **Base URL**: Public URL where your agent is accessible
   - **Capabilities**: Select which capabilities to expose
   - **Security**: Configure authentication and trusted agents

### Method 2: Settings File Configuration

Add A2A configuration to your `tmp/settings.json`:

```json
{
  "a2a_config": {
    "enabled": true,
    "agent_id": "gary-zero-unique-id",
    "agent_name": "My Gary-Zero Instance",
    "base_url": "https://my-agent.example.com",
    "capabilities": [
      "code_execution",
      "file_management",
      "web_browsing",
      "mcp_client",
      "mcp_server"
    ],
    "authentication_required": true,
    "trusted_agents": [
      "trusted-agent-id-1",
      "trusted-agent-id-2"
    ]
  }
}
```


## Usage Examples

### 1. Discovering Gary-Zero from Another Agent

```bash
# Get agent card
curl https://your-gary-zero.com/.well-known/agent.json

# Discover specific capabilities
curl -X POST https://your-gary-zero.com/a2a/discover \
  -H "Content-Type: application/json" \
  -d '{
    "requester_id": "my-agent-123",
    "capabilities_filter": ["code_execution", "web_browsing"]
  }'
```

### 2. Protocol Negotiation

```bash
curl -X POST https://your-gary-zero.com/a2a/negotiate \
  -H "Content-Type: application/json" \
  -d '{
    "requester_id": "my-agent-123",
    "session_id": "session-abc-456",
    "preferred_protocols": [
      {"name": "a2a", "version": "1.0.0", "features": ["discovery", "messaging"]},
      {"name": "json-rpc", "version": "2.0", "features": ["method_calls"]}
    ],
    "required_capabilities": ["code_execution"],
    "optional_capabilities": ["web_browsing"]
  }'
```

### 3. Sending Messages

```bash
curl -X POST https://your-gary-zero.com/a2a/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "id": "msg-123",
      "session_id": "session-abc-456",
      "sender_id": "my-agent-123",
      "recipient_id": "gary-zero-unique-id",
      "type": "request",
      "content": {
        "request_type": "execute_task",
        "task": {
          "description": "Create a Python script that prints Hello World",
          "type": "code_generation"
        }
      },
      "timestamp": "2025-01-01T00:00:00Z"
    },
    "session_token": "your-session-token"
  }'
```

### 4. MCP Tools Discovery

```bash
# List available MCP tools
curl https://your-gary-zero.com/a2a/mcp/tools

# Execute an MCP tool
curl -X POST https://your-gary-zero.com/a2a/mcp/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "code_execution",
    "server_name": "gary-zero-internal",
    "requester_id": "my-agent-123",
    "arguments": {
      "language": "python",
      "code": "print('Hello from A2A!')"
    }
  }'
```

### 5. WebSocket Streaming

```javascript
// Connect to A2A streaming endpoint
const ws = new WebSocket('wss://your-gary-zero.com/a2a/stream?agent_id=my-agent&session_id=session-123');

ws.onopen = function() {
    // Send heartbeat
    ws.send(JSON.stringify({
        type: 'heartbeat',
        data: { ping: Date.now() }
    }));
};

ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    console.log('Received A2A message:', message);
};
```


## Testing A2A Implementation

### Built-in Interoperability Test

Gary-Zero includes a comprehensive test script to validate A2A compliance:

```bash
cd /path/to/gary-zero
python test_a2a_interoperability.py
```

This test verifies:
- ✅ Agent card discovery
- ✅ Capability discovery
- ✅ Protocol negotiation
- ✅ MCP tools discovery
- ✅ Push notifications

### Manual Testing

1. **Start Gary-Zero**: `python main.py`
2. **Test agent card**: `curl http://localhost:8000/.well-known/agent.json`
3. **Test discovery**: Use the web UI's "Test A2A Interoperability" button
4. **Check endpoints**: Visit `http://localhost:8000/docs` for API documentation


## Security Considerations

### Authentication

- **Session Tokens**: A2A negotiation provides session tokens for authenticated communication
- **API Keys**: Standard Gary-Zero API key authentication is supported
- **Trusted Agents**: Configure allowlist of trusted agent IDs

### Best Practices

1. **Use HTTPS**: Always use secure connections in production
2. **Validate Inputs**: All A2A messages are validated against JSON schemas
3. **Rate Limiting**: Implement rate limiting for A2A endpoints
4. **Audit Logging**: Monitor A2A communication for security events


## Integration with MCP

Gary-Zero's A2A implementation seamlessly integrates with its MCP capabilities:

- **MCP Server Mode**: Gary-Zero can expose its tools to other agents via A2A
- **MCP Client Mode**: Gary-Zero can discover and use tools from other MCP servers
- **Cross-Protocol**: A2A agents can discover and execute MCP tools


## Troubleshooting

### Common Issues

1. **Agent card not accessible**
   - Check if Gary-Zero is running on the configured port
   - Verify firewall settings and network accessibility
   - Ensure the base URL in configuration matches your setup

2. **Capability discovery fails**
   - Verify the requester_id is provided in discovery requests
   - Check that requested capabilities are enabled in configuration

3. **Protocol negotiation rejected**
   - Ensure compatible protocols are requested (a2a, json-rpc, etc.)
   - Verify required capabilities are available and enabled

4. **WebSocket streaming issues**
   - Check WebSocket URL format and parameters
   - Verify session_id and agent_id are valid
   - Test with a simple WebSocket client first

### Debug Mode

Enable debug logging to troubleshoot A2A issues:

```python
import logging
logging.getLogger('framework.a2a').setLevel(logging.DEBUG)
```


## Advanced Configuration

### Custom Capabilities

You can define custom capabilities in the agent card:

```python
from framework.a2a.agent_card import AgentCapability, update_agent_card_config

custom_capability = AgentCapability(
    name="custom_analysis",
    description="Perform custom data analysis",
    version="1.0.0",
    enabled=True
)

# Add to configuration
config = {
    "capabilities": ["custom_analysis"]
}
update_agent_card_config(config)
```

### Custom Endpoints

Extend the A2A API with custom endpoints by adding them to the FastAPI app:

```python
from fastapi import FastAPI

@app.post("/a2a/custom-endpoint")
async def custom_a2a_endpoint(request_data: dict):
    # Your custom A2A logic here
    return {"success": True, "message": "Custom endpoint works!"}
```


## Production Deployment

### Environment Variables

```bash
# Required
export A2A_ENABLED=true
export A2A_AGENT_ID=your-unique-agent-id
export A2A_BASE_URL=https://your-domain.com

# Optional
export A2A_AGENT_NAME="Production Gary-Zero"
export A2A_AUTH_REQUIRED=true
```

### Load Balancing

When deploying behind a load balancer:

1. Ensure sticky sessions for WebSocket connections
2. Configure health checks for A2A endpoints
3. Use consistent agent IDs across instances

### Monitoring

Monitor A2A endpoints with standard web monitoring tools:

- **Health checks**: `/health` endpoint includes A2A status
- **Metrics**: Track request counts and response times for A2A endpoints
- **Logging**: Monitor A2A communication patterns and errors


## Contributing

To contribute to A2A protocol development:

1. Review the A2A specification in `docs/a2a_protocol.md`
2. Add tests for new features in the test suite
3. Update documentation for any API changes
4. Ensure backward compatibility with existing A2A agents


## Resources

- **A2A Protocol Documentation**: `docs/a2a_protocol.md`
- **API Documentation**: `http://your-gary-zero.com/docs`
- **Test Suite**: `test_a2a_interoperability.py`
- **Configuration UI**: `/components/settings/a2a/a2a-config.html`
- **GitHub Issues**: Report A2A-related issues on the Gary-Zero repository

This implementation demonstrates full A2A protocol compliance and enables Gary-Zero to participate in multi-agent ecosystems with standardized communication protocols.
