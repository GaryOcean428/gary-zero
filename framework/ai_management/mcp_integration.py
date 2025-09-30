"""
Model Context Protocol (MCP) Integration for Gary-Zero
Integrated from AI-Manus project for enhanced tool and context management
"""

from typing import Optional, Dict, List, Any, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import asyncio
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MCPTransport(str, Enum):
    """MCP transport types"""
    STDIO = "stdio"
    SSE = "sse"
    STREAMABLE_HTTP = "streamable-http"


class MCPServerConfig(BaseModel):
    """
    MCP server configuration model
    Adapted from AI-Manus for Gary-Zero integration
    """
    # For stdio transport
    command: Optional[str] = None
    args: Optional[List[str]] = None
    
    # For HTTP-based transports
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    
    # Common fields
    transport: MCPTransport
    enabled: bool = Field(default=True)
    description: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    name: str = Field(..., description="Unique server name")
    
    @field_validator("url")
    def validate_url_for_http_transport(cls, v: Optional[str], values) -> Optional[str]:
        """Validate URL is required for HTTP-based transports"""
        if hasattr(values, 'data'):
            transport = values.data.get('transport')
            if transport in [MCPTransport.SSE, MCPTransport.STREAMABLE_HTTP] and not v:
                raise ValueError("URL is required for HTTP-based transports")
        return v
    
    @field_validator("command")
    def validate_command_for_stdio(cls, v: Optional[str], values) -> Optional[str]:
        """Validate command is required for stdio transport"""
        if hasattr(values, 'data'):
            transport = values.data.get('transport')
            if transport == MCPTransport.STDIO and not v:
                raise ValueError("Command is required for stdio transport")
        return v
    
    class Config:
        extra = "allow"


class MCPCapability(BaseModel):
    """MCP server capability definition"""
    name: str
    description: Optional[str] = None
    schema: Optional[Dict[str, Any]] = None
    experimental: bool = False


class MCPServerInfo(BaseModel):
    """MCP server information"""
    name: str
    version: str
    capabilities: List[MCPCapability] = []
    protocol_version: str = "2024-11-05"


class MCPMessage(BaseModel):
    """Base MCP message structure"""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class MCPTool(BaseModel):
    """MCP tool definition"""
    name: str
    description: str
    input_schema: Dict[str, Any]


class MCPResource(BaseModel):
    """MCP resource definition"""
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None


class MCPPrompt(BaseModel):
    """MCP prompt template definition"""
    name: str
    description: Optional[str] = None
    arguments: Optional[List[Dict[str, Any]]] = None


