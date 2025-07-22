"""Hierarchical planning engine for decomposing complex objectives into actionable subtasks.

This module provides a planning engine that can break down user goals into ordered subtasks,
assign appropriate tools or instruments for each subtask, and maintain context-aware plans.
Drawing inspiration from modern autonomous-agent frameworks like Manus AI and AutoGen.
"""

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field

from framework.helpers.print_style import PrintStyle
from framework.helpers.task_models import TaskPlan, PlannedTask

# Defer heavy imports to avoid circular dependencies during testing
try:
    from framework.helpers.task_management import TaskScheduler
    _TASK_SCHEDULER_AVAILABLE = True
except ImportError:
    _TASK_SCHEDULER_AVAILABLE = False
    TaskScheduler = None

# Initialize logger
logger = logging.getLogger(__name__)


class PlanStatus(str, Enum):
    """Status of a planning operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SubtaskStatus(str, Enum):
    """Status of individual subtasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Subtask(BaseModel):
    """Individual subtask within a hierarchical plan."""
    
    id: str = Field(description="Unique identifier for the subtask")
    name: str = Field(description="Human-readable name for the subtask")
    description: str = Field(description="Detailed description of what the subtask should accomplish")
    tool_name: Optional[str] = Field(default=None, description="Recommended tool/instrument for execution")
    dependencies: List[str] = Field(default_factory=list, description="List of subtask IDs that must complete first")
    status: SubtaskStatus = Field(default=SubtaskStatus.PENDING)
    result: Optional[str] = Field(default=None, description="Result/output of subtask execution")
    error: Optional[str] = Field(default=None, description="Error message if subtask failed")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    
    def mark_started(self) -> None:
        """Mark subtask as started."""
        self.status = SubtaskStatus.IN_PROGRESS
        self.started_at = datetime.now(timezone.utc)
    
    def mark_completed(self, result: str) -> None:
        """Mark subtask as completed with result."""
        self.status = SubtaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now(timezone.utc)
    
    def mark_failed(self, error: str) -> None:
        """Mark subtask as failed with error."""
        self.status = SubtaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.now(timezone.utc)


class HierarchicalPlan(BaseModel):
    """A hierarchical plan containing ordered subtasks for achieving an objective."""
    
    id: str = Field(description="Unique identifier for the plan")
    objective: str = Field(description="High-level objective this plan aims to achieve")
    subtasks: List[Subtask] = Field(default_factory=list, description="Ordered list of subtasks")
    status: PlanStatus = Field(default=PlanStatus.PENDING)
    context_id: Optional[str] = Field(default=None, description="Agent context for plan execution")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def get_next_subtask(self) -> Optional[Subtask]:
        """Get the next subtask that can be executed (all dependencies met)."""
        for subtask in self.subtasks:
            if subtask.status != SubtaskStatus.PENDING:
                continue
                
            # Check if all dependencies are completed
            dependencies_met = True
            for dep_id in subtask.dependencies:
                dep_subtask = self.get_subtask_by_id(dep_id)
                if not dep_subtask or dep_subtask.status != SubtaskStatus.COMPLETED:
                    dependencies_met = False
                    break
            
            if dependencies_met:
                return subtask
        
        return None
    
    def get_subtask_by_id(self, subtask_id: str) -> Optional[Subtask]:
        """Get a subtask by its ID."""
        for subtask in self.subtasks:
            if subtask.id == subtask_id:
                return subtask
        return None
    
    def is_complete(self) -> bool:
        """Check if all subtasks are completed."""
        return all(subtask.status == SubtaskStatus.COMPLETED for subtask in self.subtasks)
    
    def has_failed_subtasks(self) -> bool:
        """Check if any subtasks have failed."""
        return any(subtask.status == SubtaskStatus.FAILED for subtask in self.subtasks)
    
    def get_progress_summary(self) -> Dict[str, int]:
        """Get a summary of subtask progress."""
        summary = {status.value: 0 for status in SubtaskStatus}
        for subtask in self.subtasks:
            summary[subtask.status.value] += 1
        return summary


