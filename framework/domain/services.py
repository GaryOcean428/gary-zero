"""Domain services for the Gary-Zero framework.

Implements domain service patterns for business logic that doesn't
naturally fit into entities or value objects.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from framework.interfaces import BaseService
from .entities import Agent, Message, Session, Tool
from .events import EventBus, get_event_bus
from .value_objects import ModelConfiguration, SecurityContext, ToolParameters

logger = logging.getLogger(__name__)


class DomainService(BaseService):
    """Base class for domain services."""
    
    def __init__(self, event_bus: EventBus = None):
        super().__init__()
        self.event_bus = event_bus or get_event_bus()
    
    async def initialize(self) -> None:
        """Initialize the domain service."""
        await self._set_initialized()
        logger.info(f"Initialized domain service: {self.__class__.__name__}")
    
    async def shutdown(self) -> None:
        """Shutdown the domain service."""
        await self._set_shutdown()
        logger.info(f"Shutdown domain service: {self.__class__.__name__}")


class AgentOrchestrationService(DomainService):
    """Domain service for orchestrating agent operations."""
    
    def __init__(self, event_bus: EventBus = None):
        super().__init__(event_bus)
        self._active_agents: Dict[str, Agent] = {}
        self._agent_configs: Dict[str, ModelConfiguration] = {}
    
    async def create_agent(self, name: str, agent_type: str, 
                          config: ModelConfiguration,
                          security_context: SecurityContext) -> Agent:
        """Create and register a new agent."""
        # Validate permissions
        if not security_context.has_permission("agent.create"):
            raise PermissionError("Insufficient permissions to create agent")
        
        # Create agent entity
        agent = Agent(
            name=name,
            agent_type=agent_type,
            configuration=config.__dict__
        )
        
        # Store configuration
        self._agent_configs[agent.id] = config
        
        # Activate agent (this will raise domain events)
        agent.activate()
        
        # Publish events
        for event in agent.get_uncommitted_events():
            await self.event_bus.publish(event)
        agent.mark_events_as_committed()
        
        # Register as active
        self._active_agents[agent.id] = agent
        
        logger.info(f"Created agent {agent.id} with type {agent_type}")
        return agent
    
    async def pause_agent(self, agent_id: str, security_context: SecurityContext) -> None:
        """Pause an active agent."""
        if not security_context.has_permission("agent.pause"):
            raise PermissionError("Insufficient permissions to pause agent")
        
        agent = self._active_agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent.pause()
        logger.info(f"Paused agent {agent_id}")
    
    async def stop_agent(self, agent_id: str, security_context: SecurityContext) -> None:
        """Stop an agent."""
        if not security_context.has_permission("agent.stop"):
            raise PermissionError("Insufficient permissions to stop agent")
        
        agent = self._active_agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent.stop()
        self._active_agents.pop(agent_id, None)
        self._agent_configs.pop(agent_id, None)
        logger.info(f"Stopped agent {agent_id}")
    
    def get_active_agents(self) -> List[Agent]:
        """Get all active agents."""
        return [agent for agent in self._active_agents.values() 
                if agent.status == "active"]
    
    def get_agent_configuration(self, agent_id: str) -> Optional[ModelConfiguration]:
        """Get agent configuration."""
        return self._agent_configs.get(agent_id)


class MessageProcessingService(DomainService):
    """Domain service for processing messages."""
    
    def __init__(self, event_bus: EventBus = None):
        super().__init__(event_bus)
        self._processing_queue: List[Message] = []
    
    async def process_message(self, message: Message, agent_id: str,
                            security_context: SecurityContext) -> Dict[str, Any]:
        """Process a message with an agent."""
        if not security_context.has_permission("message.process"):
            raise PermissionError("Insufficient permissions to process message")
        
        # Validate message
        if not message.content.strip():
            raise ValueError("Message content cannot be empty")
        
        # Simulate processing (in real implementation, this would call the AI model)
        import time
        start_time = time.time()
        
        # Add to processing queue
        self._processing_queue.append(message)
        
        try:
            # Simulate AI processing delay
            import asyncio
            await asyncio.sleep(0.1)
            
            # Mark as processed
            processing_time = (time.time() - start_time) * 1000
            message.mark_as_processed(processing_time)
            
            # Publish events
            for event in message.get_uncommitted_events():
                await self.event_bus.publish(event)
            message.mark_events_as_committed()
            
            # Remove from processing queue
            self._processing_queue.remove(message)
            
            result = {
                "message_id": message.id,
                "response": f"Processed by agent {agent_id}: {message.content}",
                "processing_time_ms": processing_time
            }
            
            logger.info(f"Processed message {message.id} in {processing_time:.2f}ms")
            return result
            
        except Exception as e:
            # Remove from processing queue on error
            if message in self._processing_queue:
                self._processing_queue.remove(message)
            logger.error(f"Error processing message {message.id}: {e}")
            raise
    
    def get_queue_length(self) -> int:
        """Get current processing queue length."""
        return len(self._processing_queue)


class ToolExecutionService(DomainService):
    """Domain service for executing tools."""
    
    def __init__(self, event_bus: EventBus = None):
        super().__init__(event_bus)
        self._available_tools: Dict[str, Tool] = {}
    
    def register_tool(self, tool: Tool) -> None:
        """Register a tool for execution."""
        self._available_tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    async def execute_tool(self, tool_params: ToolParameters, agent_id: str,
                          security_context: SecurityContext) -> Dict[str, Any]:
        """Execute a tool with given parameters."""
        if not security_context.has_permission("tool.execute"):
            raise PermissionError("Insufficient permissions to execute tool")
        
        tool = self._available_tools.get(tool_params.tool_name)
        if not tool:
            raise ValueError(f"Tool {tool_params.tool_name} not found")
        
        if not tool.enabled:
            raise ValueError(f"Tool {tool_params.tool_name} is disabled")
        
        # Simulate tool execution
        import time
        start_time = time.time()
        
        try:
            # Simulate tool execution (in real implementation, this would call actual tool)
            import asyncio
            await asyncio.sleep(0.05)
            
            execution_time = (time.time() - start_time) * 1000
            result = {
                "success": True,
                "output": f"Tool {tool_params.tool_name} executed successfully",
                "parameters": tool_params.parameters
            }
            
            # Record execution on tool entity
            tool.execute(agent_id, tool_params.parameters, result, execution_time)
            
            # Publish events
            for event in tool.get_uncommitted_events():
                await self.event_bus.publish(event)
            tool.mark_events_as_committed()
            
            logger.info(f"Executed tool {tool_params.tool_name} in {execution_time:.2f}ms")
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_params.tool_name}: {e}")
            raise
    
    def get_available_tools(self) -> List[Tool]:
        """Get all available tools."""
        return [tool for tool in self._available_tools.values() if tool.enabled]


class SessionManagementService(DomainService):
    """Domain service for managing user and agent sessions."""
    
    def __init__(self, event_bus: EventBus = None):
        super().__init__(event_bus)
        self._active_sessions: Dict[str, Session] = {}
    
    async def create_session(self, user_id: str, session_type: str = "user",
                           metadata: Dict[str, Any] = None) -> Session:
        """Create a new session."""
        session = Session(
            user_id=user_id,
            session_type=session_type,
            metadata=metadata or {}
        )
        
        self._active_sessions[session.id] = session
        logger.info(f"Created {session_type} session {session.id} for user {user_id}")
        return session
    
    async def end_session(self, session_id: str, security_context: SecurityContext) -> None:
        """End a session."""
        if not security_context.has_permission("session.end"):
            raise PermissionError("Insufficient permissions to end session")
        
        session = self._active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.end_session()
        self._active_sessions.pop(session_id, None)
        logger.info(f"Ended session {session_id}")
    
    def get_active_sessions(self) -> List[Session]:
        """Get all active sessions."""
        return [session for session in self._active_sessions.values() 
                if session.status == "active"]
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a specific session."""
        return self._active_sessions.get(session_id)