"""Planning tool that provides hierarchical planning capabilities to agents.

This tool integrates the hierarchical planner with the existing agent framework,
allowing agents to create, execute, and monitor complex multi-step plans.
"""

import logging

from framework.helpers.enhanced_scheduler import EnhancedHierarchicalScheduler
from framework.helpers.hierarchical_planner import PlanningConfig, PlanStatus
from framework.helpers.planner_config import PlannerSettings

# Defer heavy imports to avoid circular dependencies
try:
    from framework.helpers.tool import Response, Tool

    _TOOL_AVAILABLE = True
except ImportError:
    _TOOL_AVAILABLE = False
    Tool = object
    Response = dict

logger = logging.getLogger(__name__)


class PlanningTool(Tool if _TOOL_AVAILABLE else object):
    """Tool for creating and managing hierarchical plans."""

    def __init__(self, *args, **kwargs):
        if _TOOL_AVAILABLE:
            super().__init__(*args, **kwargs)
        self.enhanced_scheduler = EnhancedHierarchicalScheduler()

    async def execute(self, **kwargs) -> Response:
        """Execute planning tool methods.

        Args:
            **kwargs: Method arguments

        Returns:
            Response with method result
        """
        if not _TOOL_AVAILABLE:
            return {"message": "Tool framework not available", "break_loop": False}

        if self.method == "create_plan":
            return await self.create_plan(**kwargs)
        elif self.method == "execute_plan":
            return await self.execute_plan(**kwargs)
        elif self.method == "get_plan_status":
            return await self.get_plan_status(**kwargs)
        elif self.method == "list_plans":
            return await self.list_plans(**kwargs)
        elif self.method == "configure_planner":
            return await self.configure_planner(**kwargs)
        elif self.method == "cancel_plan":
            return await self.cancel_plan(**kwargs)
        else:
            return Response(
                message=f"Unknown planning method: {self.method}", break_loop=False
            )

    async def create_plan(self, **kwargs) -> Response:
        """Create a new hierarchical plan for a given objective.

        Args:
            objective: The high-level objective to achieve
            auto_execute: Whether to automatically start plan execution (default: True)

        Returns:
            Response with plan creation result
        """
        objective = kwargs.get("objective")
        auto_execute = kwargs.get("auto_execute", True)

        if not objective:
            return Response(
                message="Objective is required to create a plan", break_loop=False
            )

        try:
            # Create the plan with enhanced scheduler
            context_id = (
                self.agent.context.id if self.agent and self.agent.context else None
            )
            plan = self.enhanced_scheduler.create_and_execute_plan(
                objective, context_id, auto_execute
            )

            # Prepare response
            response_message = (
                f"Created hierarchical plan '{plan.id}' for objective: {objective}\n\n"
            )
            response_message += f"Plan contains {len(plan.subtasks)} subtasks:\n"

            for i, subtask in enumerate(plan.subtasks, 1):
                response_message += (
                    f"{i}. {subtask.name} ({subtask.tool_name or 'auto-select'})\n"
                )
                response_message += f"   {subtask.description}\n"
                if subtask.dependencies:
                    deps = [
                        f"#{j + 1}"
                        for j, s in enumerate(plan.subtasks)
                        if s.id in subtask.dependencies
                    ]
                    response_message += f"   Dependencies: {', '.join(deps)}\n"
                response_message += "\n"

            if auto_execute and plan.status == PlanStatus.IN_PROGRESS:
                response_message += "✅ Plan execution started automatically.\n"
                response_message += f"Use 'get_plan_status' with plan_id '{plan.id}' to monitor progress.\n"
                response_message += "Enhanced features: evaluation loops, automatic retry on failures.\n"
            else:
                response_message += (
                    f"Use 'execute_plan' with plan_id '{plan.id}' to start execution."
                )

            return Response(message=response_message, break_loop=False)

        except Exception as e:
            logger.error(f"Error creating plan: {str(e)}")
            return Response(
                message=f"Failed to create plan: {str(e)}", break_loop=False
            )

    async def execute_plan(self, **kwargs) -> Response:
        """Execute an existing hierarchical plan.

        Args:
            plan_id: The ID of the plan to execute

        Returns:
            Response with execution result
        """
        plan_id = kwargs.get("plan_id")

        if not plan_id:
            return Response(
                message="Plan ID is required to execute a plan", break_loop=False
            )

        try:
            plan = self.enhanced_scheduler.planner.get_plan(plan_id)
            if not plan:
                return Response(message=f"Plan not found: {plan_id}", break_loop=False)

            if plan.status == PlanStatus.IN_PROGRESS:
                return Response(
                    message=f"Plan {plan_id} is already executing", break_loop=False
                )

            if plan.status == PlanStatus.COMPLETED:
                return Response(
                    message=f"Plan {plan_id} has already been completed",
                    break_loop=False,
                )

            # Start enhanced plan execution
            success = self.enhanced_scheduler.execute_plan_enhanced(plan_id)

            if success:
                return Response(
                    message=f"🚀 Started enhanced execution of plan '{plan_id}' ({plan.objective})\n"
                    f"Plan contains {len(plan.subtasks)} subtasks.\n"
                    f"Features enabled:\n"
                    f"  • Intelligent task scheduling based on dependencies\n"
                    f"  • Automatic output evaluation and quality scoring\n"
                    f"  • Dynamic plan adjustment on failures\n"
                    f"  • Alternative tool retry mechanisms\n\n"
                    f"Use 'get_plan_status' to monitor progress.",
                    break_loop=False,
                )
            else:
                return Response(
                    message=f"Failed to start execution of plan {plan_id}",
                    break_loop=False,
                )

        except Exception as e:
            logger.error(f"Error executing plan: {str(e)}")
            return Response(
                message=f"Failed to execute plan: {str(e)}", break_loop=False
            )

    async def get_plan_status(self, **kwargs) -> Response:
        """Get the status and progress of a plan.

        Args:
            plan_id: The ID of the plan to check
            detailed: Whether to include detailed subtask information (default: True)

        Returns:
            Response with plan status information
        """
        plan_id = kwargs.get("plan_id")
        detailed = kwargs.get("detailed", True)

        if not plan_id:
            return Response(
                message="Plan ID is required to get plan status", break_loop=False
            )

        try:
            progress = self.enhanced_scheduler.get_enhanced_plan_status(plan_id)
            if not progress:
                return Response(message=f"Plan not found: {plan_id}", break_loop=False)

            # Build enhanced status message
            message = f"📊 Enhanced Plan Status: {plan_id}\n"
            message += f"Objective: {progress['objective']}\n"
            message += f"Status: {progress['status']}\n"
            message += f"Progress: {progress['completed_subtasks']}/{progress['total_subtasks']} subtasks completed\n"

            if progress["failed_subtasks"] > 0:
                message += f"⚠️  Failed subtasks: {progress['failed_subtasks']}\n"

            message += f"Created: {progress['created_at']}\n"
            message += f"Updated: {progress['updated_at']}\n"

            # Enhanced features status
            message += "\n🔧 Enhanced Features:\n"
            message += f"  • Evaluation: {'✅ Enabled' if progress.get('evaluation_enabled') else '❌ Disabled'}\n"
            message += f"  • Auto-retry: {'✅ Enabled' if progress.get('retry_enabled') else '❌ Disabled'}\n"
            message += f"  • Auto-planning: {'✅ Enabled' if progress.get('auto_planning') else '❌ Disabled'}\n"

            if detailed and progress.get("subtask_details"):
                message += "\n📝 Subtask Details:\n"
                for i, subtask in enumerate(progress["subtask_details"], 1):
                    status_icon = {
                        "pending": "⏳",
                        "in_progress": "🔄",
                        "completed": "✅",
                        "failed": "❌",
                        "skipped": "⏭️",
                    }.get(subtask["status"], "❓")

                    message += (
                        f"{i}. {status_icon} {subtask['name']} ({subtask['status']})\n"
                    )
                    message += f"   Tool: {subtask['tool'] or 'auto-select'}\n"

                    if subtask["dependencies"] > 0:
                        message += f"   Dependencies: {subtask['dependencies']}\n"

                    if subtask["status"] == "completed" and subtask["result_preview"]:
                        message += f"   Result: {subtask['result_preview']}\n"
                    elif subtask["status"] == "failed" and subtask["error"]:
                        message += f"   Error: {subtask['error']}\n"

                    if subtask["started_at"]:
                        message += f"   Started: {subtask['started_at']}\n"
                    if subtask["completed_at"]:
                        message += f"   Completed: {subtask['completed_at']}\n"

                    message += "\n"

            if progress["is_complete"]:
                message += "🎉 Plan execution completed successfully!"

            return Response(message=message, break_loop=False)

        except Exception as e:
            logger.error(f"Error getting plan status: {str(e)}")
            return Response(
                message=f"Failed to get plan status: {str(e)}", break_loop=False
            )

    async def list_plans(self, **kwargs) -> Response:
        """List all active plans.

        Args:
            status_filter: Optional status filter (pending, in_progress, completed, failed)

        Returns:
            Response with list of plans
        """
        status_filter = kwargs.get("status_filter")

        try:
            plans = []
            for plan_id, plan in self.enhanced_scheduler.planner.active_plans.items():
                if status_filter and plan.status != status_filter:
                    continue

                progress = self.enhanced_scheduler.get_enhanced_plan_status(plan_id)
                if progress:
                    plans.append(
                        {
                            "plan_id": plan_id,
                            "objective": progress["objective"],
                            "status": progress["status"],
                            "progress": f"{progress['completed_subtasks']}/{progress['total_subtasks']}",
                            "created_at": progress["created_at"],
                            "enhanced": True,
                        }
                    )

            if not plans:
                filter_msg = f" with status '{status_filter}'" if status_filter else ""
                return Response(message=f"No plans found{filter_msg}", break_loop=False)

            message = f"📋 Active Enhanced Plans ({len(plans)} found):\n\n"
            for plan in plans:
                status_icon = {
                    "pending": "⏳",
                    "in_progress": "🔄",
                    "completed": "✅",
                    "failed": "❌",
                    "cancelled": "🚫",
                }.get(plan["status"], "❓")

                message += f"{status_icon} ID: {plan['plan_id']}\n"
                message += f"  Objective: {plan['objective']}\n"
                message += f"  Status: {plan['status']} ({plan['progress']})\n"
                message += f"  Created: {plan['created_at']}\n"
                message += f"  Enhanced: {'✅' if plan.get('enhanced') else '❌'}\n\n"

            return Response(message=message, break_loop=False)

        except Exception as e:
            logger.error(f"Error listing plans: {str(e)}")
            return Response(message=f"Failed to list plans: {str(e)}", break_loop=False)

    async def configure_planner(self, **kwargs) -> Response:
        """Configure planner settings.

        Args:
            auto_planning_enabled: Enable/disable automatic planning
            max_recursion_depth: Maximum recursion depth for planning
            model_name: LLM model to use for planning
            max_subtasks: Maximum number of subtasks per plan
            verification_enabled: Enable/disable result verification
            retry_failed_subtasks: Enable/disable retry of failed subtasks

        Returns:
            Response with configuration result
        """
        try:
            config_updates = {}

            # Validate and collect configuration updates
            for key in [
                "auto_planning_enabled",
                "max_recursion_depth",
                "model_name",
                "max_subtasks",
                "verification_enabled",
                "retry_failed_subtasks",
            ]:
                if key in kwargs:
                    config_updates[key] = kwargs[key]

            if not config_updates:
                # Return current configuration
                config = PlannerSettings.get_settings_dict()
                message = "🔧 Current Enhanced Planner Configuration:\n"
                message += f"Auto Planning: {'✅' if config['auto_planning_enabled'] else '❌'}\n"
                message += f"Max Recursion Depth: {config['max_recursion_depth']}\n"
                message += f"Model: {config['model_name']}\n"
                message += f"Max Subtasks: {config['max_subtasks']}\n"
                message += f"Verification: {'✅' if config['verification_enabled'] else '❌'}\n"
                message += f"Retry Failed: {'✅' if config['retry_failed_subtasks'] else '❌'}\n"

                return Response(message=message, break_loop=False)

            # Validate configuration
            errors = PlannerSettings.validate_config(config_updates)
            if errors:
                error_msg = "Configuration validation errors:\n"
                for field, error in errors.items():
                    error_msg += f"  • {field}: {error}\n"
                return Response(message=error_msg, break_loop=False)

            # Update configuration
            updated_config = self.enhanced_scheduler.update_configuration(
                **config_updates
            )

            message = "✅ Enhanced planner configuration updated:\n"
            for key, value in config_updates.items():
                emoji = (
                    "✅"
                    if isinstance(value, bool) and value
                    else "❌" if isinstance(value, bool) else "🔧"
                )
                message += f"  {emoji} {key}: {value}\n"

            return Response(message=message, break_loop=False)

        except Exception as e:
            logger.error(f"Error configuring planner: {str(e)}")
            return Response(
                message=f"Failed to configure planner: {str(e)}", break_loop=False
            )

    async def cancel_plan(self, **kwargs) -> Response:
        """Cancel an active plan.

        Args:
            plan_id: The ID of the plan to cancel

        Returns:
            Response with cancellation result
        """
        plan_id = kwargs.get("plan_id")

        if not plan_id:
            return Response(
                message="Plan ID is required to cancel a plan", break_loop=False
            )

        try:
            plan = self.enhanced_scheduler.planner.get_plan(plan_id)
            if not plan:
                return Response(message=f"Plan not found: {plan_id}", break_loop=False)

            if plan.status == PlanStatus.COMPLETED:
                return Response(
                    message=f"Cannot cancel completed plan: {plan_id}", break_loop=False
                )

            if plan.status == PlanStatus.CANCELLED:
                return Response(
                    message=f"Plan {plan_id} is already cancelled", break_loop=False
                )

            # Mark plan as cancelled
            plan.status = PlanStatus.CANCELLED

            # Cancel any running tasks in TaskScheduler
            await self._cancel_plan_tasks(plan_id)

            return Response(
                message=f"🚫 Plan {plan_id} has been cancelled", break_loop=False
            )

        except Exception as e:
            logger.error(f"Error cancelling plan: {str(e)}")
            return Response(
                message=f"Failed to cancel plan: {str(e)}", break_loop=False
            )

    async def create_plan(self, **kwargs) -> Response:
        """Create a new hierarchical plan for a given objective.

        Args:
            objective: The high-level objective to achieve
            auto_execute: Whether to automatically start plan execution (default: False)

        Returns:
            Response with plan creation result
        """
        objective = kwargs.get("objective")
        auto_execute = kwargs.get("auto_execute", False)

        if not objective:
            return Response(
                message="Objective is required to create a plan", break_loop=False
            )

        try:
            # Create the plan
            context_id = (
                self.agent.context.id if self.agent and self.agent.context else None
            )
            plan = self.planner.create_plan(objective, context_id)

            # Prepare response
            plan_info = {
                "plan_id": plan.id,
                "objective": plan.objective,
                "status": plan.status,
                "subtasks": [
                    {
                        "id": subtask.id,
                        "name": subtask.name,
                        "description": subtask.description,
                        "tool_name": subtask.tool_name,
                        "dependencies": subtask.dependencies,
                        "status": subtask.status,
                    }
                    for subtask in plan.subtasks
                ],
                "created_at": plan.created_at.isoformat(),
            }

            response_message = (
                f"Created hierarchical plan '{plan.id}' for objective: {objective}\n\n"
            )
            response_message += f"Plan contains {len(plan.subtasks)} subtasks:\n"

            for i, subtask in enumerate(plan.subtasks, 1):
                response_message += (
                    f"{i}. {subtask.name} ({subtask.tool_name or 'auto-select'})\n"
                )
                response_message += f"   {subtask.description}\n"
                if subtask.dependencies:
                    deps = [
                        f"#{j + 1}"
                        for j, s in enumerate(plan.subtasks)
                        if s.id in subtask.dependencies
                    ]
                    response_message += f"   Dependencies: {', '.join(deps)}\n"
                response_message += "\n"

            if auto_execute:
                execution_started = self.planner.execute_plan(plan.id)
                if execution_started:
                    response_message += "Plan execution started automatically.\n"
                    response_message += "Use 'get_plan_status' to monitor progress."
                else:
                    response_message += "Failed to start automatic execution."
            else:
                response_message += (
                    f"Use 'execute_plan' with plan_id '{plan.id}' to start execution."
                )

            return Response(message=response_message, break_loop=False)

        except Exception as e:
            logger.error(f"Error creating plan: {str(e)}")
            return Response(
                message=f"Failed to create plan: {str(e)}", break_loop=False
            )

    async def execute_plan(self, **kwargs) -> Response:
        """Execute an existing hierarchical plan.

        Args:
            plan_id: The ID of the plan to execute

        Returns:
            Response with execution result
        """
        plan_id = kwargs.get("plan_id")

        if not plan_id:
            return Response(
                message="Plan ID is required to execute a plan", break_loop=False
            )

        try:
            plan = self.planner.get_plan(plan_id)
            if not plan:
                return Response(message=f"Plan not found: {plan_id}", break_loop=False)

            if plan.status == PlanStatus.IN_PROGRESS:
                return Response(
                    message=f"Plan {plan_id} is already executing", break_loop=False
                )

            if plan.status == PlanStatus.COMPLETED:
                return Response(
                    message=f"Plan {plan_id} has already been completed",
                    break_loop=False,
                )

            # Start plan execution
            success = self.planner.execute_plan(plan_id)

            if success:
                return Response(
                    message=f"Started execution of plan '{plan_id}' ({plan.objective})\n"
                    f"Plan contains {len(plan.subtasks)} subtasks.\n"
                    f"Use 'get_plan_status' to monitor progress.",
                    break_loop=False,
                )
            else:
                return Response(
                    message=f"Failed to start execution of plan {plan_id}",
                    break_loop=False,
                )

        except Exception as e:
            logger.error(f"Error executing plan: {str(e)}")
            return Response(
                message=f"Failed to execute plan: {str(e)}", break_loop=False
            )

    async def get_plan_status(self, **kwargs) -> Response:
        """Get the status and progress of a plan.

        Args:
            plan_id: The ID of the plan to check
            detailed: Whether to include detailed subtask information (default: False)

        Returns:
            Response with plan status information
        """
        plan_id = kwargs.get("plan_id")
        detailed = kwargs.get("detailed", False)

        if not plan_id:
            return Response(
                message="Plan ID is required to get plan status", break_loop=False
            )

        try:
            progress = self.planner.get_plan_progress(plan_id)
            if not progress:
                return Response(message=f"Plan not found: {plan_id}", break_loop=False)

            plan = self.planner.get_plan(plan_id)

            # Build status message
            message = f"Plan Status: {plan_id}\n"
            message += f"Objective: {progress['objective']}\n"
            message += f"Status: {progress['status']}\n"
            message += f"Progress: {progress['completed_subtasks']}/{progress['total_subtasks']} subtasks completed\n"

            if progress["failed_subtasks"] > 0:
                message += f"Failed subtasks: {progress['failed_subtasks']}\n"

            message += f"Created: {progress['created_at']}\n"
            message += f"Updated: {progress['updated_at']}\n"

            if detailed and plan:
                message += "\nSubtask Details:\n"
                for i, subtask in enumerate(plan.subtasks, 1):
                    status_icon = {
                        "pending": "⏳",
                        "in_progress": "🔄",
                        "completed": "✅",
                        "failed": "❌",
                        "skipped": "⏭️",
                    }.get(subtask.status, "❓")

                    message += f"{i}. {status_icon} {subtask.name} ({subtask.status})\n"
                    if subtask.status == "completed" and subtask.result:
                        result_preview = (
                            subtask.result[:100] + "..."
                            if len(subtask.result) > 100
                            else subtask.result
                        )
                        message += f"   Result: {result_preview}\n"
                    elif subtask.status == "failed" and subtask.error:
                        message += f"   Error: {subtask.error}\n"

            if progress["is_complete"]:
                message += "\n🎉 Plan execution completed successfully!"

            return Response(message=message, break_loop=False)

        except Exception as e:
            logger.error(f"Error getting plan status: {str(e)}")
            return Response(
                message=f"Failed to get plan status: {str(e)}", break_loop=False
            )

    async def list_plans(self, **kwargs) -> Response:
        """List all active plans.

        Args:
            status_filter: Optional status filter (pending, in_progress, completed, failed)

        Returns:
            Response with list of plans
        """
        status_filter = kwargs.get("status_filter")

        try:
            plans = []
            for plan_id, plan in self.planner.active_plans.items():
                if status_filter and plan.status != status_filter:
                    continue

                progress = self.planner.get_plan_progress(plan_id)
                if progress:
                    plans.append(
                        {
                            "plan_id": plan_id,
                            "objective": progress["objective"],
                            "status": progress["status"],
                            "progress": f"{progress['completed_subtasks']}/{progress['total_subtasks']}",
                            "created_at": progress["created_at"],
                        }
                    )

            if not plans:
                filter_msg = f" with status '{status_filter}'" if status_filter else ""
                return Response(message=f"No plans found{filter_msg}", break_loop=False)

            message = f"Active Plans ({len(plans)} found):\n\n"
            for plan in plans:
                message += f"ID: {plan['plan_id']}\n"
                message += f"Objective: {plan['objective']}\n"
                message += f"Status: {plan['status']} ({plan['progress']})\n"
                message += f"Created: {plan['created_at']}\n\n"

            return Response(message=message, break_loop=False)

        except Exception as e:
            logger.error(f"Error listing plans: {str(e)}")
            return Response(message=f"Failed to list plans: {str(e)}", break_loop=False)

    async def configure_planner(self, **kwargs) -> Response:
        """Configure planner settings.

        Args:
            auto_planning_enabled: Enable/disable automatic planning
            max_recursion_depth: Maximum recursion depth for planning
            model_name: LLM model to use for planning
            max_subtasks: Maximum number of subtasks per plan
            verification_enabled: Enable/disable result verification

        Returns:
            Response with configuration result
        """
        try:
            config_updates = {}

            if "auto_planning_enabled" in kwargs:
                config_updates["auto_planning_enabled"] = kwargs[
                    "auto_planning_enabled"
                ]
            if "max_recursion_depth" in kwargs:
                config_updates["max_recursion_depth"] = kwargs["max_recursion_depth"]
            if "model_name" in kwargs:
                config_updates["model_name"] = kwargs["model_name"]
            if "max_subtasks" in kwargs:
                config_updates["max_subtasks"] = kwargs["max_subtasks"]
            if "verification_enabled" in kwargs:
                config_updates["verification_enabled"] = kwargs["verification_enabled"]

            if not config_updates:
                # Return current configuration
                config = self.planner.config
                message = "Current Planner Configuration:\n"
                message += f"Auto Planning: {config.auto_planning_enabled}\n"
                message += f"Max Recursion Depth: {config.max_recursion_depth}\n"
                message += f"Model: {config.model_name}\n"
                message += f"Max Subtasks: {config.max_subtasks}\n"
                message += f"Verification: {config.verification_enabled}\n"
                message += f"Retry Failed: {config.retry_failed_subtasks}\n"

                return Response(message=message, break_loop=False)

            # Update configuration
            current_config = self.planner.config.dict()
            current_config.update(config_updates)
            self.planner.config = PlanningConfig(**current_config)

            message = "Planner configuration updated:\n"
            for key, value in config_updates.items():
                message += f"{key}: {value}\n"

            return Response(message=message, break_loop=False)

        except Exception as e:
            logger.error(f"Error configuring planner: {str(e)}")
            return Response(
                message=f"Failed to configure planner: {str(e)}", break_loop=False
            )

    async def cancel_plan(self, **kwargs) -> Response:
        """Cancel an active plan.

        Args:
            plan_id: The ID of the plan to cancel

        Returns:
            Response with cancellation result
        """
        plan_id = kwargs.get("plan_id")

        if not plan_id:
            return Response(
                message="Plan ID is required to cancel a plan", break_loop=False
            )

        try:
            plan = self.planner.get_plan(plan_id)
            if not plan:
                return Response(message=f"Plan not found: {plan_id}", break_loop=False)

            if plan.status == PlanStatus.COMPLETED:
                return Response(
                    message=f"Cannot cancel completed plan: {plan_id}", break_loop=False
                )

            if plan.status == PlanStatus.CANCELLED:
                return Response(
                    message=f"Plan {plan_id} is already cancelled", break_loop=False
                )

            # Mark plan as cancelled
            plan.status = PlanStatus.CANCELLED

            # Cancel any running tasks in TaskScheduler
            await self._cancel_plan_tasks(plan_id)

            return Response(
                message=f"Plan {plan_id} has been cancelled", break_loop=False
            )

        except Exception as e:
            logger.error(f"Error cancelling plan: {str(e)}")
            return Response(
                message=f"Failed to cancel plan: {str(e)}", break_loop=False
            )

    async def _cancel_plan_tasks(self, plan_id: str):
        """Cancel any running tasks associated with a plan."""
        try:
            # Try to import TaskScheduler and cancel related tasks
            from framework.helpers.task_scheduler_backup import TaskScheduler
            
            scheduler = TaskScheduler.get()
            
            # Get all tasks that might be related to this plan
            all_tasks = scheduler.get_tasks()
            
            # Find tasks related to this plan (by UUID or metadata)  
            plan_tasks = []
            for task in all_tasks:
                # Check if task is related to this plan
                # This could be by plan_id in task metadata, description, or name
                if (plan_id in str(task.uuid) or 
                    plan_id in task.name or 
                    (hasattr(task, 'metadata') and plan_id in str(task.metadata))):
                    plan_tasks.append(task)
            
            # Cancel/stop running tasks
            cancelled_count = 0
            for task in plan_tasks:
                try:
                    if hasattr(task, 'state') and task.state == 'RUNNING':
                        # Try to update task state to cancelled/idle
                        await scheduler.update_task(task.uuid, state='IDLE')
                        cancelled_count += 1
                        logger.info(f"Cancelled running task: {task.name} ({task.uuid})")
                except Exception as e:
                    logger.warning(f"Failed to cancel task {task.uuid}: {e}")
            
            if cancelled_count > 0:
                logger.info(f"Cancelled {cancelled_count} running tasks for plan {plan_id}")
            else:
                logger.debug(f"No running tasks found for plan {plan_id}")
                
        except ImportError:
            logger.debug("TaskScheduler not available for task cancellation")
        except Exception as e:
            logger.error(f"Error cancelling plan tasks: {e}")
