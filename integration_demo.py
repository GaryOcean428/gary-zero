"""
Integration script for unified logging, monitoring and benchmarking framework.

This script demonstrates how to integrate the new framework with existing
Gary-Zero components and provides examples of usage.
"""

import asyncio
import time
from pathlib import Path

from framework.api.monitoring import router
from framework.benchmarking.analysis import BenchmarkAnalysis
from framework.benchmarking.harness import (
    BenchmarkHarness,
    BenchmarkResult,
    TaskStatus,
    TestExecutor,
)
from framework.benchmarking.reporting import BenchmarkReporter
from framework.benchmarking.tasks import StandardTasks
from framework.logging.hooks import log_operation, log_tool_execution
from framework.logging.storage import SqliteStorage

# Import the new framework components
from framework.logging.unified_logger import (
    EventType,
    LogEvent,
    LogLevel,
    get_unified_logger,
)


class GaryZeroTestExecutor(TestExecutor):
    """Test executor that integrates with Gary-Zero agent capabilities."""

    async def execute(self, test_case, config):
        """Execute a test case using Gary-Zero agent."""
        start_time = time.time()

        # Log test start
        logger = get_unified_logger()
        await logger.log_event(
            LogEvent(
                event_type=EventType.TASK_CREATED,
                level=LogLevel.INFO,
                message=f"Starting task execution: {test_case.name}",
                metadata={
                    "task_id": test_case.task_id,
                    "task_type": test_case.task_type.value,
                    "configuration": config,
                },
            )
        )

        try:
            # Simulate different task types
            if test_case.task_type.value == "summarization":
                result = await self._execute_summarization_task(test_case, config)
            elif test_case.task_type.value == "code_generation":
                result = await self._execute_code_generation_task(test_case, config)
            else:
                # Default execution
                result = await self._execute_generic_task(test_case, config)

            # Log successful completion
            await logger.log_event(
                LogEvent(
                    event_type=EventType.TASK_COMPLETED,
                    level=LogLevel.INFO,
                    message=f"Task completed successfully: {test_case.name}",
                    duration_ms=(time.time() - start_time) * 1000,
                    metadata={
                        "task_id": test_case.task_id,
                        "score": result.score,
                        "configuration": config,
                    },
                )
            )

            return result

        except Exception as e:
            # Log failure
            await logger.log_event(
                LogEvent(
                    event_type=EventType.TASK_FAILED,
                    level=LogLevel.ERROR,
                    message=f"Task failed: {test_case.name}",
                    error_message=str(e),
                    duration_ms=(time.time() - start_time) * 1000,
                    metadata={"task_id": test_case.task_id, "configuration": config},
                )
            )

            # Return failed result
            return BenchmarkResult(
                task_id=test_case.task_id,
                run_id=f"failed_{int(start_time)}",
                timestamp=start_time,
                status=TaskStatus.FAILED,
                duration_seconds=time.time() - start_time,
                error_message=str(e),
                configuration=config,
            )

    async def _execute_summarization_task(self, test_case, config):
        """Execute a summarization task."""
        # Simulate text processing
        await asyncio.sleep(0.2)

        # Simulate scoring based on expected output
        base_score = 0.8
        if config.get("model") == "gpt-4":
            base_score = 0.9
        elif config.get("model") == "local-model":
            base_score = 0.7

        return BenchmarkResult(
            task_id=test_case.task_id,
            run_id=f"sum_{int(time.time())}",
            timestamp=time.time(),
            status=TaskStatus.COMPLETED,
            duration_seconds=0.2,
            score=base_score,
            scores={
                "accuracy": base_score + 0.05,
                "completeness": base_score,
                "conciseness": base_score - 0.05,
            },
            output_data={"summary": "Generated summary text...", "word_count": 120},
            configuration=config,
        )

    async def _execute_code_generation_task(self, test_case, config):
        """Execute a code generation task."""
        # Simulate code generation
        await asyncio.sleep(0.3)

        # Simulate scoring
        base_score = 0.75
        if config.get("temperature", 0.7) < 0.5:
            base_score += 0.1  # Lower temperature = better code quality

        return BenchmarkResult(
            task_id=test_case.task_id,
            run_id=f"code_{int(time.time())}",
            timestamp=time.time(),
            status=TaskStatus.COMPLETED,
            duration_seconds=0.3,
            score=base_score,
            scores={
                "correctness": base_score + 0.05,
                "code_quality": base_score,
                "documentation": base_score - 0.1,
            },
            output_data={
                "code": "def quicksort(arr): ...",
                "lines_of_code": 25,
                "tests_included": True,
            },
            configuration=config,
        )

    async def _execute_generic_task(self, test_case, config):
        """Execute a generic task."""
        await asyncio.sleep(0.15)

        return BenchmarkResult(
            task_id=test_case.task_id,
            run_id=f"generic_{int(time.time())}",
            timestamp=time.time(),
            status=TaskStatus.COMPLETED,
            duration_seconds=0.15,
            score=0.8,
            configuration=config,
        )


