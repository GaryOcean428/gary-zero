"""
Example integration of async orchestration with Gary-Zero agent system.

This example shows how to use the async orchestration system alongside
the existing agent framework for improved performance and concurrency.
"""

import asyncio
import sys
import time

sys.path.append("/home/runner/work/gary-zero/gary-zero")

from framework.helpers.async_orchestrator import get_orchestrator
from framework.helpers.enhanced_scheduler import (
    get_enhanced_scheduler,
    run_enhanced_tick,
)
from framework.helpers.orchestration_config import (
    get_config_manager,
    update_orchestration_config,
)
from framework.helpers.task_manager import TaskCategory, TaskManager


class ExampleAgentTask:
    """Example task that simulates agent work."""

    def __init__(self, task_id, title, task_type="general", agent_id=None):
        self.id = task_id
        self.title = title
        self.task_type = task_type
        self.agent_id = agent_id
        self.description = f"{task_type} task: {title}"
        self.status = "pending"
        self.created_at = time.time()


async def simulate_agent_work(task):
    """Simulate agent performing work."""
    work_times = {
        "coding": 0.4,
        "research": 0.3,
        "analysis": 0.35,
        "communication": 0.2,
        "system": 0.5,
    }

    work_time = work_times.get(task.task_type, 0.3)

    # Simulate actual agent work
    await asyncio.sleep(work_time)

    return {
        "task_id": task.id,
        "title": task.title,
        "result": f"Agent completed: {task.title}",
        "execution_time": work_time,
        "agent_id": task.agent_id,
    }


async def example_multi_agent_workflow():
    """Example of coordinated multi-agent workflow with orchestration."""
    print("🤖 MULTI-AGENT ORCHESTRATION EXAMPLE")
    print("=" * 60)

    # Configure orchestration for multiple agents
    update_orchestration_config(
        max_concurrent_tasks=8,
        default_task_timeout_seconds=30.0,
        enable_performance_monitoring=True,
    )

    # Set agent-specific configurations
    config_manager = get_config_manager()

    # Configure different agent types with appropriate limits
    agent_configs = {
        "coding_agent": {
            "max_concurrent_tasks": 3,
            "max_requests_per_minute": 40,
            "max_memory_mb": 2048.0,
        },
        "research_agent": {
            "max_concurrent_tasks": 4,
            "max_requests_per_minute": 60,
            "max_memory_mb": 1024.0,
        },
        "analysis_agent": {
            "max_concurrent_tasks": 2,
            "max_requests_per_minute": 30,
            "max_memory_mb": 1536.0,
        },
    }

    for agent_id, config in agent_configs.items():
        config_manager.set_agent_config(agent_id, config)

    # Get orchestrator
    orchestrator = await get_orchestrator()

    # Replace execution method with our agent simulation
    orchestrator._execute_managed_task = simulate_agent_work

    try:
        # Create a realistic software development workflow
        workflow_tasks = [
            # Research phase
            ExampleAgentTask(
                "req_1", "Gather user requirements", "research", "research_agent"
            ),
            ExampleAgentTask(
                "req_2", "Market research analysis", "research", "research_agent"
            ),
            ExampleAgentTask(
                "req_3", "Technical feasibility study", "research", "research_agent"
            ),
            # Design phase
            ExampleAgentTask(
                "design_1", "System architecture design", "analysis", "analysis_agent"
            ),
            ExampleAgentTask(
                "design_2", "Database schema design", "analysis", "analysis_agent"
            ),
            # Development phase
            ExampleAgentTask(
                "code_1", "Implement authentication", "coding", "coding_agent"
            ),
            ExampleAgentTask(
                "code_2", "Implement user management", "coding", "coding_agent"
            ),
            ExampleAgentTask(
                "code_3", "Implement API endpoints", "coding", "coding_agent"
            ),
            ExampleAgentTask("code_4", "Frontend components", "coding", "coding_agent"),
            # Testing and deployment
            ExampleAgentTask(
                "test_1", "Integration testing", "system", "analysis_agent"
            ),
            ExampleAgentTask(
                "deploy_1", "Production deployment", "system", "analysis_agent"
            ),
            # Documentation
            ExampleAgentTask(
                "doc_1", "API documentation", "communication", "research_agent"
            ),
            ExampleAgentTask("doc_2", "User manual", "communication", "research_agent"),
        ]

        print(f"📋 Workflow: {len(workflow_tasks)} tasks across 3 agent types")

        # Group tasks by agent
        tasks_by_agent = {}
        for task in workflow_tasks:
            agent = task.agent_id
            if agent not in tasks_by_agent:
                tasks_by_agent[agent] = []
            tasks_by_agent[agent].append(task)

        for agent, tasks in tasks_by_agent.items():
            print(f"   {agent}: {len(tasks)} tasks")

        # Execute workflow
        start_time = time.time()

        # Submit all tasks with agent assignments
        task_submissions = []
        for task in workflow_tasks:
            submission = orchestrator.submit_task(
                task,
                assigned_agent=task.agent_id,
                priority=1
                if task.task_type == "system"
                else 0,  # Higher priority for system tasks
            )
            task_submissions.append(submission)

        # Wait for all submissions to complete
        task_ids = await asyncio.gather(*task_submissions)

        print("\n⚡ Executing workflow with orchestration...")

        # Wait for all tasks to complete
        results = await asyncio.gather(
            *[orchestrator.wait_for_task(task_id, timeout=60.0) for task_id in task_ids]
        )

        execution_time = time.time() - start_time

        # Analyze results
        print("\n📊 Workflow Results:")
        print(f"   - Total tasks: {len(results)}")
        print(f"   - Execution time: {execution_time:.2f}s")
        print(f"   - Average time per task: {execution_time / len(results):.2f}s")

        # Show agent utilization
        metrics = await orchestrator.get_orchestration_metrics()
        agent_util = metrics.get("agent_utilization", {})

        print("\n🤖 Agent Utilization:")
        for agent_id, util in agent_util.items():
            print(f"   {agent_id}:")
            print(f"     - Tasks handled: {util['current_tasks']}")
            print(f"     - Max capacity: {util['max_tasks']}")
            print(f"     - Peak utilization: {util['utilization_percent']:.1f}%")

        # Performance metrics
        orchestration_metrics = metrics["orchestration_metrics"]
        print("\n📈 Performance Metrics:")
        print(f"   - Tasks submitted: {orchestration_metrics['tasks_submitted']}")
        print(f"   - Tasks completed: {orchestration_metrics['tasks_completed']}")
        print(f"   - Tasks failed: {orchestration_metrics['tasks_failed']}")
        print(
            f"   - Resource constraints hit: {orchestration_metrics['resource_constraints_hit']}"
        )

        success_rate = (
            orchestration_metrics["tasks_completed"]
            / orchestration_metrics["tasks_submitted"]
        ) * 100
        print(f"   - Success rate: {success_rate:.1f}%")

        return execution_time, len(results), success_rate

    finally:
        await orchestrator.stop()


