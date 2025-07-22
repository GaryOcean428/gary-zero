"""Enhanced scheduler integration for hierarchical planning.

This module extends the existing TaskScheduler to integrate seamlessly with
the hierarchical planner, enabling automatic plan execution and monitoring.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

from framework.helpers.hierarchical_planner import (
    HierarchicalPlanner,
    HierarchicalPlan,
    Subtask,
    SubtaskStatus,
    PlanStatus
)
from framework.helpers.plan_evaluation import EvaluationLoop, EvaluationCriteria
from framework.helpers.planner_config import PlannerSettings
from framework.helpers.task_models import PlannedTask, TaskPlan, TaskState

try:
    from framework.helpers.task_management import TaskScheduler
    _TASK_SCHEDULER_AVAILABLE = True
except ImportError:
    _TASK_SCHEDULER_AVAILABLE = False
    TaskScheduler = None

logger = logging.getLogger(__name__)


class PlanExecutionMonitor:
    """Monitors plan execution and handles evaluation feedback."""
    
    def __init__(self, planner: HierarchicalPlanner):
        """Initialize the execution monitor.
        
        Args:
            planner: The hierarchical planner instance
        """
        self.planner = planner
        self.evaluation_loop = EvaluationLoop()
        self.task_to_plan_mapping: Dict[str, str] = {}  # task_uuid -> plan_id
        self.task_to_subtask_mapping: Dict[str, str] = {}  # task_uuid -> subtask_id
        
    def register_plan_execution(self, plan_id: str, task_mappings: Dict[str, str]) -> None:
        """Register a plan execution with task mappings.
        
        Args:
            plan_id: The plan being executed
            task_mappings: Mapping of task_uuid to subtask_id
        """
        for task_uuid, subtask_id in task_mappings.items():
            self.task_to_plan_mapping[task_uuid] = plan_id
            self.task_to_subtask_mapping[task_uuid] = subtask_id
    
    async def handle_task_completion(self, task_uuid: str, result: str) -> None:
        """Handle completion of a scheduled task.
        
        Args:
            task_uuid: The completed task UUID
            result: The task result
        """
        if task_uuid not in self.task_to_plan_mapping:
            return  # Not a hierarchical plan task
            
        plan_id = self.task_to_plan_mapping[task_uuid]
        subtask_id = self.task_to_subtask_mapping[task_uuid]
        
        plan = self.planner.get_plan(plan_id)
        if not plan:
            logger.warning(f"Plan {plan_id} not found for completed task {task_uuid}")
            return
        
        subtask = plan.get_subtask_by_id(subtask_id)
        if not subtask:
            logger.warning(f"Subtask {subtask_id} not found in plan {plan_id}")
            return
        
        # Evaluate subtask completion
        success = self.evaluation_loop.process_subtask_completion(plan, subtask, result)
        
        if success:
            logger.info(f"Subtask '{subtask.name}' completed successfully")
            await self._check_plan_completion(plan)
        else:
            logger.info(f"Subtask '{subtask.name}' required plan adjustment")
            await self._handle_plan_adjustment(plan)
    
    async def _check_plan_completion(self, plan: HierarchicalPlan) -> None:
        """Check if plan is complete and update status.
        
        Args:
            plan: The plan to check
        """
        if plan.is_complete():
            plan.status = PlanStatus.COMPLETED
            plan.updated_at = datetime.now(timezone.utc)
            logger.info(f"Plan '{plan.id}' completed successfully")
        elif plan.has_failed_subtasks():
            failed_count = sum(1 for s in plan.subtasks if s.status == SubtaskStatus.FAILED)
            if failed_count > len(plan.subtasks) // 2:  # More than half failed
                plan.status = PlanStatus.FAILED
                logger.warning(f"Plan '{plan.id}' failed with {failed_count} failed subtasks")
    
    async def _handle_plan_adjustment(self, plan: HierarchicalPlan) -> None:
        """Handle plan adjustment after evaluation feedback.
        
        Args:
            plan: The adjusted plan
        """
        # Schedule new subtasks if they were added during adjustment
        if not _TASK_SCHEDULER_AVAILABLE:
            logger.warning("TaskScheduler not available for plan adjustment")
            return
            
        scheduler = TaskScheduler.get()
        new_tasks = []
        
        for subtask in plan.subtasks:
            if (subtask.status == SubtaskStatus.PENDING and 
                subtask.id not in self.task_to_subtask_mapping.values()):
                # This is a new subtask added during adjustment
                new_tasks.append(subtask)
        
        if new_tasks:
            await self._schedule_subtasks(plan, new_tasks, scheduler)
            logger.info(f"Scheduled {len(new_tasks)} new subtasks for plan adjustment")
    
    async def _schedule_subtasks(self, plan: HierarchicalPlan, subtasks: List[Subtask], scheduler) -> None:
        """Schedule subtasks with the TaskScheduler.
        
        Args:
            plan: The parent plan
            subtasks: Subtasks to schedule
            scheduler: TaskScheduler instance
        """
        base_time = datetime.now(timezone.utc)
        
        for i, subtask in enumerate(subtasks):
            # Schedule with delays to handle dependencies
            execution_time = base_time + timedelta(seconds=30 + (i * 15))
            
            task_plan = TaskPlan.create(todo=[execution_time])
            
            planned_task = PlannedTask.create(
                name=f"Subtask: {subtask.name}",
                system_prompt="You are an autonomous agent executing a subtask as part of a hierarchical plan.",
                prompt=f"Execute this subtask: {subtask.description}\n\nRecommended tool: {subtask.tool_name or 'auto-select'}",
                plan=task_plan,
                context_id=plan.context_id
            )
            
            scheduler.add_task(planned_task)
            
            # Register the mapping
            self.task_to_plan_mapping[planned_task.uuid] = plan.id
            self.task_to_subtask_mapping[planned_task.uuid] = subtask.id


class EnhancedHierarchicalScheduler:
    """Enhanced scheduler that integrates hierarchical planning with TaskScheduler."""
    
    def __init__(self):
        """Initialize the enhanced scheduler."""
        self.planner = HierarchicalPlanner()
        self.monitor = PlanExecutionMonitor(self.planner)
        self.config = PlannerSettings.get_config()
        
    def create_and_execute_plan(
        self, 
        objective: str, 
        context_id: Optional[str] = None,
        auto_execute: bool = True
    ) -> HierarchicalPlan:
        """Create and optionally execute a hierarchical plan.
        
        Args:
            objective: The objective to achieve
            context_id: Agent context for execution
            auto_execute: Whether to start execution immediately
            
        Returns:
            HierarchicalPlan: The created plan
        """
        # Update planner configuration
        self.planner.config = self.config
        
        # Create the plan
        plan = self.planner.create_plan(objective, context_id)
        
        if auto_execute and self.config.auto_planning_enabled:
            self.execute_plan_enhanced(plan.id)
        
        return plan
    
    def execute_plan_enhanced(self, plan_id: str) -> bool:
        """Execute a plan with enhanced monitoring and evaluation.
        
        Args:
            plan_id: The plan to execute
            
        Returns:
            bool: True if execution started successfully
        """
        if not _TASK_SCHEDULER_AVAILABLE:
            logger.error("TaskScheduler not available for plan execution")
            return False
            
        plan = self.planner.get_plan(plan_id)
        if not plan:
            logger.error(f"Plan not found: {plan_id}")
            return False
        
        plan.status = PlanStatus.IN_PROGRESS
        plan.updated_at = datetime.now(timezone.utc)
        
        scheduler = TaskScheduler.get()
        task_mappings = {}
        
        # Schedule all subtasks
        base_time = datetime.now(timezone.utc)
        
        for i, subtask in enumerate(plan.subtasks):
            # Calculate execution time based on dependencies
            execution_time = self._calculate_subtask_timing(plan, subtask, base_time)
            
            task_plan = TaskPlan.create(todo=[execution_time])
            
            # Create enhanced prompt with evaluation criteria
            enhanced_prompt = self._create_enhanced_prompt(subtask, plan.objective)
            
            planned_task = PlannedTask.create(
                name=f"Subtask: {subtask.name}",
                system_prompt="You are an autonomous agent executing a subtask as part of a hierarchical plan. Focus on producing high-quality, detailed output that can be evaluated and built upon.",
                prompt=enhanced_prompt,
                plan=task_plan,
                context_id=plan.context_id
            )
            
            scheduler.add_task(planned_task)
            task_mappings[planned_task.uuid] = subtask.id
        
        # Register with monitor
        self.monitor.register_plan_execution(plan_id, task_mappings)
        
        logger.info(f"Started enhanced execution of plan '{plan_id}' with {len(plan.subtasks)} subtasks")
        return True
    
    def _calculate_subtask_timing(self, plan: HierarchicalPlan, subtask: Subtask, base_time: datetime) -> datetime:
        """Calculate when a subtask should execute based on dependencies.
        
        Args:
            plan: The parent plan
            subtask: The subtask to schedule
            base_time: Base execution time
            
        Returns:
            datetime: When the subtask should execute
        """
        if not subtask.dependencies:
            return base_time
        
        # Find the maximum depth of dependencies
        max_depth = 0
        for dep_id in subtask.dependencies:
            dep_subtask = plan.get_subtask_by_id(dep_id)
            if dep_subtask:
                depth = self._get_subtask_depth(plan, dep_subtask) + 1
                max_depth = max(max_depth, depth)
        
        # Schedule with delay based on dependency depth
        delay_minutes = max_depth * 5  # 5 minutes per dependency level
        return base_time + timedelta(minutes=delay_minutes)
    
    def _get_subtask_depth(self, plan: HierarchicalPlan, subtask: Subtask) -> int:
        """Get the dependency depth of a subtask.
        
        Args:
            plan: The parent plan
            subtask: The subtask to analyze
            
        Returns:
            int: Dependency depth
        """
        if not subtask.dependencies:
            return 0
        
        max_depth = 0
        for dep_id in subtask.dependencies:
            dep_subtask = plan.get_subtask_by_id(dep_id)
            if dep_subtask:
                depth = self._get_subtask_depth(plan, dep_subtask) + 1
                max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _create_enhanced_prompt(self, subtask: Subtask, objective: str) -> str:
        """Create an enhanced prompt with evaluation guidance.
        
        Args:
            subtask: The subtask to create prompt for
            objective: The overall objective
            
        Returns:
            str: Enhanced prompt
        """
        prompt = f"""You are executing a subtask as part of achieving this objective: {objective}