async def setup_comprehensive_benchmark():
    """Set up a comprehensive benchmark suite."""
    print("🔧 Setting up comprehensive benchmark suite...")

    # Create benchmark harness
    harness = BenchmarkHarness(results_dir="./logs/benchmark_results")

    # Register tasks from standard task registry
    task_registry = StandardTasks.get_all_standard_tasks()

    for task_id, task in task_registry.tasks.items():
        harness.register_test_case(task)

    print(f"✅ Registered {len(task_registry.tasks)} benchmark tasks")

    # Register executor
    harness.register_executor("gary_zero", GaryZeroTestExecutor())

    # Register different configurations for comparison
    configurations = {
        "gpt4_optimized": {
            "model": "gpt-4",
            "temperature": 0.3,
            "max_tokens": 2000,
            "top_p": 0.9,
        },
        "gpt4_creative": {
            "model": "gpt-4",
            "temperature": 0.8,
            "max_tokens": 2000,
            "top_p": 0.95,
        },
        "local_model": {
            "model": "local-model",
            "temperature": 0.5,
            "max_tokens": 1500,
            "top_p": 0.9,
        },
    }

    for config_name, config in configurations.items():
        harness.register_configuration(config_name, config)

    print(f"✅ Registered {len(configurations)} configurations")

    return harness


@log_tool_execution(tool_name="example_agent_function", user_id="demo_user")
async def example_agent_function(query: str, context: dict):
    """Example of an agent function with automatic logging."""
    # Simulate some processing
    await asyncio.sleep(0.1)

    # Use logging hooks for sub-operations
    async with log_operation(
        "knowledge_search", EventType.KNOWLEDGE_RETRIEVAL, user_id="demo_user"
    ):
        # Simulate knowledge retrieval
        await asyncio.sleep(0.05)
        results = ["result1", "result2", "result3"]

    async with log_operation(
        "response_generation", EventType.AGENT_DECISION, user_id="demo_user"
    ):
        # Simulate response generation
        await asyncio.sleep(0.08)
        response = f"Generated response for: {query}"

    return {"response": response, "sources": results, "processing_time": 0.13}


