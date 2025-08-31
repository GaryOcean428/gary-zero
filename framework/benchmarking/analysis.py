"""
Benchmark analysis and regression detection tools.

Provides statistical analysis of benchmark results and automated regression detection.
"""

import statistics
from dataclasses import dataclass
from typing import Any

from .harness import BenchmarkResult, TaskStatus


@dataclass
class RegressionAlert:
    """Alert for detected performance regression."""

    task_id: str
    metric: str
    current_value: float
    baseline_value: float
    change_percent: float
    severity: str  # "minor", "moderate", "severe"
    timestamp: float


class BenchmarkAnalysis:
    """Statistical analysis tools for benchmark results."""

    @staticmethod
    def calculate_summary_stats(results: list[BenchmarkResult]) -> dict[str, Any]:
        """Calculate summary statistics for a set of results."""
        if not results:
            return {}

        # Filter successful results
        successful = [
            r
            for r in results
            if r.status == TaskStatus.COMPLETED and r.score is not None
        ]

        if not successful:
            return {"error": "No successful results to analyze"}

        scores = [r.score for r in successful]
        durations = [r.duration_seconds for r in successful]

        return {
            "total_runs": len(results),
            "successful_runs": len(successful),
            "success_rate": len(successful) / len(results),
            "score_stats": {
                "mean": statistics.mean(scores),
                "median": statistics.median(scores),
                "std_dev": statistics.stdev(scores) if len(scores) > 1 else 0,
                "min": min(scores),
                "max": max(scores),
            },
            "duration_stats": {
                "mean": statistics.mean(durations),
                "median": statistics.median(durations),
                "std_dev": statistics.stdev(durations) if len(durations) > 1 else 0,
                "min": min(durations),
                "max": max(durations),
            },
        }

    @staticmethod
    def compare_configurations(
        results: list[BenchmarkResult], config_field: str = "config_name"
    ) -> dict[str, Any]:
        """Compare performance across different configurations."""
        config_results = {}

        for result in results:
            if result.status != TaskStatus.COMPLETED or result.score is None:
                continue

            config_name = result.configuration.get(config_field, "unknown")
            if config_name not in config_results:
                config_results[config_name] = []
            config_results[config_name].append(result)

        comparison = {}
        for config_name, config_results_list in config_results.items():
            comparison[config_name] = BenchmarkAnalysis.calculate_summary_stats(
                config_results_list
            )

        return comparison

    @staticmethod
    def analyze_trends(
        results: list[BenchmarkResult], window_size: int = 10
    ) -> dict[str, Any]:
        """Analyze performance trends over time."""
        if len(results) < window_size:
            return {"error": "Insufficient data for trend analysis"}

        # Sort by timestamp
        sorted_results = sorted(results, key=lambda r: r.timestamp)

        # Filter successful results
        successful = [
            r
            for r in sorted_results
            if r.status == TaskStatus.COMPLETED and r.score is not None
        ]

        if len(successful) < window_size:
            return {"error": "Insufficient successful results for trend analysis"}

        # Calculate moving averages
        moving_averages = []
        for i in range(len(successful) - window_size + 1):
            window_results = successful[i : i + window_size]
            avg_score = statistics.mean(r.score for r in window_results)
            avg_duration = statistics.mean(r.duration_seconds for r in window_results)

            moving_averages.append(
                {
                    "timestamp": window_results[-1].timestamp,
                    "avg_score": avg_score,
                    "avg_duration": avg_duration,
                    "window_start": i,
                    "window_end": i + window_size - 1,
                }
            )

        # Calculate trend direction
        if len(moving_averages) >= 2:
            first_avg = moving_averages[0]["avg_score"]
            last_avg = moving_averages[-1]["avg_score"]
            score_trend = (
                "improving"
                if last_avg > first_avg
                else "declining" if last_avg < first_avg else "stable"
            )

            first_duration = moving_averages[0]["avg_duration"]
            last_duration = moving_averages[-1]["avg_duration"]
            duration_trend = (
                "faster"
                if last_duration < first_duration
                else "slower" if last_duration > first_duration else "stable"
            )
        else:
            score_trend = "insufficient_data"
            duration_trend = "insufficient_data"

        return {
            "window_size": window_size,
            "data_points": len(moving_averages),
            "score_trend": score_trend,
            "duration_trend": duration_trend,
            "moving_averages": moving_averages,
        }


