"""OpenAI Agents SDK integration wrapper for Gary-Zero.

This module provides a compatibility layer between the existing Gary-Zero agent
system and the OpenAI Agents SDK, enabling gradual migration to standardized
agent primitives while maintaining backward compatibility.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Callable, TYPE_CHECKING
from dataclasses import dataclass, field

# OpenAI Agents SDK imports
from agents import Agent as SDKAgent, AgentBase, Session, Tool, Handoff
from agents import RunResult, RunConfig, ModelProvider, Model
from agents import OpenAIProvider, OpenAIChatCompletionsModel
from agents import InputGuardrail, OutputGuardrail
from agents import Trace, get_current_trace, set_trace_processors

# Gary-Zero imports
from framework.helpers.task_manager import TaskManager, Task, TaskStatus, TaskCategory
from framework.helpers import log as Log
from framework.helpers.print_style import PrintStyle

# Forward reference imports
if TYPE_CHECKING:
    from agent import Agent


@dataclass
class SDKAgentConfig:
    """Configuration for SDK-wrapped agents."""
    name: str
    model_provider: str = "openai"
    model_name: str = "o3"  # Updated to modern o3 model
    instructions: str = ""
    enable_tracing: bool = True
    enable_guardrails: bool = True
    max_turns: int = 50


class GaryZeroSDKAgent:
    """Wrapper that adapts existing Gary-Zero agents to OpenAI Agents SDK."""
    
    def __init__(self, gary_agent: "Agent", config: SDKAgentConfig):
        self.gary_agent = gary_agent
        self.config = config
        self.task_manager = TaskManager.get_instance()
        
        # Create SDK agent instance
        self.sdk_agent = self._create_sdk_agent()
        
        # Initialize session
        self.session = Session()
        
        # SDK run tracking
        self._current_run_id: Optional[str] = None
        self._sdk_context: Dict[str, Any] = {}
        
    def _create_sdk_agent(self) -> SDKAgent:
        """Create the underlying SDK agent."""
        # Configure model provider
        if self.config.model_provider.lower() == "openai":
            provider = OpenAIProvider()
            model = OpenAIChatCompletionsModel(
                name=self.config.model_name,
                provider=provider
            )
        else:
            # Fallback to default
            provider = OpenAIProvider()
            model = OpenAIChatCompletionsModel(
                name="o3",  # Updated to modern o3 model
                provider=provider
            )
        
        # Create SDK agent with configuration
        agent = SDKAgent(
            name=self.config.name,
            model=model,
            instructions=self.config.instructions or self._get_default_instructions(),
            max_turns=self.config.max_turns
        )
        
        return agent
    
    def _get_default_instructions(self) -> str:
        """Get default instructions based on Gary-Zero agent configuration."""
        return f"""
        You are {self.config.name}, an AI agent in the Gary-Zero framework.
        
        You have access to various tools and can perform complex tasks.
        Always explain your reasoning and ask for clarification when needed.
        Work systematically through tasks and provide clear status updates.
        
        When you complete a task, use the response tool to provide your final answer.
        """
    
    async def execute_task(self, task_id: str, message: str) -> Dict[str, Any]:
        """Execute a task using SDK primitives."""
        task = self.task_manager.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        try:
            # Start tracing if enabled
            if self.config.enable_tracing:
                trace = self._start_trace(task_id, message)
            
            # Mark task as started
            self.task_manager.start_task(task_id, f"sdk_{self.config.name}")
            
            # Create run configuration
            run_config = RunConfig(
                max_turns=self.config.max_turns,
                enable_parallel_tool_calls=True
            )
            
            # Execute with SDK
            result = await self._run_sdk_agent(message, run_config)
            
            # Process result and update task
            if result.is_success:
                self.task_manager.complete_task(task_id, str(result.value))
                return {
                    "status": "completed",
                    "result": result.value,
                    "trace_id": trace.trace_id if self.config.enable_tracing else None
                }
            else:
                error_msg = str(result.error) if result.error else "Unknown error"
                self.task_manager.fail_task(task_id, error_msg)
                return {
                    "status": "failed",
                    "error": error_msg,
                    "trace_id": trace.trace_id if self.config.enable_tracing else None
                }
                
        except Exception as e:
            self.task_manager.fail_task(task_id, str(e))
            PrintStyle(font_color="red", padding=True).print(f"SDK Agent execution failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _run_sdk_agent(self, message: str, config: RunConfig) -> RunResult:
        """Run the SDK agent with the given message."""
        # Apply guardrails if enabled
        if self.config.enable_guardrails:
            message = await self._apply_input_guardrails(message)
        
        # Execute through SDK
        result = await self.sdk_agent.run(
            messages=[{"role": "user", "content": message}],
            session=self.session,
            config=config
        )
        
        # Apply output guardrails if enabled
        if self.config.enable_guardrails and result.is_success:
            result = await self._apply_output_guardrails(result)
        
        return result
    
    async def _apply_input_guardrails(self, message: str) -> str:
        """Apply input guardrails to validate and sanitize input."""
        # Import guardrails (will be created in next phase)
        try:
            from framework.helpers.guardrails import InputValidator
            validator = InputValidator()
            return await validator.validate_and_sanitize(message)
        except ImportError:
            # Fallback to basic validation
            return self._basic_input_validation(message)
    
    def _basic_input_validation(self, message: str) -> str:
        """Basic input validation as fallback."""
        # Remove potentially harmful content
        if len(message) > 10000:
            message = message[:10000] + "... [truncated]"
        
        # Basic sanitization
        message = message.strip()
        
        return message
    
    async def _apply_output_guardrails(self, result: RunResult) -> RunResult:
        """Apply output guardrails to validate response."""
        try:
            from framework.helpers.guardrails import OutputValidator
            validator = OutputValidator()
            validated_result = await validator.validate_output(result)
            return validated_result
        except ImportError:
            # Return original result if guardrails not available
            return result
    
    def _start_trace(self, task_id: str, message: str) -> Trace:
        """Start tracing for the SDK execution."""
        trace = get_current_trace()
        if trace:
            # Add Gary-Zero specific metadata
            trace.add_tag("gary_zero_task_id", task_id)
            trace.add_tag("gary_zero_agent", self.gary_agent.agent_name)
            trace.add_tag("execution_time", datetime.now(timezone.utc).isoformat())
        return trace
    
    async def handle_handoff(self, to_agent: str, context: Dict[str, Any]) -> bool:
        """Handle agent handoff using SDK primitives."""
        try:
            # Create handoff object
            handoff = Handoff(
                agent_name=to_agent,
                context=context
            )
            
            # Execute handoff through SDK
            # This would typically be handled by the SDK's session management
            PrintStyle(font_color="cyan", padding=True).print(
                f"SDK Handoff initiated: {self.config.name} -> {to_agent}"
            )
            
            return True
            
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(f"Handoff failed: {e}")
            return False
    
    def get_sdk_tools(self) -> List[Tool]:
        """Get SDK-compatible tools from existing Gary-Zero tools."""
        # This will be implemented in Phase 5
        return []
    
    def get_session_data(self) -> Dict[str, Any]:
        """Get current session data."""
        return {
            "session_id": self.session.session_id if hasattr(self.session, 'session_id') else None,
            "agent_name": self.config.name,
            "current_run_id": self._current_run_id,
            "context": self._sdk_context
        }


class SDKTaskWrapper:
    """Wrapper to adapt Gary-Zero tasks to SDK task format."""
    
    def __init__(self, gary_task: Task):
        self.gary_task = gary_task
        self.sdk_metadata = self._extract_sdk_metadata()
    
    def _extract_sdk_metadata(self) -> Dict[str, Any]:
        """Extract SDK-relevant metadata from Gary-Zero task."""
        return {
            "id": self.gary_task.id,
            "title": self.gary_task.title,
            "description": self.gary_task.description,
            "category": self.gary_task.category.value,
            "priority": self.gary_task.priority.value,
            "status": self.gary_task.status.value,
            "progress": self.gary_task.progress,
            "created_at": self.gary_task.created_at.isoformat(),
            "context": self.gary_task.context
        }
    
    def to_sdk_format(self) -> Dict[str, Any]:
        """Convert to SDK-compatible task format."""
        return {
            "task_id": self.gary_task.id,
            "instructions": self.gary_task.description,
            "metadata": self.sdk_metadata,
            "context": self.gary_task.context
        }


class SDKAgentOrchestrator:
    """Orchestrator for managing multiple SDK-wrapped agents."""
    
    def __init__(self):
        self.agents: Dict[str, GaryZeroSDKAgent] = {}
        self.active_sessions: Dict[str, Session] = {}
        
    def register_agent(self, gary_agent: "Agent", config: SDKAgentConfig) -> str:
        """Register a Gary-Zero agent with SDK wrapper."""
        agent_id = f"sdk_{config.name}_{uuid.uuid4().hex[:8]}"
        
        wrapped_agent = GaryZeroSDKAgent(gary_agent, config)
        self.agents[agent_id] = wrapped_agent
        
        PrintStyle(font_color="green", padding=True).print(
            f"Registered SDK agent: {config.name} ({agent_id})"
        )
        
        return agent_id
    
    async def execute_with_agent(self, agent_id: str, task_id: str, message: str) -> Dict[str, Any]:
        """Execute a task with a specific SDK agent."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent = self.agents[agent_id]
        return await agent.execute_task(task_id, message)
    
    async def coordinate_handoff(self, from_agent_id: str, to_agent_id: str, 
                                context: Dict[str, Any]) -> bool:
        """Coordinate handoff between SDK agents."""
        if from_agent_id not in self.agents or to_agent_id not in self.agents:
            return False
        
        from_agent = self.agents[from_agent_id]
        to_agent = self.agents[to_agent_id]
        
        # Perform handoff
        success = await from_agent.handle_handoff(to_agent.config.name, context)
        
        if success:
            PrintStyle(font_color="blue", padding=True).print(
                f"Handoff completed: {from_agent.config.name} -> {to_agent.config.name}"
            )
        
        return success
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific agent."""
        if agent_id not in self.agents:
            return None
        
        agent = self.agents[agent_id]
        return {
            "agent_id": agent_id,
            "name": agent.config.name,
            "session_data": agent.get_session_data(),
            "is_active": True  # Simplified for now
        }
    
    def get_all_agents_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered agents."""
        return {
            agent_id: self.get_agent_status(agent_id)
            for agent_id in self.agents
        }


# Global orchestrator instance
_orchestrator: Optional[SDKAgentOrchestrator] = None


def get_sdk_orchestrator() -> SDKAgentOrchestrator:
    """Get the global SDK agent orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SDKAgentOrchestrator()
    return _orchestrator


def initialize_sdk_integration(enable_tracing: bool = True) -> None:
    """Initialize the OpenAI Agents SDK integration."""
    if enable_tracing:
        # Configure SDK tracing
        set_trace_processors([])  # Will be configured with actual processors
    
    PrintStyle(font_color="green", padding=True).print(
        "OpenAI Agents SDK integration initialized"
    )


# Backward compatibility functions
def wrap_gary_agent_with_sdk(gary_agent: "Agent", 
                            name: Optional[str] = None) -> GaryZeroSDKAgent:
    """Convenience function to wrap a Gary-Zero agent with SDK."""
    config = SDKAgentConfig(
        name=name or gary_agent.agent_name,
        instructions=f"You are {gary_agent.agent_name} in the Gary-Zero framework."
    )
    
    return GaryZeroSDKAgent(gary_agent, config)