async def demonstrate_integration():
    """Demonstrate the integrated framework capabilities."""
    print("🚀 Demonstrating Unified Logging, Monitoring & Benchmarking Framework")
    print("=" * 70)

    # 1. Unified Logging Demo
    print("\n📝 1. Unified Logging Demo")
    logger = get_unified_logger()

    # Example agent operations with automatic logging
    result = await example_agent_function(
        query="What are the benefits of AI in healthcare?",
        context={"user_session": "demo_session_123"},
    )

    print(f"✅ Agent function result: {result['response'][:50]}...")

    # Manual logging examples
    await logger.log_code_execution(
        code_snippet="print('Hello, AI!')",
        language="python",
        success=True,
        duration_ms=25.5,
        output="Hello, AI!",
        user_id="demo_user",
        agent_id="demo_agent",
    )

    await logger.log_gui_action(
        action_type="click",
        element="submit_button",
        success=True,
        duration_ms=150.0,
        page_url="https://example.com/form",
        user_id="demo_user",
        agent_id="demo_agent",
    )

    # Show statistics
    stats = logger.get_statistics()
    print(
        f"✅ Logged {stats['total_events']} events across {len(stats['events_by_type'])} types"
    )

    # 2. Storage Demo
    print("\n💾 2. Persistent Storage Demo")
    storage = SqliteStorage("./logs/demo_events.db")

    # Store some events
    for i in range(5):
        event = LogEvent(
            event_type=EventType.PERFORMANCE_METRIC,
            level=LogLevel.DEBUG,
            message=f"Performance metric {i}",
            metadata={"metric_name": f"test_metric_{i}", "value": i * 10},
        )
        await storage.store_event(event)

    stored_events = await storage.get_events(limit=10)
    storage_stats = await storage.get_statistics()
    print(f"✅ Stored and retrieved {len(stored_events)} events")
    print(f"✅ Database contains {storage_stats['total_events']} total events")

    # 3. Benchmarking Demo
    print("\n📊 3. Benchmarking Demo")
    harness = await setup_comprehensive_benchmark()

    # Run a subset of tests
    test_suite = ["summarize_research_paper", "generate_sorting_algorithm"]
    config_subset = ["gpt4_optimized", "local_model"]

    print(
        f"🏃 Running benchmark suite: {len(test_suite)} tasks × {len(config_subset)} configs"
    )

    results = await harness.run_test_suite(
        task_ids=test_suite,
        config_names=config_subset,
        run_parallel=True,
        max_concurrent=2,
    )

    print(f"✅ Completed {len(results)} benchmark runs")

    # 4. Analysis and Reporting Demo
    print("\n📈 4. Analysis and Reporting Demo")

    # Generate summary analysis
    analysis = BenchmarkAnalysis.calculate_summary_stats(results)
    print(f"✅ Success rate: {analysis.get('success_rate', 0):.1%}")
    print(f"✅ Average score: {analysis.get('score_stats', {}).get('mean', 0):.3f}")

    # Generate configuration comparison
    config_comparison = BenchmarkAnalysis.compare_configurations(results)
    print(f"✅ Compared {len(config_comparison)} configurations")

    # Generate reports
    reporter = BenchmarkReporter(output_dir="./logs/reports")

    summary_report = reporter.generate_summary_report(results, "Demo Benchmark Report")
    print(f"✅ Generated summary report: {Path(summary_report).name}")

    # 5. API Endpoints Demo
    print("\n🌐 5. API Endpoints Demo")
    print(
        f"✅ Monitoring API provides {len([r for r in router.routes if hasattr(r, 'path')])} endpoints:"
    )

    for route in router.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            methods = ", ".join(route.methods) if route.methods else "GET"
            print(f"   {methods:<8} {route.path}")

    # Show timeline capability
    timeline = await logger.get_execution_timeline(user_id="demo_user")
    print(f"✅ Execution timeline contains {len(timeline)} events")

    print("\n" + "=" * 70)
    print("🎉 Integration demonstration completed successfully!")
    print("📁 Generated files saved to:")
    print("   - Logs: ./logs/")
    print("   - Benchmark results: ./logs/benchmark_results/")
    print("   - Reports: ./logs/reports/")
    print("\n📚 Ready for production integration!")


async def main():
    """Main integration demo."""
    # Ensure log directories exist
    Path("./logs").mkdir(exist_ok=True)
    Path("./logs/benchmark_results").mkdir(exist_ok=True)
    Path("./logs/reports").mkdir(exist_ok=True)

    await demonstrate_integration()


if __name__ == "__main__":
    asyncio.run(main())
