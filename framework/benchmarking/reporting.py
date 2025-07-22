"""
Benchmark reporting and visualization tools.

Provides comprehensive reporting capabilities for benchmark results,
including trend analysis, regression reports, and performance summaries.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from .harness import BenchmarkResult
from .analysis import BenchmarkAnalysis, RegressionDetector


class BenchmarkReporter:
    """Generate comprehensive benchmark reports."""
    
    def __init__(self, output_dir: str = "./benchmark_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_summary_report(self, 
                               results: List[BenchmarkResult],
                               title: str = "Benchmark Summary Report") -> str:
        """Generate a comprehensive summary report."""
        timestamp = datetime.now(timezone.utc)
        
        # Calculate summary statistics
        summary_stats = BenchmarkAnalysis.calculate_summary_stats(results)
        
        # Generate configuration comparison
        config_comparison = BenchmarkAnalysis.compare_configurations(results)
        
        # Create report
        report = {
            "title": title,
            "timestamp": timestamp.isoformat(),
            "metadata": {
                "total_results": len(results),
                "report_generation_time": timestamp.isoformat(),
                "analysis_period": {
                    "start": min(r.timestamp for r in results) if results else None,
                    "end": max(r.timestamp for r in results) if results else None
                }
            },
            "summary_statistics": summary_stats,
            "configuration_comparison": config_comparison,
            "task_breakdown": self._generate_task_breakdown(results),
            "recommendations": self._generate_recommendations(results, summary_stats)
        }
        
        # Save report
        report_file = self.output_dir / f"summary_report_{int(timestamp.timestamp())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return str(report_file)
    
    def generate_regression_report(self,
                                  baseline_results: List[BenchmarkResult],
                                  current_results: List[BenchmarkResult],
                                  title: str = "Regression Analysis Report") -> str:
        """Generate a regression analysis report."""
        timestamp = datetime.now(timezone.utc)
        
        # Detect regressions
        detector = RegressionDetector()
        alerts = detector.detect_regressions(baseline_results, current_results)
        
        # Analyze stability
        stability_analysis = detector.analyze_stability(current_results)
        
        # Create report
        report = {
            "title": title,
            "timestamp": timestamp.isoformat(),
            "metadata": {
                "baseline_results": len(baseline_results),
                "current_results": len(current_results),
                "detection_thresholds": {
                    "score_threshold": detector.score_threshold,
                    "duration_threshold": detector.duration_threshold
                }
            },
            "regression_alerts": [
                {
                    "task_id": alert.task_id,
                    "metric": alert.metric,
                    "current_value": alert.current_value,
                    "baseline_value": alert.baseline_value,
                    "change_percent": alert.change_percent,
                    "severity": alert.severity,
                    "timestamp": alert.timestamp
                }
                for alert in alerts
            ],
            "stability_analysis": stability_analysis,
            "summary": {
                "total_alerts": len(alerts),
                "alerts_by_severity": {
                    "severe": len([a for a in alerts if a.severity == "severe"]),
                    "moderate": len([a for a in alerts if a.severity == "moderate"]),
                    "minor": len([a for a in alerts if a.severity == "minor"])
                },
                "most_affected_tasks": self._get_most_affected_tasks(alerts)
            }
        }
        
        # Save report
        report_file = self.output_dir / f"regression_report_{int(timestamp.timestamp())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return str(report_file)
    
    def generate_trend_report(self,
                             results: List[BenchmarkResult],
                             window_size: int = 10,
                             title: str = "Performance Trend Analysis") -> str:
        """Generate a trend analysis report."""
        timestamp = datetime.now(timezone.utc)
        
        # Analyze trends
        trend_analysis = BenchmarkAnalysis.analyze_trends(results, window_size)
        
        # Group by task for detailed analysis
        task_results = {}
        for result in results:
            if result.task_id not in task_results:
                task_results[result.task_id] = []
            task_results[result.task_id].append(result)
        
        task_trends = {}
        for task_id, task_result_list in task_results.items():
            task_trends[task_id] = BenchmarkAnalysis.analyze_trends(task_result_list, window_size)
        
        # Create report
        report = {
            "title": title,
            "timestamp": timestamp.isoformat(),
            "metadata": {
                "total_results": len(results),
                "window_size": window_size,
                "analysis_period": {
                    "start": min(r.timestamp for r in results) if results else None,
                    "end": max(r.timestamp for r in results) if results else None
                }
            },
            "overall_trends": trend_analysis,
            "task_specific_trends": task_trends,
            "insights": self._generate_trend_insights(trend_analysis, task_trends)
        }
        
        # Save report
        report_file = self.output_dir / f"trend_report_{int(timestamp.timestamp())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return str(report_file)
    
    def _generate_task_breakdown(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Generate task-specific breakdown."""
        task_breakdown = {}
        
        for result in results:
            task_id = result.task_id
            if task_id not in task_breakdown:
                task_breakdown[task_id] = {
                    "total_runs": 0,
                    "successful_runs": 0,
                    "failed_runs": 0,
                    "scores": [],
                    "durations": []
                }
            
            breakdown = task_breakdown[task_id]
            breakdown["total_runs"] += 1
            
            if result.status.value == "completed":
                breakdown["successful_runs"] += 1
                if result.score is not None:
                    breakdown["scores"].append(result.score)
                breakdown["durations"].append(result.duration_seconds)
            else:
                breakdown["failed_runs"] += 1
        
        # Calculate statistics for each task
        for task_id, breakdown in task_breakdown.items():
            if breakdown["scores"]:
                breakdown["avg_score"] = sum(breakdown["scores"]) / len(breakdown["scores"])
                breakdown["min_score"] = min(breakdown["scores"])
                breakdown["max_score"] = max(breakdown["scores"])
            
            if breakdown["durations"]:
                breakdown["avg_duration"] = sum(breakdown["durations"]) / len(breakdown["durations"])
                breakdown["min_duration"] = min(breakdown["durations"])
                breakdown["max_duration"] = max(breakdown["durations"])
            
            breakdown["success_rate"] = breakdown["successful_runs"] / breakdown["total_runs"]
            
            # Clean up raw data arrays for cleaner JSON
            del breakdown["scores"]
            del breakdown["durations"]
        
        return task_breakdown
    
    def _generate_recommendations(self, 
                                 results: List[BenchmarkResult],
                                 summary_stats: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on results."""
        recommendations = []
        
        if not summary_stats or "error" in summary_stats:
            recommendations.append("No successful results available for analysis.")
            return recommendations
        
        success_rate = summary_stats.get("success_rate", 0)
        if success_rate < 0.8:
            recommendations.append(f"Success rate is low ({success_rate:.1%}). Investigate failing test cases.")
        
        score_stats = summary_stats.get("score_stats", {})
        avg_score = score_stats.get("mean", 0)
        if avg_score < 0.7:
            recommendations.append(f"Average score is below target ({avg_score:.2f}). Review model performance.")
        
        score_std = score_stats.get("std_dev", 0)
        if score_std > 0.15:
            recommendations.append(f"High score variability (σ={score_std:.3f}). Consider more stable configurations.")
        
        duration_stats = summary_stats.get("duration_stats", {})
        avg_duration = duration_stats.get("mean", 0)
        if avg_duration > 300:  # 5 minutes
            recommendations.append(f"Long average duration ({avg_duration:.1f}s). Optimize for performance.")
        
        return recommendations
    
    def _get_most_affected_tasks(self, alerts) -> List[Dict[str, Any]]:
        """Get tasks most affected by regressions."""
        task_alert_counts = {}
        
        for alert in alerts:
            task_id = alert.task_id
            if task_id not in task_alert_counts:
                task_alert_counts[task_id] = {"count": 0, "max_severity": "minor"}
            
            task_alert_counts[task_id]["count"] += 1
            
            # Track maximum severity
            current_severity = task_alert_counts[task_id]["max_severity"]
            if alert.severity == "severe" or (alert.severity == "moderate" and current_severity == "minor"):
                task_alert_counts[task_id]["max_severity"] = alert.severity
        
        # Sort by alert count and severity
        severity_order = {"severe": 3, "moderate": 2, "minor": 1}
        sorted_tasks = sorted(
            task_alert_counts.items(),
            key=lambda x: (x[1]["count"], severity_order[x[1]["max_severity"]]),
            reverse=True
        )
        
        return [
            {"task_id": task_id, "alert_count": info["count"], "max_severity": info["max_severity"]}
            for task_id, info in sorted_tasks[:5]  # Top 5 most affected
        ]
    
    def _generate_trend_insights(self, 
                                overall_trends: Dict[str, Any],
                                task_trends: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate insights from trend analysis."""
        insights = []
        
        # Overall insights
        if overall_trends.get("score_trend") == "declining":
            insights.append("Overall performance is declining. Review recent changes.")
        elif overall_trends.get("score_trend") == "improving":
            insights.append("Overall performance is improving. Good progress!")
        
        if overall_trends.get("duration_trend") == "slower":
            insights.append("Tasks are taking longer to complete. Performance optimization needed.")
        elif overall_trends.get("duration_trend") == "faster":
            insights.append("Task completion times are improving.")
        
        # Task-specific insights
        declining_tasks = []
        improving_tasks = []
        
        for task_id, trend in task_trends.items():
            if trend.get("score_trend") == "declining":
                declining_tasks.append(task_id)
            elif trend.get("score_trend") == "improving":
                improving_tasks.append(task_id)
        
        if declining_tasks:
            insights.append(f"Tasks showing declining performance: {', '.join(declining_tasks[:3])}")
        
        if improving_tasks:
            insights.append(f"Tasks showing improvement: {', '.join(improving_tasks[:3])}")
        
        return insights