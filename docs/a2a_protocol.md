# Agent2Agent (A2A) Protocol Implementation

## Overview

The Agent2Agent (A2A) protocol enables standardized communication between AI agents across different vendors and platforms. This document outlines Gary-Zero's implementation of A2A protocol compliance.

## A2A Protocol Components

### 1. Agent Card (/.well-known/agent.json)

The agent card is a standardized metadata endpoint that exposes agent capabilities, endpoints, and discovery information.

**Required Fields:**
- `id`: Unique agent identifier
- `name`: Human-readable agent name  
- `version`: Agent version
- `capabilities`: Array of supported capabilities
- `endpoints`: Available API endpoints
- `protocols`: Supported protocols (A2A, MCP, etc.)
- `metadata`: Additional agent information

### 2. JSON-RPC Endpoints

A2A requires the following JSON-RPC endpoints for agent interoperability:

#### Discovery Endpoint (`/a2a/discover`)
- Allows other agents to discover this agent's capabilities
- Returns agent card information and available services

#### Negotiation Endpoint (`/a2a/negotiate`) 
- Handles protocol negotiation between agents
- Establishes communication parameters and capabilities

#### Communication Endpoint (`/a2a/message`)
- Handles agent-to-agent message exchange
- Supports both synchronous and asynchronous communication

#### Streaming Endpoint (`/a2a/stream`)
- Provides real-time streaming communication
- WebSocket-based for persistent connections

#### Push Notifications (`/a2a/notify`)
- Handles push notifications between agents
- Supports event-driven communication patterns

### 3. Integration with MCP

A2A protocol integrates with Gary-Zero's existing MCP implementation:

- MCP servers can be discovered and registered via A2A
- A2A agents can expose MCP tools to other agents
- Cross-protocol communication is supported

## Implementation Architecture

```
├── framework/
│   ├── a2a/
│   │   ├── __init__.py
│   │   ├── agent_card.py       # Agent card generation
│   │   ├── discovery.py        # Discovery service
│   │   ├── negotiation.py      # Protocol negotiation
│   │   ├── communication.py    # Message handling
│   │   └── streaming.py        # WebSocket streaming
│   ├── api/
│   │   ├── a2a_agent_card.py   # /.well-known/agent.json endpoint
│   │   ├── a2a_discover.py     # Discovery endpoint
│   │   ├── a2a_negotiate.py    # Negotiation endpoint
│   │   ├── a2a_message.py      # Communication endpoint
│   │   └── a2a_stream.py       # Streaming endpoint
│   └── helpers/
│       └── a2a_handler.py      # A2A protocol handler
├── webui/
│   └── components/
│       └── settings/
│           └── a2a/            # A2A configuration UI
└── docs/
    └── a2a_setup.md           # Setup documentation
```

## Configuration

A2A agents are configured through Gary-Zero's settings system:

```json
{
  "a2a_config": {
    "enabled": true,
    "agent_id": "gary-zero-instance-001",
    "agent_name": "Gary-Zero",
    "base_url": "http://localhost:8000",
    "capabilities": [
      "code_execution",
      "file_management", 
      "web_browsing",
      "mcp_client",
      "mcp_server"
    ],
    "trusted_agents": [
      "agent-id-1",
      "agent-id-2"
    ]
  }
}
```

## Security Considerations

- Agent authentication via API keys or OAuth
- Trusted agent allowlists
- Rate limiting and request validation
- Secure communication channels (HTTPS/WSS)
- Input sanitization and validation

## Interoperability Testing

To demonstrate A2A compliance, Gary-Zero will:

1. Expose its agent card at `/.well-known/agent.json`
2. Implement all required JSON-RPC endpoints
3. Successfully communicate with external A2A-compliant agents
4. Show bidirectional tool/capability sharing
5. Maintain security and isolation between agents