class PlanningConfig(BaseModel):
    """Configuration options for the hierarchical planner."""
    
    auto_planning_enabled: bool = Field(default=True, description="Enable automatic planning")
    max_recursion_depth: int = Field(default=3, description="Maximum recursion depth for plan decomposition")
    model_name: str = Field(default="gpt-4", description="LLM model to use for planning")
    max_subtasks: int = Field(default=10, description="Maximum number of subtasks per plan")
    verification_enabled: bool = Field(default=True, description="Enable subtask result verification")
    retry_failed_subtasks: bool = Field(default=True, description="Retry failed subtasks with alternative approaches")
    
    @classmethod
    def get_default(cls) -> "PlanningConfig":
        """Get default planning configuration."""
        return cls()


class HierarchicalPlanner:
    """Main hierarchical planning engine for task decomposition and execution."""
    
    def __init__(self, config: Optional[PlanningConfig] = None):
        """Initialize the hierarchical planner.
        
        Args:
            config: Planning configuration options
        """
        self.config = config or PlanningConfig.get_default()
        self.active_plans: Dict[str, HierarchicalPlan] = {}
        self.printer = PrintStyle(italic=True, font_color="blue", padding=False)
        
    def create_plan(self, objective: str, context_id: Optional[str] = None) -> HierarchicalPlan:
        """Create a new hierarchical plan for the given objective.
        
        Args:
            objective: High-level objective to achieve
            context_id: Agent context for plan execution
            
        Returns:
            HierarchicalPlan: The created plan
        """
        import uuid
        plan_id = str(uuid.uuid4())
        
        plan = HierarchicalPlan(
            id=plan_id,
            objective=objective,
            context_id=context_id
        )
        
        # Decompose objective into subtasks
        subtasks = self._decompose_objective(objective)
        plan.subtasks = subtasks
        
        # Store the plan
        self.active_plans[plan_id] = plan
        
        self.printer.print(f"Created hierarchical plan '{plan_id}' with {len(subtasks)} subtasks")
        return plan
    
    def _decompose_objective(self, objective: str) -> List[Subtask]:
        """Decompose a high-level objective into actionable subtasks.
        
        This is a placeholder implementation that would typically use an LLM
        to intelligently break down complex objectives.
        
        Args:
            objective: The objective to decompose
            
        Returns:
            List of subtasks
        """
        import uuid
        
        # Simple rule-based decomposition for common patterns
        # In a full implementation, this would use LLM reasoning
        
        if "research" in objective.lower() and "summarize" in objective.lower():
            return self._create_research_and_summarize_plan(objective)
        elif "create" in objective.lower() and ("slide" in objective.lower() or "presentation" in objective.lower()):
            return self._create_presentation_plan(objective)
        elif "battery technolog" in objective.lower():
            return self._create_battery_research_plan(objective)
        else:
            return self._create_generic_plan(objective)
    
    def _create_research_and_summarize_plan(self, objective: str) -> List[Subtask]:
        """Create a plan for research and summarization tasks."""
        import uuid
        
        # Extract key topic from objective for more specific subtasks
        topic = self._extract_research_topic(objective)
        
        subtasks = [
            Subtask(
                id=str(uuid.uuid4()),
                name=f"Define research scope for {topic}",
                description=f"Identify specific aspects of {topic} to research based on the objective: {objective}",
                tool_name="knowledge_tool"
            ),
            Subtask(
                id=str(uuid.uuid4()),
                name=f"Search for {topic} information",
                description=f"Search for the latest information and developments about {topic}",
                tool_name="search_engine"
            ),
            Subtask(
                id=str(uuid.uuid4()),
                name=f"Gather detailed {topic} content",
                description=f"Collect detailed content and data about {topic} from relevant sources",
                tool_name="webpage_content_tool"
            ),
            Subtask(
                id=str(uuid.uuid4()),
                name=f"Analyze {topic} findings",
                description=f"Analyze and synthesize the gathered information about {topic}",
                tool_name="knowledge_tool"
            ),
            Subtask(
                id=str(uuid.uuid4()),
                name=f"Create {topic} summary",
                description=f"Generate a comprehensive summary of {topic} findings and insights",
                tool_name="response"
            )
        ]
        
        # Set dependencies after all subtasks are created
        if len(subtasks) >= 2:
            subtasks[1].dependencies = [subtasks[0].id]
        if len(subtasks) >= 3:
            subtasks[2].dependencies = [subtasks[1].id]
        if len(subtasks) >= 4:
            subtasks[3].dependencies = [subtasks[2].id]
        if len(subtasks) >= 5:
            subtasks[4].dependencies = [subtasks[3].id]
            
        return subtasks
    
    def _extract_research_topic(self, objective: str) -> str:
        """Extract the main research topic from an objective.
        
        Args:
            objective: The research objective
            
        Returns:
            str: The main topic to research
        """
        objective_lower = objective.lower()
        
        # Look for key research topics
        if "battery" in objective_lower:
            if "technolog" in objective_lower:
                return "battery technologies"
            else:
                return "batteries"
        elif "ai" in objective_lower or "artificial intelligence" in objective_lower:
            if "paper" in objective_lower:
                return "AI research papers"
            else:
                return "artificial intelligence"
        elif "machine learning" in objective_lower or "ml" in objective_lower:
            return "machine learning"
        elif "quantum" in objective_lower:
            return "quantum computing"
        elif "renewable energy" in objective_lower:
            return "renewable energy"
        elif "climate" in objective_lower:
            return "climate technology"
        else:
            # Extract the main subject (simple heuristic)
            words = objective_lower.split()
            # Look for nouns that might be the topic
            key_words = []
            for word in words:
                if len(word) > 3 and word not in ["research", "analyze", "create", "generate", "latest", "recent"]:
                    key_words.append(word)
            
            if key_words:
                return " ".join(key_words[:2])  # Take first 2 key words
            else:
                return "the specified topic"
    
    def _create_presentation_plan(self, objective: str) -> List[Subtask]:
        """Create a plan for presentation creation tasks."""
        import uuid
        
        # Extract presentation topic
        topic = self._extract_presentation_topic(objective)
        
        subtasks = [
            Subtask(
                id=str(uuid.uuid4()),
                name=f"Define {topic} presentation scope",
                description=f"Determine the scope, audience, and key points for the {topic} presentation",
                tool_name="knowledge_tool"
            ),
            Subtask(
                id=str(uuid.uuid4()),
                name=f"Create {topic} outline",
                description=f"Develop a structured outline for {topic} with main sections and key points",
                tool_name="code_execution_tool"
            ),
            Subtask(
                id=str(uuid.uuid4()),
                name=f"Generate {topic} slide content",
                description=f"Create detailed content for each slide about {topic}",
                tool_name="code_execution_tool"
            ),
            Subtask(
                id=str(uuid.uuid4()),
                name=f"Format {topic} presentation",
                description=f"Format the {topic} content into a proper presentation format (PowerPoint/HTML)",
                tool_name="code_execution_tool"
            )
        ]
        
        # Set dependencies
        if len(subtasks) >= 2:
            subtasks[1].dependencies = [subtasks[0].id]
        if len(subtasks) >= 3:
            subtasks[2].dependencies = [subtasks[1].id]
        if len(subtasks) >= 4:
            subtasks[3].dependencies = [subtasks[2].id]
            
        return subtasks
    
    def _extract_presentation_topic(self, objective: str) -> str:
        """Extract the presentation topic from an objective.
        
        Args:
            objective: The presentation objective
            
        Returns:
            str: The presentation topic
        """
        objective_lower = objective.lower()
        
        # Look for specific topics
        if "machine learning" in objective_lower:
            return "machine learning"
        elif "ai" in objective_lower:
            return "AI"
        elif "battery" in objective_lower:
            return "battery technology"
        elif "data" in objective_lower and "visualization" in objective_lower:
            return "data visualization"
        elif "dashboard" in objective_lower:
            return "dashboard"
        else:
            # Extract key terms
            words = objective_lower.replace("slide", "").replace("deck", "").replace("presentation", "").split()
            key_words = [word for word in words if len(word) > 3 and word not in ["create", "about", "make"]]
            if key_words:
                return " ".join(key_words[:2])
            else:
                return "presentation"
    
    def _create_battery_research_plan(self, objective: str) -> List[Subtask]:
        """Create a specific plan for battery technology research."""
        import uuid
        
        subtasks = [
            Subtask(
                id=str(uuid.uuid4()),
                name="Search for latest battery technologies",
                description="Find recent developments in battery technology",
                tool_name="search_engine"
            ),
            Subtask(
                id=str(uuid.uuid4()),
                name="Analyze lithium-ion advances",
                description="Research improvements in lithium-ion battery technology",
                tool_name="webpage_content_tool"
            ),
            Subtask(
                id=str(uuid.uuid4()),
                name="Investigate solid-state batteries",
                description="Research solid-state battery developments",
                tool_name="webpage_content_tool"
            ),
            Subtask(
                id=str(uuid.uuid4()),
                name="Review alternative chemistries",
                description="Investigate alternative battery chemistries (sodium-ion, lithium-sulfur, etc.)",
                tool_name="webpage_content_tool"
            ),
            Subtask(
                id=str(uuid.uuid4()),
                name="Compile comprehensive summary",
                description="Create a detailed summary of all battery technology findings",
                tool_name="response"
            )
        ]
        
        # Dependencies: analysis tasks can run in parallel after search, summary depends on all
        if len(subtasks) >= 5:
            subtasks[1].dependencies = [subtasks[0].id]
            subtasks[2].dependencies = [subtasks[0].id]  
            subtasks[3].dependencies = [subtasks[0].id]
            subtasks[4].dependencies = [subtasks[1].id, subtasks[2].id, subtasks[3].id]
            
        return subtasks
    
    def _create_generic_plan(self, objective: str) -> List[Subtask]:
        """Create a generic plan for unknown objectives."""
        import uuid
        
        objective_lower = objective.lower()
        
        # Determine primary action and appropriate tools
        if any(word in objective_lower for word in ["search", "find", "research", "investigate"]):
            # Research/search-oriented task
            subtasks = [
                Subtask(
                    id=str(uuid.uuid4()),
                    name="Search for information",
                    description=f"Search for information related to: {objective}",
                    tool_name="search_engine"
                ),
                Subtask(
                    id=str(uuid.uuid4()),
                    name="Gather detailed content",
                    description=f"Collect detailed information from sources about: {objective}",
                    tool_name="webpage_content_tool"
                ),
                Subtask(
                    id=str(uuid.uuid4()),
                    name="Summarize findings",
                    description=f"Summarize the findings about: {objective}",
                    tool_name="response"
                )
            ]
        elif any(word in objective_lower for word in ["create", "build", "develop", "generate", "make"]):
            # Creation/development task
            if any(word in objective_lower for word in ["code", "script", "program", "application", "software"]):
                # Code-related creation
                subtasks = [
                    Subtask(
                        id=str(uuid.uuid4()),
                        name="Plan development approach",
                        description=f"Plan the approach for: {objective}",
                        tool_name="knowledge_tool"
                    ),
                    Subtask(
                        id=str(uuid.uuid4()),
                        name="Implement solution",
                        description=f"Implement the solution for: {objective}",
                        tool_name="code_execution_tool"
                    ),
                    Subtask(
                        id=str(uuid.uuid4()),
                        name="Test and verify",
                        description=f"Test and verify the solution for: {objective}",
                        tool_name="code_execution_tool"
                    )
                ]
            else:
                # General creation task
                subtasks = [
                    Subtask(
                        id=str(uuid.uuid4()),
                        name="Define requirements",
                        description=f"Define requirements for: {objective}",
                        tool_name="knowledge_tool"
                    ),
                    Subtask(
                        id=str(uuid.uuid4()),
                        name="Create content",
                        description=f"Create the content for: {objective}",
                        tool_name="code_execution_tool"
                    ),
                    Subtask(
                        id=str(uuid.uuid4()),
                        name="Review and finalize",
                        description=f"Review and finalize: {objective}",
                        tool_name="response"
                    )
                ]
        elif any(word in objective_lower for word in ["analyze", "examine", "evaluate", "assess"]):
            # Analysis task
            subtasks = [
                Subtask(
                    id=str(uuid.uuid4()),
                    name="Gather data for analysis",
                    description=f"Gather data and information for analyzing: {objective}",
                    tool_name="knowledge_tool"
                ),
                Subtask(
                    id=str(uuid.uuid4()),
                    name="Perform analysis",
                    description=f"Perform detailed analysis of: {objective}",
                    tool_name="code_execution_tool"
                ),
                Subtask(
                    id=str(uuid.uuid4()),
                    name="Generate analysis report",
                    description=f"Generate analysis report for: {objective}",
                    tool_name="response"
                )
            ]
        elif any(word in objective_lower for word in ["summarize", "report", "document"]):
            # Documentation/reporting task
            subtasks = [
                Subtask(
                    id=str(uuid.uuid4()),
                    name="Collect information",
                    description=f"Collect information needed for: {objective}",
                    tool_name="knowledge_tool"
                ),
                Subtask(
                    id=str(uuid.uuid4()),
                    name="Organize content",
                    description=f"Organize and structure content for: {objective}",
                    tool_name="knowledge_tool"
                ),
                Subtask(
                    id=str(uuid.uuid4()),
                    name="Generate final output",
                    description=f"Generate the final output for: {objective}",
                    tool_name="response"
                )
            ]
        else:
            # Fallback generic plan
            subtasks = [
                Subtask(
                    id=str(uuid.uuid4()),
                    name="Analyze objective",
                    description=f"Break down and understand the objective: {objective}",
                    tool_name="knowledge_tool"
                ),
                Subtask(
                    id=str(uuid.uuid4()),
                    name="Execute main task",
                    description=f"Perform the primary work needed to achieve: {objective}",
                    tool_name="code_execution_tool"
                ),
                Subtask(
                    id=str(uuid.uuid4()),
                    name="Verify completion",
                    description=f"Verify that the objective has been successfully achieved: {objective}",
                    tool_name="response"
                )
            ]
        
        # Set dependencies
        for i in range(1, len(subtasks)):
            subtasks[i].dependencies = [subtasks[i-1].id]
            
        return subtasks
    
    def get_plan(self, plan_id: str) -> Optional[HierarchicalPlan]:
        """Get a plan by its ID.
        
        Args:
            plan_id: The plan identifier
            
        Returns:
            The plan if found, None otherwise
        """
        return self.active_plans.get(plan_id)
    
    def execute_plan(self, plan_id: str) -> bool:
        """Execute a hierarchical plan by converting it to TaskScheduler tasks.
        
        Args:
            plan_id: The plan to execute
            
        Returns:
            True if plan execution was started successfully
        """
        plan = self.get_plan(plan_id)
        if not plan:
            logger.error(f"Plan not found: {plan_id}")
            return False
        
        plan.status = PlanStatus.IN_PROGRESS
        plan.updated_at = datetime.now(timezone.utc)
        
        # Create planned tasks for each subtask
        if not _TASK_SCHEDULER_AVAILABLE:
            logger.warning("TaskScheduler not available - plan execution disabled")
            return False
            
        scheduler = TaskScheduler.get()
        execution_times = []
        base_time = datetime.now(timezone.utc)
        
        for i, subtask in enumerate(plan.subtasks):
            # Schedule subtasks with small delays to handle dependencies
            execution_time = base_time.replace(second=base_time.second + (i * 10))
            execution_times.append(execution_time)
            
            # Create a planned task for this subtask
            task_plan = TaskPlan.create(todo=[execution_time])
            
            planned_task = PlannedTask.create(
                name=f"Subtask: {subtask.name}",
                system_prompt="You are an autonomous agent executing a subtask as part of a larger plan.",
                prompt=f"Execute this subtask: {subtask.description}\n\nRecommended tool: {subtask.tool_name or 'auto-select'}",
                plan=task_plan,
                context_id=plan.context_id
            )
            
            scheduler.add_task(planned_task)
        
        self.printer.print(f"Started execution of plan '{plan_id}' with {len(plan.subtasks)} subtasks")
        return True
    
    def get_plan_progress(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get progress information for a plan.
        
        Args:
            plan_id: The plan identifier
            
        Returns:
            Progress information dictionary
        """
        plan = self.get_plan(plan_id)
        if not plan:
            return None
        
        progress = plan.get_progress_summary()
        
        return {
            "plan_id": plan_id,
            "objective": plan.objective,
            "status": plan.status,
            "subtask_progress": progress,
            "total_subtasks": len(plan.subtasks),
            "completed_subtasks": progress.get(SubtaskStatus.COMPLETED.value, 0),
            "failed_subtasks": progress.get(SubtaskStatus.FAILED.value, 0),
            "is_complete": plan.is_complete(),
            "created_at": plan.created_at,
            "updated_at": plan.updated_at
        }