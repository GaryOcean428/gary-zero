"""
AI-Manus Integration Configuration for Gary-Zero
Centralized integration point for AI-Manus features
"""

from typing import Optional, Dict, List, Any
from pydantic import BaseModel
import asyncio
import logging
import time
from pathlib import Path

from .mcp_integration import MCPIntegrationManager, initialize_mcp_integration
from ..tools.enhanced_browser import EnhancedBrowserTool, BrowserTaskRunner, create_enhanced_browser
from ..container.sandbox_manager import SandboxManager, SandboxPool, create_sandbox_manager

logger = logging.getLogger(__name__)


class AiManusFeatures(BaseModel):
    """Configuration for AI-Manus features to integrate"""
    mcp_integration: bool = True
    enhanced_browser: bool = True
    sandbox_management: bool = True
    task_sessions: bool = True
    browser_takeover: bool = False  # Advanced feature, disabled by default
    
    # MCP configuration
    mcp_config_path: Optional[str] = None
    mcp_auto_connect: bool = True
    
    # Browser configuration  
    browser_headless: bool = True
    browser_screenshots: bool = True
    
    # Sandbox configuration
    max_sandboxes: int = 5
    sandbox_pool_size: int = 2
    default_sandbox_image: str = "python:3.12-slim"


class AiManusIntegrationManager:
    """
    Main integration manager for AI-Manus features in Gary-Zero
    """
    
    def __init__(self, config: AiManusFeatures):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Component managers
        self.mcp_manager: Optional[MCPIntegrationManager] = None
        self.browser_tool: Optional[EnhancedBrowserTool] = None
        self.browser_runner: Optional[BrowserTaskRunner] = None
        self.sandbox_manager: Optional[SandboxManager] = None
        self.sandbox_pool: Optional[SandboxPool] = None
        
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize all AI-Manus components"""
        try:
            self.logger.info("Initializing AI-Manus integration...")
            
            # Initialize MCP integration
            if self.config.mcp_integration:
                config_path = Path(self.config.mcp_config_path) if self.config.mcp_config_path else None
                self.mcp_manager = await initialize_mcp_integration(config_path)
                self.logger.info("MCP integration initialized")
            
            # Initialize enhanced browser
            if self.config.enhanced_browser:
                self.browser_tool = await create_enhanced_browser(
                    headless=self.config.browser_headless
                )
                self.browser_runner = BrowserTaskRunner(self.browser_tool)
                self.logger.info("Enhanced browser tools initialized")
            
            # Initialize sandbox management
            if self.config.sandbox_management:
                self.sandbox_manager = await create_sandbox_manager(
                    max_sandboxes=self.config.max_sandboxes
                )
                
                if self.config.sandbox_pool_size > 0:
                    self.sandbox_pool = SandboxPool(
                        self.sandbox_manager, 
                        pool_size=self.config.sandbox_pool_size
                    )
                    await self.sandbox_pool.initialize_pool()
                
                self.logger.info("Sandbox management initialized")
            
            self.initialized = True
            self.logger.info("AI-Manus integration completed successfully")
            
        except Exception as e:
            self.logger.error(f"AI-Manus integration failed: {e}")
            raise
    
    async def get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get available MCP tools"""
        if not self.mcp_manager:
            return []
        
        tools = await self.mcp_manager.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
                "source": "mcp"
            }
            for tool in tools
        ]
    
    async def execute_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute an MCP tool"""
        if not self.mcp_manager:
            raise ValueError("MCP integration not initialized")
        
        return await self.mcp_manager.call_tool(tool_name, arguments)
    
    async def create_browser_session(self) -> Optional[BrowserTaskRunner]:
        """Create a new browser session"""
        if not self.config.enhanced_browser:
            return None
        
        browser = await create_enhanced_browser(headless=self.config.browser_headless)
        return BrowserTaskRunner(browser)
    
    async def create_sandbox_session(self, session_id: str, 
                                   config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create a sandbox for a session"""
        if not self.sandbox_manager:
            return None
        
        if self.sandbox_pool:
            return await self.sandbox_pool.acquire_sandbox(session_id)
        else:
            sandbox = await self.sandbox_manager.create_session_sandbox(session_id, config)
            return sandbox.id if sandbox.status == "running" else None
    
    async def execute_in_sandbox(self, sandbox_id: str, command: str, 
                               working_dir: Optional[str] = None) -> Dict[str, Any]:
        """Execute a command in a sandbox"""
        if not self.sandbox_manager:
            raise ValueError("Sandbox management not initialized")
        
        execution = await self.sandbox_manager.execute_command(
            sandbox_id, command, working_dir
        )
        
        return {
            "id": execution.id,
            "status": execution.status,
            "exit_code": execution.exit_code,
            "stdout": execution.stdout,
            "stderr": execution.stderr,
            "duration": (execution.end_time or time.time()) - execution.start_time
        }
    
    async def cleanup_session(self, session_id: str):
        """Clean up resources for a session"""
        try:
            # Clean up sandbox
            if self.sandbox_pool:
                # Find sandbox for this session
                for sandbox_id, sid in self.sandbox_pool.busy_sandboxes.items():
                    if sid == session_id:
                        await self.sandbox_pool.release_sandbox(sandbox_id)
                        break
            elif self.sandbox_manager:
                # Find and destroy session sandbox
                sandboxes = await self.sandbox_manager.list_sandboxes()
                for sandbox in sandboxes:
                    if sandbox.name == f"session-{session_id}":
                        await self.sandbox_manager.destroy_sandbox(sandbox.id)
                        break
            
            self.logger.info(f"Cleaned up session resources: {session_id}")
            
        except Exception as e:
            self.logger.error(f"Session cleanup failed for {session_id}: {e}")
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all integration components"""
        status = {
            "initialized": self.initialized,
            "components": {}
        }
        
        if self.config.mcp_integration:
            status["components"]["mcp"] = {
                "enabled": True,
                "initialized": self.mcp_manager is not None,
                "servers": self.mcp_manager.get_server_status() if self.mcp_manager else {}
            }
        
        if self.config.enhanced_browser:
            status["components"]["browser"] = {
                "enabled": True,
                "initialized": self.browser_tool is not None,
                "headless": self.config.browser_headless
            }
        
        if self.config.sandbox_management:
            status["components"]["sandbox"] = {
                "enabled": True,
                "initialized": self.sandbox_manager is not None,
                "pool_enabled": self.sandbox_pool is not None,
                "stats": self.sandbox_manager.get_stats_summary() if self.sandbox_manager else {}
            }
        
        return status
    
    async def shutdown(self):
        """Shutdown all integration components"""
        try:
            self.logger.info("Shutting down AI-Manus integration...")
            
            # Close browser
            if self.browser_tool:
                await self.browser_tool.close()
            
            # Disconnect MCP servers
            if self.mcp_manager:
                for server_name in list(self.mcp_manager.active_connections.keys()):
                    await self.mcp_manager.disconnect_server(server_name)
            
            # Clean up sandboxes
            if self.sandbox_manager:
                sandbox_ids = list(self.sandbox_manager.sandboxes.keys())
                for sandbox_id in sandbox_ids:
                    await self.sandbox_manager.destroy_sandbox(sandbox_id)
            
            self.logger.info("AI-Manus integration shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Shutdown error: {e}")


# Factory functions and utilities

async def initialize_ai_manus_integration(
    config: Optional[AiManusFeatures] = None
) -> AiManusIntegrationManager:
    """Initialize AI-Manus integration with default or custom config"""
    
    if config is None:
        config = AIManus​Features()
    
    manager = AIManus​IntegrationManager(config)
    await manager.initialize()
    return manager


def create_development_config() -> AiManusFeatures:
    """Create development-friendly configuration"""
    return AIManus​Features(
        mcp_integration=True,
        enhanced_browser=True,
        sandbox_management=True,
        browser_headless=False,  # Show browser for development
        max_sandboxes=3,
        sandbox_pool_size=1
    )


def create_production_config() -> AiManusFeatures:
    """Create production-optimized configuration"""
    return AiManusFeatures(
        mcp_integration=True,
        enhanced_browser=True,
        sandbox_management=True,
        browser_headless=True,
        max_sandboxes=10,
        sandbox_pool_size=3,
        browser_takeover=False  # Disabled for security
    )


def create_minimal_config() -> AiManusFeatures:
    """Create minimal configuration for resource-constrained environments"""
    return AiManusFeatures(
        mcp_integration=True,
        enhanced_browser=False,  # Disable browser to save resources
        sandbox_management=True,
        max_sandboxes=2,
        sandbox_pool_size=0  # No pool to save resources
    )


# Integration status and health checks

async def health_check_integration(manager: AiManusIntegrationManager) -> Dict[str, Any]:
    """Perform health check on AI-Manus integration"""
    health = {
        "status": "healthy",
        "components": {},
        "issues": []
    }
    
    try:
        # Check MCP integration
        if manager.mcp_manager:
            mcp_status = manager.mcp_manager.get_server_status()
            connected_servers = len([s for s in mcp_status.values() if s.get("connected")])
            health["components"]["mcp"] = {
                "status": "healthy" if connected_servers > 0 else "warning",
                "connected_servers": connected_servers,
                "total_servers": len(mcp_status)
            }
            
            if connected_servers == 0:
                health["issues"].append("No MCP servers connected")
        
        # Check browser
        if manager.browser_tool:
            try:
                # Test basic browser functionality
                result = await manager.browser_tool.get_page_info()
                health["components"]["browser"] = {
                    "status": "healthy" if result.success else "error",
                    "message": result.message
                }
                
                if not result.success:
                    health["issues"].append(f"Browser error: {result.message}")
            except Exception as e:
                health["components"]["browser"] = {
                    "status": "error",
                    "message": str(e)
                }
                health["issues"].append(f"Browser health check failed: {e}")
        
        # Check sandbox manager
        if manager.sandbox_manager:
            stats = manager.sandbox_manager.get_stats_summary()
            health["components"]["sandbox"] = {
                "status": "healthy",
                "running_sandboxes": stats["running_sandboxes"],
                "total_sandboxes": stats["total_sandboxes"],
                "success_rate": stats["success_rate"]
            }
            
            if stats["error_sandboxes"] > 0:
                health["issues"].append(f"{stats['error_sandboxes']} sandboxes in error state")
        
        # Determine overall status
        if health["issues"]:
            health["status"] = "warning" if len(health["issues"]) <= 2 else "error"
        
        return health
        
    except Exception as e:
        health["status"] = "error"
        health["issues"].append(f"Health check failed: {e}")
        return health


# Example usage and configuration templates
INTEGRATION_EXAMPLES = {
    "web_research_workflow": {
        "description": "Web research with sandboxed analysis",
        "components": ["mcp", "browser", "sandbox"],
        "workflow": [
            "Create sandbox session",
            "Use browser to search and extract content",
            "Process content in sandbox environment",
            "Store results via MCP tools"
        ]
    },
    "code_execution_workflow": {
        "description": "Safe code execution with MCP integration",
        "components": ["mcp", "sandbox"],
        "workflow": [
            "Receive code via MCP",
            "Execute in isolated sandbox",
            "Return results via MCP tools"
        ]
    },
    "automated_testing_workflow": {
        "description": "Automated web testing with screenshots",
        "components": ["browser", "sandbox"],
        "workflow": [
            "Create browser session",
            "Execute test scenarios",
            "Capture screenshots",
            "Analyze results in sandbox"
        ]
    }
}