SUBTASK: {subtask.name}
DESCRIPTION: {subtask.description}
RECOMMENDED TOOL: {subtask.tool_name or 'Select the most appropriate tool'}

IMPORTANT EXECUTION GUIDELINES:
1. Produce detailed, high-quality output that can be evaluated and used by subsequent subtasks
2. If using search tools, include specific URLs and sources
3. If analyzing content, provide structured summaries with key points
4. If creating content, ensure it's well-formatted and comprehensive
5. If encountering errors, provide clear explanation and suggest alternatives

Your output will be evaluated for quality, completeness, and usefulness for achieving the overall objective.
Focus on creating output that clearly demonstrates successful completion of the subtask."""
        
        return prompt
    
    def get_enhanced_plan_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get enhanced plan status with execution monitoring.
        
        Args:
            plan_id: The plan ID
            
        Returns:
            Enhanced status information
        """
        basic_status = self.planner.get_plan_progress(plan_id)
        if not basic_status:
            return None
        
        plan = self.planner.get_plan(plan_id)
        if not plan:
            return basic_status
        
        # Add execution monitoring information
        basic_status.update({
            "evaluation_enabled": self.config.verification_enabled,
            "retry_enabled": self.config.retry_failed_subtasks,
            "auto_planning": self.config.auto_planning_enabled,
            "subtask_details": [
                {
                    "id": subtask.id,
                    "name": subtask.name,
                    "status": subtask.status,
                    "tool": subtask.tool_name,
                    "dependencies": len(subtask.dependencies),
                    "started_at": subtask.started_at.isoformat() if subtask.started_at else None,
                    "completed_at": subtask.completed_at.isoformat() if subtask.completed_at else None,
                    "result_preview": subtask.result[:100] + "..." if subtask.result and len(subtask.result) > 100 else subtask.result,
                    "error": subtask.error
                }
                for subtask in plan.subtasks
            ]
        })
        
        return basic_status
    
    def update_configuration(self, **kwargs) -> Dict[str, Any]:
        """Update planner configuration.
        
        Args:
            **kwargs: Configuration parameters
            
        Returns:
            Updated configuration
        """
        self.config = PlannerSettings.update_config(**kwargs)
        self.planner.config = self.config
        return PlannerSettings.get_settings_dict()
    
    async def handle_task_completion_callback(self, task_uuid: str, result: str) -> None:
        """Callback for task completion events.
        
        This should be called by the TaskScheduler when tasks complete.
        
        Args:
            task_uuid: Completed task UUID
            result: Task result
        """
        await self.monitor.handle_task_completion(task_uuid, result)