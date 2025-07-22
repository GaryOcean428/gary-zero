"""
A2A Agent Card Implementation

Generates and manages the agent card for A2A protocol compliance.
The agent card provides standardized metadata about Gary-Zero's capabilities.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from framework.helpers import settings


class AgentEndpoint(BaseModel):
    """A2A endpoint definition"""
    name: str = Field(description="Endpoint name")
    path: str = Field(description="Endpoint URL path")
    method: str = Field(description="HTTP method", default="POST")
    description: str = Field(description="Endpoint description")
    protocols: List[str] = Field(description="Supported protocols", default=["json-rpc"])


class AgentCapability(BaseModel):
    """A2A capability definition"""
    name: str = Field(description="Capability name")
    description: str = Field(description="Capability description")
    version: str = Field(description="Capability version", default="1.0.0")
    enabled: bool = Field(description="Whether capability is enabled", default=True)


class AgentCard(BaseModel):
    """A2A Agent Card Model"""
    id: str = Field(description="Unique agent identifier")
    name: str = Field(description="Human-readable agent name")
    version: str = Field(description="Agent version")
    description: str = Field(description="Agent description")
    
    # Core A2A protocol fields
    capabilities: List[AgentCapability] = Field(description="Agent capabilities")
    endpoints: List[AgentEndpoint] = Field(description="Available endpoints")
    protocols: List[str] = Field(description="Supported protocols")
    
    # Metadata
    base_url: str = Field(description="Agent base URL")
    created_at: str = Field(description="Agent creation timestamp")
    updated_at: str = Field(description="Last update timestamp")
    
    # Optional fields
    vendor: Optional[str] = Field(description="Agent vendor", default="Gary-Zero Project")
    homepage: Optional[str] = Field(description="Agent homepage URL", default=None)
    documentation: Optional[str] = Field(description="Documentation URL", default=None)
    contact: Optional[Dict[str, str]] = Field(description="Contact information", default=None)
    
    # Security and trust
    trusted_agents: List[str] = Field(description="List of trusted agent IDs", default=[])
    authentication_required: bool = Field(description="Whether authentication is required", default=True)


def get_default_capabilities() -> List[AgentCapability]:
    """Get default capabilities for Gary-Zero"""
    return [
        AgentCapability(
            name="code_execution",
            description="Execute code in multiple programming languages",
            version="1.0.0"
        ),
        AgentCapability(
            name="file_management", 
            description="Create, read, update, and delete files and directories",
            version="1.0.0"
        ),
        AgentCapability(
            name="web_browsing",
            description="Browse websites and extract content",
            version="1.0.0"
        ),
        AgentCapability(
            name="search_engine",
            description="Search the internet for information",
            version="1.0.0"
        ),
        AgentCapability(
            name="mcp_client",
            description="Connect to external MCP servers as a client",
            version="1.0.0"
        ),
        AgentCapability(
            name="mcp_server", 
            description="Act as an MCP server for other agents",
            version="1.0.0"
        ),
        AgentCapability(
            name="task_scheduling",
            description="Schedule and manage tasks",
            version="1.0.0"
        ),
        AgentCapability(
            name="knowledge_management",
            description="Store and retrieve knowledge and memories",
            version="1.0.0"
        ),
        AgentCapability(
            name="multi_agent_coordination",
            description="Coordinate with subordinate agents",
            version="1.0.0"
        )
    ]


def get_default_endpoints() -> List[AgentEndpoint]:
    """Get default A2A endpoints for Gary-Zero"""
    return [
        AgentEndpoint(
            name="discover",
            path="/a2a/discover",
            method="POST",
            description="Discover agent capabilities and services"
        ),
        AgentEndpoint(
            name="negotiate",
            path="/a2a/negotiate", 
            method="POST",
            description="Negotiate protocol parameters and capabilities"
        ),
        AgentEndpoint(
            name="message",
            path="/a2a/message",
            method="POST", 
            description="Send messages to the agent"
        ),
        AgentEndpoint(
            name="stream",
            path="/a2a/stream",
            method="GET",
            description="Establish streaming WebSocket connection",
            protocols=["websocket"]
        ),
        AgentEndpoint(
            name="notify",
            path="/a2a/notify",
            method="POST",
            description="Send push notifications to the agent"
        ),
        AgentEndpoint(
            name="mcp_tools",
            path="/a2a/mcp/tools",
            method="GET", 
            description="List available MCP tools"
        ),
        AgentEndpoint(
            name="mcp_execute",
            path="/a2a/mcp/execute",
            method="POST",
            description="Execute MCP tools"
        )
    ]


def get_agent_card() -> AgentCard:
    """Generate the current agent card for Gary-Zero"""
    
    # Get configuration from settings
    a2a_config = settings.get_settings().get("a2a_config", {})
    
    # Generate or get agent ID
    agent_id = a2a_config.get("agent_id")
    if not agent_id:
        agent_id = f"gary-zero-{str(uuid.uuid4())[:8]}"
    
    # Get base URL
    base_url = a2a_config.get("base_url", "http://localhost:8000")
    
    # Get agent name
    agent_name = a2a_config.get("agent_name", "Gary-Zero")
    
    # Get enabled capabilities
    enabled_capabilities = a2a_config.get("capabilities", [])
    all_capabilities = get_default_capabilities()
    
    # Filter capabilities based on configuration
    if enabled_capabilities:
        capabilities = [cap for cap in all_capabilities if cap.name in enabled_capabilities]
    else:
        capabilities = all_capabilities
    
    # Get trusted agents
    trusted_agents = a2a_config.get("trusted_agents", [])
    
    now = datetime.utcnow().isoformat() + "Z"
    
    return AgentCard(
        id=agent_id,
        name=agent_name,
        version="1.0.0",
        description="Gary-Zero is a general-purpose AI assistant with multi-agent coordination capabilities",
        capabilities=capabilities,
        endpoints=get_default_endpoints(),
        protocols=["a2a", "mcp", "json-rpc", "websocket"],
        base_url=base_url,
        created_at=now,
        updated_at=now,
        vendor="Gary-Zero Project",
        homepage="https://github.com/GaryOcean428/gary-zero",
        documentation=f"{base_url}/docs/a2a_protocol.md",
        contact={
            "github": "https://github.com/GaryOcean428/gary-zero",
            "support": "https://github.com/GaryOcean428/gary-zero/issues"
        },
        trusted_agents=trusted_agents,
        authentication_required=a2a_config.get("authentication_required", True)
    )


def update_agent_card_config(config: Dict[str, Any]) -> None:
    """Update A2A configuration in settings"""
    current_settings = settings.get_settings()
    current_settings["a2a_config"] = {**current_settings.get("a2a_config", {}), **config}
    settings.save_settings(current_settings)