class MCPIntegrationManager:
    """
    Manages MCP server connections and interactions
    Integrated from AI-Manus for Gary-Zero
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self.servers: Dict[str, MCPServerConfig] = {}
        self.active_connections: Dict[str, Any] = {}
        self.config_path = config_path or Path("mcp.json")
        self.logger = logging.getLogger(__name__)
        
    async def load_config(self) -> None:
        """Load MCP server configurations from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                    
                for server_name, server_config in config_data.get("mcpServers", {}).items():
                    try:
                        server_config["name"] = server_name
                        self.servers[server_name] = MCPServerConfig(**server_config)
                    except Exception as e:
                        self.logger.error(f"Failed to load MCP server config for {server_name}: {e}")
                        
            self.logger.info(f"Loaded {len(self.servers)} MCP server configurations")
        except Exception as e:
            self.logger.error(f"Failed to load MCP config: {e}")
    
    async def save_config(self) -> None:
        """Save MCP server configurations to file"""
        try:
            config_data = {
                "mcpServers": {
                    name: server.model_dump(exclude_none=True) 
                    for name, server in self.servers.items()
                }
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
                
            self.logger.info(f"Saved {len(self.servers)} MCP server configurations")
        except Exception as e:
            self.logger.error(f"Failed to save MCP config: {e}")
    
    def add_server(self, server_config: MCPServerConfig) -> None:
        """Add a new MCP server configuration"""
        self.servers[server_config.name] = server_config
        self.logger.info(f"Added MCP server: {server_config.name}")
    
    def remove_server(self, server_name: str) -> bool:
        """Remove an MCP server configuration"""
        if server_name in self.servers:
            del self.servers[server_name]
            if server_name in self.active_connections:
                # Close connection if active
                del self.active_connections[server_name]
            self.logger.info(f"Removed MCP server: {server_name}")
            return True
        return False
    
    async def connect_server(self, server_name: str) -> bool:
        """Connect to an MCP server"""
        if server_name not in self.servers:
            self.logger.error(f"Server {server_name} not configured")
            return False
            
        server_config = self.servers[server_name]
        if not server_config.enabled:
            self.logger.info(f"Server {server_name} is disabled")
            return False
            
        try:
            # For now, just mark as connected - actual implementation would depend on transport
            self.active_connections[server_name] = {
                "config": server_config,
                "connected": True,
                "tools": [],
                "resources": [],
                "prompts": []
            }
            
            self.logger.info(f"Connected to MCP server: {server_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MCP server {server_name}: {e}")
            return False
    
    async def disconnect_server(self, server_name: str) -> None:
        """Disconnect from an MCP server"""
        if server_name in self.active_connections:
            del self.active_connections[server_name]
            self.logger.info(f"Disconnected from MCP server: {server_name}")
    
    async def list_tools(self, server_name: Optional[str] = None) -> List[MCPTool]:
        """List available tools from MCP servers"""
        tools = []
        
        if server_name:
            if server_name in self.active_connections:
                connection = self.active_connections[server_name]
                tools.extend(connection.get("tools", []))
        else:
            for connection in self.active_connections.values():
                tools.extend(connection.get("tools", []))
                
        return tools
    
    async def list_resources(self, server_name: Optional[str] = None) -> List[MCPResource]:
        """List available resources from MCP servers"""
        resources = []
        
        if server_name:
            if server_name in self.active_connections:
                connection = self.active_connections[server_name]
                resources.extend(connection.get("resources", []))
        else:
            for connection in self.active_connections.values():
                resources.extend(connection.get("resources", []))
                
        return resources
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any], 
                       server_name: Optional[str] = None) -> Any:
        """Call an MCP tool"""
        # Find the tool in connected servers
        target_server = None
        
        if server_name and server_name in self.active_connections:
            target_server = server_name
        else:
            # Search all connected servers for the tool
            for name, connection in self.active_connections.items():
                tools = connection.get("tools", [])
                if any(tool.name == tool_name for tool in tools):
                    target_server = name
                    break
        
        if not target_server:
            raise ValueError(f"Tool {tool_name} not found in any connected MCP server")
        
        # For now, return a placeholder - actual implementation would make the MCP call
        self.logger.info(f"Calling MCP tool {tool_name} with args {arguments} on server {target_server}")
        return {"status": "success", "message": f"Called {tool_name}"}
    
    async def get_resource(self, uri: str, server_name: Optional[str] = None) -> Any:
        """Get an MCP resource"""
        # For now, return a placeholder - actual implementation would fetch the resource
        self.logger.info(f"Getting MCP resource {uri} from server {server_name}")
        return {"uri": uri, "content": "Resource content"}
    
    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all MCP servers"""
        status = {}
        
        for name, config in self.servers.items():
            status[name] = {
                "enabled": config.enabled,
                "connected": name in self.active_connections,
                "transport": config.transport,
                "description": config.description
            }
            
        return status


# Default MCP server configurations for Gary-Zero
DEFAULT_MCP_SERVERS = {
    "filesystem": MCPServerConfig(
        name="filesystem",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        description="Local filesystem access",
        enabled=True
    ),
    "git": MCPServerConfig(
        name="git",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-git"],
        description="Git repository operations",
        enabled=True
    ),
    "fetch": MCPServerConfig(
        name="fetch",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-fetch"],
        description="Web content fetching",
        enabled=True
    )
}


def create_default_mcp_config(config_path: Path) -> None:
    """Create default MCP configuration file"""
    config_data = {
        "mcpServers": {
            name: server.model_dump(exclude_none=True)
            for name, server in DEFAULT_MCP_SERVERS.items()
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    logging.info(f"Created default MCP config at {config_path}")


async def initialize_mcp_integration(config_path: Optional[Path] = None) -> MCPIntegrationManager:
    """Initialize MCP integration for Gary-Zero"""
    manager = MCPIntegrationManager(config_path)
    
    # Create default config if it doesn't exist
    if not manager.config_path.exists():
        create_default_mcp_config(manager.config_path)
    
    await manager.load_config()
    
    # Try to connect to enabled servers
    for server_name in manager.servers:
        if manager.servers[server_name].enabled:
            await manager.connect_server(server_name)
    
    return manager