async def example_enhanced_scheduler_integration():
    """Example of using the enhanced scheduler with orchestration."""
    print("\n📅 ENHANCED SCHEDULER INTEGRATION")
    print("=" * 60)

    # Get enhanced scheduler
    scheduler = get_enhanced_scheduler()

    print("🔧 Scheduler Integration Features:")
    print("   - Automatic async/sync mode selection")
    print("   - Performance metrics collection")
    print("   - Backward compatibility maintained")

    # Run enhanced tick
    print("\n⚡ Running enhanced scheduler tick...")

    tick_metrics = await run_enhanced_tick()

    print("📊 Tick Results:")
    print(f"   - Mode: {tick_metrics['mode']}")
    print(f"   - Tasks processed: {tick_metrics['tasks_processed']}")
    print(f"   - Concurrent tasks: {tick_metrics['concurrent_tasks']}")
    print(f"   - Execution time: {tick_metrics['execution_time']:.3f}s")
    print(f"   - Errors: {len(tick_metrics['errors'])}")

    # Get execution statistics
    stats = scheduler.get_execution_stats()
    print("\n📈 Execution Statistics:")
    print(f"   - Sync executions: {stats['sync_executions']}")
    print(f"   - Async executions: {stats['async_executions']}")
    print(f"   - Concurrent executions: {stats['concurrent_executions']}")
    print(f"   - Fallbacks to sync: {stats['fallbacks_to_sync']}")


async def example_task_manager_integration():
    """Example of integrating with the existing TaskManager."""
    print("\n📋 TASK MANAGER INTEGRATION")
    print("=" * 60)

    # Get task manager instance
    task_manager = TaskManager.get_instance()

    print("📊 Task Manager Integration:")
    print("   - Leverages existing task persistence")
    print("   - Maintains task lifecycle management")
    print("   - Adds orchestration capabilities")

    # Create some tasks using TaskManager
    tasks = []
    for i in range(3):
        task = task_manager.create_task(
            title=f"Integration Task {i + 1}",
            description=f"Example task {i + 1} for integration testing",
            category=TaskCategory.SYSTEM,
            context={"orchestration_example": True},
        )
        tasks.append(task)

    print(f"\n📋 Created {len(tasks)} tasks in TaskManager")

    # Get statistics
    stats = task_manager.get_statistics()
    print("📊 TaskManager Statistics:")
    print(f"   - Total tasks: {stats['total_tasks']}")
    print(f"   - Active tasks: {stats['active_tasks']}")
    print(f"   - Completed tasks: {stats['completed_tasks']}")

    return len(tasks)


async def main():
    """Run all integration examples."""
    print("🚀 GARY-ZERO ASYNC ORCHESTRATION INTEGRATION EXAMPLES")
    print("=" * 80)
    print("These examples demonstrate how to integrate async orchestration")
    print("with the existing Gary-Zero agent system for enhanced performance.")
    print()

    try:
        # Example 1: Multi-agent workflow
        (
            workflow_time,
            workflow_tasks,
            success_rate,
        ) = await example_multi_agent_workflow()

        # Example 2: Enhanced scheduler
        await example_enhanced_scheduler_integration()

        # Example 3: Task manager integration
        task_count = await example_task_manager_integration()

        print("\n🎉 INTEGRATION EXAMPLES COMPLETED!")
        print("=" * 80)
        print("🎯 Summary:")
        print(
            f"   ✅ Multi-agent workflow: {workflow_tasks} tasks in {workflow_time:.2f}s"
        )
        print(f"   ✅ Success rate: {success_rate:.1f}%")
        print("   ✅ Enhanced scheduler: Integrated and functional")
        print(f"   ✅ Task manager: {task_count} tasks created and managed")
        print()
        print("🔗 Integration Benefits:")
        print("   • Seamless integration with existing systems")
        print("   • Enhanced performance through concurrency")
        print("   • Maintained backward compatibility")
        print("   • Improved resource utilization")
        print("   • Robust error handling and recovery")

        return True

    except Exception as e:
        print(f"\n❌ Integration example failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
