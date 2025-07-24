"""
GAIA-style benchmarking harness for automated agent evaluation.

Provides infrastructure to run standardized tasks across different configurations
and compare results against ground truth or human-rated references.
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ..logging.unified_logger import EventType, LogEvent, LogLevel, get_unified_logger


class TaskStatus(Enum):
    """Status of a benchmark task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


class TaskType(Enum):
    """Types of benchmark tasks."""

    SUMMARIZATION = "summarization"
    CODE_GENERATION = "code_generation"
    PRESENTATION_CREATION = "presentation_creation"
    RESEARCH_ANALYSIS = "research_analysis"
    PROBLEM_SOLVING = "problem_solving"
    CREATIVE_WRITING = "creative_writing"
    DATA_ANALYSIS = "data_analysis"
    TOOL_USAGE = "tool_usage"
    MULTI_STEP_REASONING = "multi_step_reasoning"
    CUSTOM = "custom"


@dataclass
class TestCase:
    """Definition of a benchmark test case."""

    task_id: str
    name: str
    description: str
    task_type: TaskType
    input_data: dict[str, Any]
    expected_output: dict[str, Any] | None = None
    ground_truth: str | None = None
    reference_files: list[str] = field(default_factory=list)
    timeout_seconds: int = 300
    max_retries: int = 0
    scoring_criteria: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Result of a benchmark test execution."""

    task_id: str
    run_id: str
    timestamp: float
    status: TaskStatus
    duration_seconds: float
    score: float | None = None
    scores: dict[str, float] = field(default_factory=dict)  # Multiple scoring criteria
    output_data: dict[str, Any] | None = None
    error_message: str | None = None
    logs: list[str] = field(default_factory=list)
    resource_usage: dict[str, float] = field(default_factory=dict)
    configuration: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)  # Generated files, outputs

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "timestamp_iso": datetime.fromtimestamp(self.timestamp, tz=UTC).isoformat(),
            "status": self.status.value,
            "duration_seconds": self.duration_seconds,
            "score": self.score,
            "scores": self.scores,
            "output_data": self.output_data,
            "error_message": self.error_message,
            "logs": self.logs,
            "resource_usage": self.resource_usage,
            "configuration": self.configuration,
            "artifacts": self.artifacts,
        }


class TestExecutor(ABC):
    """Abstract base class for test executors."""

    @abstractmethod
    async def execute(
        self, test_case: TestCase, config: dict[str, Any]
    ) -> BenchmarkResult:
        """Execute a test case and return results."""
        pass


class BenchmarkHarness:
    """
    GAIA-style benchmarking harness for comprehensive agent evaluation.

    Provides infrastructure to run standardized tasks, collect metrics,
    and compare results across different configurations.
    """

    def __init__(
        self, results_dir: str = "./benchmark_results", enable_logging: bool = True
    ):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.enable_logging = enable_logging

        if enable_logging:
            self.logger = get_unified_logger()
        else:
            self.logger = None

        self.test_cases: dict[str, TestCase] = {}
        self.executors: dict[str, TestExecutor] = {}
        self.configurations: dict[str, dict[str, Any]] = {}

        # Statistics
        self.total_runs = 0
        self.successful_runs = 0
        self.failed_runs = 0

    def register_test_case(self, test_case: TestCase) -> None:
        """Register a test case for benchmarking."""
        self.test_cases[test_case.task_id] = test_case

    def register_executor(self, name: str, executor: TestExecutor) -> None:
        """Register a test executor."""
        self.executors[name] = executor

    def register_configuration(self, name: str, config: dict[str, Any]) -> None:
        """Register a configuration for testing."""
        self.configurations[name] = config

    async def run_single_test(
        self,
        task_id: str,
        executor_name: str,
        config_name: str,
        run_id: str | None = None,
    ) -> BenchmarkResult:
        """Run a single test case."""
        if task_id not in self.test_cases:
            raise ValueError(f"Test case {task_id} not found")

        if executor_name not in self.executors:
            raise ValueError(f"Executor {executor_name} not found")

        if config_name not in self.configurations:
            raise ValueError(f"Configuration {config_name} not found")

        test_case = self.test_cases[task_id]
        executor = self.executors[executor_name]
        config = self.configurations[config_name].copy()
        config["executor_name"] = executor_name
        config["config_name"] = config_name

        if not run_id:
            run_id = f"{task_id}_{config_name}_{int(time.time())}"

        # Log test start
        if self.logger:
            await self.logger.log_event(
                LogEvent(
                    event_type=EventType.TASK_CREATED,
                    level=LogLevel.INFO,
                    message=f"Starting benchmark test: {task_id} with {config_name}",
                    metadata={
                        "task_id": task_id,
                        "executor": executor_name,
                        "configuration": config_name,
                        "run_id": run_id,
                    },
                )
            )

        start_time = time.time()

        try:
            # Execute the test
            result = await executor.execute(test_case, config)
            result.run_id = run_id
            result.configuration = config

            # Update statistics
            self.total_runs += 1
            if result.status == TaskStatus.COMPLETED:
                self.successful_runs += 1
            else:
                self.failed_runs += 1

            # Log completion
            if self.logger:
                await self.logger.log_event(
                    LogEvent(
                        event_type=EventType.TASK_COMPLETED,
                        level=LogLevel.INFO,
                        message=f"Benchmark test completed: {task_id}",
                        duration_ms=(time.time() - start_time) * 1000,
                        metadata={
                            "task_id": task_id,
                            "run_id": run_id,
                            "status": result.status.value,
                            "score": result.score,
                            "duration_seconds": result.duration_seconds,
                        },
                    )
                )

            # Save result
            await self._save_result(result)

            return result

        except Exception as e:
            # Create failed result
            result = BenchmarkResult(
                task_id=task_id,
                run_id=run_id,
                timestamp=start_time,
                status=TaskStatus.FAILED,
                duration_seconds=time.time() - start_time,
                error_message=str(e),
                configuration=config,
            )

            self.total_runs += 1
            self.failed_runs += 1

            # Log failure
            if self.logger:
                await self.logger.log_event(
                    LogEvent(
                        event_type=EventType.TASK_FAILED,
                        level=LogLevel.ERROR,
                        message=f"Benchmark test failed: {task_id}",
                        error_message=str(e),
                        metadata={
                            "task_id": task_id,
                            "run_id": run_id,
                            "executor": executor_name,
                            "configuration": config_name,
                        },
                    )
                )

            await self._save_result(result)
            return result

    async def run_test_suite(
        self,
        task_ids: list[str] | None = None,
        executor_names: list[str] | None = None,
        config_names: list[str] | None = None,
        run_parallel: bool = True,
        max_concurrent: int = 5,
    ) -> list[BenchmarkResult]:
        """Run a suite of tests across multiple configurations."""
        # Default to all registered items if not specified
        task_ids = task_ids or list(self.test_cases.keys())
        executor_names = executor_names or list(self.executors.keys())
        config_names = config_names or list(self.configurations.keys())

        # Generate all combinations
        test_combinations = []
        for task_id in task_ids:
            for executor_name in executor_names:
                for config_name in config_names:
                    test_combinations.append((task_id, executor_name, config_name))

        # Log suite start
        if self.logger:
            await self.logger.log_event(
                LogEvent(
                    event_type=EventType.SYSTEM_EVENT,
                    level=LogLevel.INFO,
                    message=f"Starting benchmark suite: {len(test_combinations)} test combinations",
                    metadata={
                        "suite_size": len(test_combinations),
                        "tasks": task_ids,
                        "executors": executor_names,
                        "configurations": config_names,
                        "parallel": run_parallel,
                        "max_concurrent": max_concurrent,
                    },
                )
            )

        results = []

        if run_parallel:
            # Run tests in parallel with concurrency limit
            semaphore = asyncio.Semaphore(max_concurrent)

            async def run_with_semaphore(combo):
                async with semaphore:
                    return await self.run_single_test(*combo)

            tasks = [run_with_semaphore(combo) for combo in test_combinations]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle exceptions
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create failed result for exception
                    task_id, executor_name, config_name = test_combinations[i]
                    failed_result = BenchmarkResult(
                        task_id=task_id,
                        run_id=f"{task_id}_{config_name}_{int(time.time())}",
                        timestamp=time.time(),
                        status=TaskStatus.FAILED,
                        duration_seconds=0,
                        error_message=str(result),
                        configuration={
                            "executor": executor_name,
                            "config": config_name,
                        },
                    )
                    final_results.append(failed_result)
                else:
                    final_results.append(result)

            results = final_results
        else:
            # Run tests sequentially
            for combo in test_combinations:
                result = await self.run_single_test(*combo)
                results.append(result)

        # Log suite completion
        if self.logger:
            successful = sum(1 for r in results if r.status == TaskStatus.COMPLETED)
            failed = len(results) - successful

            await self.logger.log_event(
                LogEvent(
                    event_type=EventType.SYSTEM_EVENT,
                    level=LogLevel.INFO,
                    message=f"Benchmark suite completed: {successful} successful, {failed} failed",
                    metadata={
                        "total_tests": len(results),
                        "successful": successful,
                        "failed": failed,
                        "success_rate": successful / len(results) if results else 0,
                    },
                )
            )

        return results

    async def _save_result(self, result: BenchmarkResult) -> None:
        """Save a benchmark result to disk."""
        result_file = self.results_dir / f"{result.run_id}.json"

        with open(result_file, "w") as f:
            json.dump(result.to_dict(), f, indent=2, default=str)

    async def load_results(
        self,
        start_time: float | None = None,
        end_time: float | None = None,
        task_ids: list[str] | None = None,
        config_names: list[str] | None = None,
    ) -> list[BenchmarkResult]:
        """Load benchmark results from disk with filtering."""
        results = []

        for result_file in self.results_dir.glob("*.json"):
            try:
                with open(result_file) as f:
                    data = json.load(f)

                # Apply filters
                if start_time and data.get("timestamp", 0) < start_time:
                    continue

                if end_time and data.get("timestamp", 0) > end_time:
                    continue

                if task_ids and data.get("task_id") not in task_ids:
                    continue

                if (
                    config_names
                    and data.get("configuration", {}).get("config_name")
                    not in config_names
                ):
                    continue

                # Convert back to BenchmarkResult
                result = BenchmarkResult(
                    task_id=data["task_id"],
                    run_id=data["run_id"],
                    timestamp=data["timestamp"],
                    status=TaskStatus(data["status"]),
                    duration_seconds=data["duration_seconds"],
                    score=data.get("score"),
                    scores=data.get("scores", {}),
                    output_data=data.get("output_data"),
                    error_message=data.get("error_message"),
                    logs=data.get("logs", []),
                    resource_usage=data.get("resource_usage", {}),
                    configuration=data.get("configuration", {}),
                    artifacts=data.get("artifacts", []),
                )

                results.append(result)

            except Exception as e:
                print(f"Error loading result file {result_file}: {e}")

        return results

    def get_statistics(self) -> dict[str, Any]:
        """Get benchmarking statistics."""
        return {
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "success_rate": self.successful_runs / self.total_runs
            if self.total_runs > 0
            else 0,
            "registered_tests": len(self.test_cases),
            "registered_executors": len(self.executors),
            "registered_configurations": len(self.configurations),
        }