class RegressionDetector:
    """Automated regression detection for benchmark results."""

    def __init__(
        self,
        score_threshold: float = 0.05,  # 5% degradation
        duration_threshold: float = 0.10,  # 10% slower
        min_baseline_samples: int = 5,
    ):
        self.score_threshold = score_threshold
        self.duration_threshold = duration_threshold
        self.min_baseline_samples = min_baseline_samples

    def detect_regressions(
        self,
        baseline_results: list[BenchmarkResult],
        current_results: list[BenchmarkResult],
    ) -> list[RegressionAlert]:
        """Detect regressions by comparing current results to baseline."""
        alerts = []

        # Group results by task_id
        baseline_by_task = self._group_by_task(baseline_results)
        current_by_task = self._group_by_task(current_results)

        for task_id in current_by_task:
            if task_id not in baseline_by_task:
                continue  # No baseline to compare against

            baseline_task_results = baseline_by_task[task_id]
            current_task_results = current_by_task[task_id]

            if len(baseline_task_results) < self.min_baseline_samples:
                continue  # Insufficient baseline data

            # Detect score regressions
            score_alerts = self._detect_metric_regression(
                task_id,
                "score",
                baseline_task_results,
                current_task_results,
                self.score_threshold,
                lower_is_worse=True,
            )
            alerts.extend(score_alerts)

            # Detect duration regressions (higher duration is worse)
            duration_alerts = self._detect_metric_regression(
                task_id,
                "duration_seconds",
                baseline_task_results,
                current_task_results,
                self.duration_threshold,
                lower_is_worse=False,
            )
            alerts.extend(duration_alerts)

        return alerts

    def _group_by_task(
        self, results: list[BenchmarkResult]
    ) -> dict[str, list[BenchmarkResult]]:
        """Group results by task_id."""
        grouped = {}
        for result in results:
            if result.status == TaskStatus.COMPLETED:
                if result.task_id not in grouped:
                    grouped[result.task_id] = []
                grouped[result.task_id].append(result)
        return grouped

    def _detect_metric_regression(
        self,
        task_id: str,
        metric: str,
        baseline_results: list[BenchmarkResult],
        current_results: list[BenchmarkResult],
        threshold: float,
        lower_is_worse: bool,
    ) -> list[RegressionAlert]:
        """Detect regression for a specific metric."""
        alerts = []

        # Extract metric values
        if metric == "score":
            baseline_values = [r.score for r in baseline_results if r.score is not None]
            current_values = [r.score for r in current_results if r.score is not None]
        elif metric == "duration_seconds":
            baseline_values = [r.duration_seconds for r in baseline_results]
            current_values = [r.duration_seconds for r in current_results]
        else:
            return alerts  # Unknown metric

        if not baseline_values or not current_values:
            return alerts

        # Calculate baseline and current averages
        baseline_avg = statistics.mean(baseline_values)
        current_avg = statistics.mean(current_values)

        # Calculate change percentage
        if baseline_avg == 0:
            return alerts  # Avoid division by zero

        change_percent = (current_avg - baseline_avg) / baseline_avg

        # Check for regression
        is_regression = False
        if lower_is_worse:
            # For metrics where lower values are worse (e.g., accuracy scores)
            is_regression = change_percent < -threshold
        else:
            # For metrics where higher values are worse (e.g., duration)
            is_regression = change_percent > threshold

        if is_regression:
            # Determine severity
            abs_change = abs(change_percent)
            if abs_change >= 0.20:  # 20% or more
                severity = "severe"
            elif abs_change >= 0.10:  # 10-20%
                severity = "moderate"
            else:
                severity = "minor"

            alert = RegressionAlert(
                task_id=task_id,
                metric=metric,
                current_value=current_avg,
                baseline_value=baseline_avg,
                change_percent=change_percent,
                severity=severity,
                timestamp=max(r.timestamp for r in current_results),
            )
            alerts.append(alert)

        return alerts

    def analyze_stability(self, results: list[BenchmarkResult]) -> dict[str, Any]:
        """Analyze result stability over time."""
        task_results = self._group_by_task(results)

        stability_analysis = {}

        for task_id, task_result_list in task_results.items():
            if len(task_result_list) < 3:
                continue  # Need at least 3 results for stability analysis

            # Sort by timestamp
            sorted_results = sorted(task_result_list, key=lambda r: r.timestamp)

            # Calculate score stability
            scores = [r.score for r in sorted_results if r.score is not None]
            if scores:
                score_cv = (
                    statistics.stdev(scores) / statistics.mean(scores)
                    if len(scores) > 1
                    else 0
                )
            else:
                score_cv = None

            # Calculate duration stability
            durations = [r.duration_seconds for r in sorted_results]
            duration_cv = (
                statistics.stdev(durations) / statistics.mean(durations)
                if len(durations) > 1
                else 0
            )

            # Classify stability
            if score_cv is not None:
                if score_cv < 0.05:
                    score_stability = "very_stable"
                elif score_cv < 0.10:
                    score_stability = "stable"
                elif score_cv < 0.20:
                    score_stability = "moderate"
                else:
                    score_stability = "unstable"
            else:
                score_stability = "no_data"

            if duration_cv < 0.10:
                duration_stability = "very_stable"
            elif duration_cv < 0.20:
                duration_stability = "stable"
            elif duration_cv < 0.30:
                duration_stability = "moderate"
            else:
                duration_stability = "unstable"

            stability_analysis[task_id] = {
                "sample_size": len(sorted_results),
                "score_coefficient_of_variation": score_cv,
                "duration_coefficient_of_variation": duration_cv,
                "score_stability": score_stability,
                "duration_stability": duration_stability,
                "time_span_days": (
                    sorted_results[-1].timestamp - sorted_results[0].timestamp
                )
                / 86400,
            }

        return stability_analysis
