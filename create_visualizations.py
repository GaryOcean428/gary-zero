#!/usr/bin/env python3
"""
Visualization script for unified logging, monitoring & benchmarking framework.

Creates simple charts and reports to demonstrate the framework's analysis capabilities.
"""

import asyncio
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from framework.benchmarking.analysis import BenchmarkAnalysis
from framework.benchmarking.harness import BenchmarkHarness, BenchmarkResult, TaskStatus
from framework.benchmarking.tasks import StandardTasks

# Import our framework components
from framework.logging.unified_logger import (
    EventType,
    LogEvent,
    LogLevel,
    get_unified_logger,
)
from integration_demo import GaryZeroTestExecutor


def create_performance_timeline_chart(
    events: list[LogEvent], output_file: str = "performance_timeline.png"
):
    """Create a timeline chart showing performance metrics over time."""
    # Filter performance events with duration data
    perf_events = [
        e
        for e in events
        if e.duration_ms is not None
        and e.event_type
        in [EventType.TOOL_EXECUTION, EventType.CODE_EXECUTION, EventType.GUI_ACTION]
    ]

    if not perf_events:
        print("❌ No performance events with duration data found")
        return

    # Extract data
    timestamps = [datetime.fromtimestamp(e.timestamp) for e in perf_events]
    durations = [e.duration_ms for e in perf_events]
    event_types = [e.event_type.value for e in perf_events]

    # Create the plot
    plt.figure(figsize=(12, 6))

    # Color map for different event types
    colors = {
        "tool_execution": "blue",
        "code_execution": "green",
        "gui_action": "red",
        "knowledge_retrieval": "orange",
        "memory_operation": "purple",
    }

    # Plot points colored by event type
    for event_type in set(event_types):
        type_timestamps = [
            t for i, t in enumerate(timestamps) if event_types[i] == event_type
        ]
        type_durations = [
            d for i, d in enumerate(durations) if event_types[i] == event_type
        ]

        plt.scatter(
            type_timestamps,
            type_durations,
            c=colors.get(event_type, "gray"),
            label=event_type.replace("_", " ").title(),
            alpha=0.7,
            s=50,
        )

    plt.xlabel("Time")
    plt.ylabel("Duration (ms)")
    plt.title("Performance Timeline - Task Execution Duration Over Time")
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Format x-axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.gca().xaxis.set_major_locator(mdates.SecondLocator(interval=30))
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"✅ Performance timeline chart saved to {output_file}")


def create_benchmark_comparison_chart(
    results: list[BenchmarkResult], output_file: str = "benchmark_comparison.png"
):
    """Create a comparison chart of benchmark results across configurations."""
    if not results:
        print("❌ No benchmark results found")
        return

    # Group results by configuration and task
    config_data = {}
    for result in results:
        if result.status != TaskStatus.COMPLETED or result.score is None:
            continue

        config_name = result.configuration.get("config_name", "unknown")
        task_id = result.task_id

        if config_name not in config_data:
            config_data[config_name] = {}
        if task_id not in config_data[config_name]:
            config_data[config_name][task_id] = []

        config_data[config_name][task_id].append(result.score)

    if not config_data:
        print("❌ No completed benchmark results with scores found")
        return

    # Calculate averages
    config_averages = {}
    all_tasks = set()

    for config_name, tasks in config_data.items():
        config_averages[config_name] = {}
        for task_id, scores in tasks.items():
            config_averages[config_name][task_id] = sum(scores) / len(scores)
            all_tasks.add(task_id)

    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 8))

    # Prepare data for grouped bar chart
    task_names = list(all_tasks)
    config_names = list(config_data.keys())

    x = range(len(task_names))
    width = 0.8 / len(config_names)

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    for i, config_name in enumerate(config_names):
        scores = [config_averages[config_name].get(task, 0) for task in task_names]
        offset = (i - len(config_names) / 2 + 0.5) * width

        bars = ax.bar(
            [xi + offset for xi in x],
            scores,
            width,
            label=config_name,
            color=colors[i % len(colors)],
            alpha=0.8,
        )

        # Add value labels on bars
        for bar, score in zip(bars, scores, strict=False):
            if score > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.01,
                    f"{score:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

    ax.set_xlabel("Benchmark Tasks")
    ax.set_ylabel("Average Score")
    ax.set_title("Benchmark Results Comparison Across Configurations")
    ax.set_xticks(x)
    ax.set_xticklabels(
        [task.replace("_", " ").title() for task in task_names], rotation=45, ha="right"
    )
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    ax.set_ylim(0, 1.0)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"✅ Benchmark comparison chart saved to {output_file}")


def create_event_distribution_chart(
    events: list[LogEvent], output_file: str = "event_distribution.png"
):
    """Create a pie chart showing distribution of event types."""
    if not events:
        print("❌ No events found")
        return

    # Count events by type
    event_counts = {}
    for event in events:
        event_type = event.event_type.value
        event_counts[event_type] = event_counts.get(event_type, 0) + 1

    # Create the plot
    plt.figure(figsize=(10, 8))

    # Prepare data
    labels = list(event_counts.keys())
    sizes = list(event_counts.values())
    colors = plt.cm.Set3(range(len(labels)))

    # Create pie chart
    wedges, texts, autotexts = plt.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        startangle=90,
        textprops={"fontsize": 10},
    )

    # Improve readability
    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_weight("bold")

    plt.title("Distribution of Event Types", fontsize=16, fontweight="bold")
    plt.axis("equal")

    # Add total count
    total_events = sum(sizes)
    plt.figtext(0.5, 0.02, f"Total Events: {total_events}", ha="center", fontsize=12)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"✅ Event distribution chart saved to {output_file}")


def create_performance_summary_report(
    events: list[LogEvent],
    results: list[BenchmarkResult],
    output_file: str = "performance_summary.html",
):
    """Create an HTML performance summary report."""
    # Calculate statistics
    total_events = len(events)
    event_types = {}
    duration_stats = {}

    for event in events:
        event_type = event.event_type.value
        event_types[event_type] = event_types.get(event_type, 0) + 1

        if event.duration_ms is not None:
            if event_type not in duration_stats:
                duration_stats[event_type] = []
            duration_stats[event_type].append(event.duration_ms)

    # Benchmark statistics
    benchmark_stats = BenchmarkAnalysis.calculate_summary_stats(results)

    # Create HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gary-Zero Performance Summary</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 8px; }}
            .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
            .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #2196F3; }}
            .metric-label {{ font-size: 14px; color: #666; }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f4f4f4; }}
            .status-success {{ color: green; font-weight: bold; }}
            .status-warning {{ color: orange; font-weight: bold; }}
            .status-error {{ color: red; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 Gary-Zero Performance Summary</h1>
            <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <div class="section">
            <h2>📊 Event Statistics</h2>
            <div class="metric">
                <div class="metric-value">{total_events}</div>
                <div class="metric-label">Total Events</div>
            </div>
            <div class="metric">
                <div class="metric-value">{len(event_types)}</div>
                <div class="metric-label">Event Types</div>
            </div>
            
            <h3>Event Distribution</h3>
            <table>
                <tr><th>Event Type</th><th>Count</th><th>Percentage</th></tr>
    """

    for event_type, count in sorted(
        event_types.items(), key=lambda x: x[1], reverse=True
    ):
        percentage = (count / total_events) * 100 if total_events > 0 else 0
        html_content += f"<tr><td>{event_type.replace('_', ' ').title()}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>\n"

    html_content += """
            </table>
        </div>
        
        <div class="section">
            <h2>⏱️ Performance Metrics</h2>
    """

    if duration_stats:
        html_content += "<h3>Average Execution Times</h3>\n<table>\n<tr><th>Operation Type</th><th>Avg Duration (ms)</th><th>Min (ms)</th><th>Max (ms)</th><th>Count</th></tr>\n"

        for event_type, durations in duration_stats.items():
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            count = len(durations)

            html_content += f"<tr><td>{event_type.replace('_', ' ').title()}</td><td>{avg_duration:.1f}</td><td>{min_duration:.1f}</td><td>{max_duration:.1f}</td><td>{count}</td></tr>\n"

        html_content += "</table>\n"
    else:
        html_content += "<p>No performance timing data available.</p>\n"

    html_content += """
        </div>
        
        <div class="section">
            <h2>🧪 Benchmark Results</h2>
    """

    if benchmark_stats and "error" not in benchmark_stats:
        success_rate = benchmark_stats.get("success_rate", 0) * 100
        avg_score = benchmark_stats.get("score_stats", {}).get("mean", 0)

        status_class = (
            "status-success"
            if success_rate > 80
            else "status-warning"
            if success_rate > 60
            else "status-error"
        )

        html_content += f"""
            <div class="metric">
                <div class="metric-value {status_class}">{success_rate:.1f}%</div>
                <div class="metric-label">Success Rate</div>
            </div>
            <div class="metric">
                <div class="metric-value">{avg_score:.3f}</div>
                <div class="metric-label">Average Score</div>
            </div>
            
            <h3>Score Statistics</h3>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Mean Score</td><td>{benchmark_stats["score_stats"].get("mean", 0):.3f}</td></tr>
                <tr><td>Median Score</td><td>{benchmark_stats["score_stats"].get("median", 0):.3f}</td></tr>
                <tr><td>Standard Deviation</td><td>{benchmark_stats["score_stats"].get("std_dev", 0):.3f}</td></tr>
                <tr><td>Min Score</td><td>{benchmark_stats["score_stats"].get("min", 0):.3f}</td></tr>
                <tr><td>Max Score</td><td>{benchmark_stats["score_stats"].get("max", 0):.3f}</td></tr>
            </table>
        """
    else:
        html_content += "<p>No benchmark results available.</p>\n"

    html_content += """
        </div>
        
        <div class="section">
            <h2>📈 Recommendations</h2>
            <ul>
    """

    # Generate recommendations
    recommendations = []

    if benchmark_stats and "error" not in benchmark_stats:
        success_rate = benchmark_stats.get("success_rate", 0)
        if success_rate < 0.8:
            recommendations.append(
                f"Success rate is {success_rate:.1%}. Investigate failing test cases to improve reliability."
            )

        avg_score = benchmark_stats.get("score_stats", {}).get("mean", 0)
        if avg_score < 0.7:
            recommendations.append(
                f"Average score is {avg_score:.2f}. Consider model fine-tuning or prompt optimization."
            )

    if duration_stats:
        slow_operations = []
        for event_type, durations in duration_stats.items():
            avg_duration = sum(durations) / len(durations)
            if avg_duration > 5000:  # 5 seconds
                slow_operations.append(f"{event_type} ({avg_duration:.0f}ms)")

        if slow_operations:
            recommendations.append(
                f"Slow operations detected: {', '.join(slow_operations)}. Consider performance optimization."
            )

    if not recommendations:
        recommendations.append(
            "System performance appears to be within normal parameters."
        )

    for rec in recommendations:
        html_content += f"<li>{rec}</li>\n"

    html_content += """
            </ul>
        </div>
        
        <div class="section">
            <h2>🔍 Generated Visualizations</h2>
            <p>The following visualization files have been generated:</p>
            <ul>
                <li><strong>performance_timeline.png</strong> - Timeline of task execution durations</li>
                <li><strong>benchmark_comparison.png</strong> - Comparison of benchmark results across configurations</li>
                <li><strong>event_distribution.png</strong> - Distribution of logged event types</li>
            </ul>
        </div>
        
        <footer style="margin-top: 40px; padding: 20px; background-color: #f4f4f4; border-radius: 8px; text-align: center;">
            <p>🤖 Generated by Gary-Zero Unified Logging, Monitoring & Benchmarking Framework</p>
        </footer>
    </body>
    </html>
    """

    # Save HTML report
    with open(output_file, "w") as f:
        f.write(html_content)

    print(f"✅ Performance summary report saved to {output_file}")


async def generate_sample_data():
    """Generate sample data for visualization."""
    print("📊 Generating sample data for visualization...")

    # Generate some log events
    logger = get_unified_logger()

    # Simulate various agent operations
    events_to_create = [
        (EventType.TOOL_EXECUTION, "web_search", 250),
        (EventType.TOOL_EXECUTION, "document_analysis", 450),
        (EventType.CODE_EXECUTION, "python_script", 120),
        (EventType.CODE_EXECUTION, "data_processing", 380),
        (EventType.GUI_ACTION, "button_click", 150),
        (EventType.GUI_ACTION, "form_submission", 200),
        (EventType.KNOWLEDGE_RETRIEVAL, "vector_search", 180),
        (EventType.MEMORY_OPERATION, "graph_update", 90),
        (EventType.AGENT_DECISION, "action_planning", 320),
        (EventType.PERFORMANCE_METRIC, "response_time", 25),
    ]

    for i, (event_type, operation, base_duration) in enumerate(events_to_create):
        # Add some variation to duration
        import random

        duration = base_duration + random.randint(-50, 100)

        event = LogEvent(
            event_type=event_type,
            level=LogLevel.INFO,
            message=f"Sample {operation} operation {i + 1}",
            duration_ms=duration,
            user_id="demo_user",
            agent_id="demo_agent",
            metadata={"sample_data": True, "operation": operation},
        )

        await logger.log_event(event)
        # Small delay to spread timestamps
        await asyncio.sleep(0.01)

    # Generate benchmark results
    harness = BenchmarkHarness(results_dir="./visualization_benchmark_results")

    # Register standard tasks
    task_registry = StandardTasks.get_all_standard_tasks()
    summarization_tasks = task_registry.get_tasks_by_group("summarization")
    code_tasks = task_registry.get_tasks_by_group("code_generation")

    if summarization_tasks:
        harness.register_test_case(summarization_tasks[0])
    if code_tasks:
        harness.register_test_case(code_tasks[0])

    # Register executor and configurations
    harness.register_executor("gary_zero", GaryZeroTestExecutor())

    configs = {
        "optimized": {"model": "gpt-4", "temperature": 0.3},
        "creative": {"model": "gpt-4", "temperature": 0.8},
        "local": {"model": "local-model", "temperature": 0.5},
    }

    for config_name, config in configs.items():
        harness.register_configuration(config_name, config)

    # Run benchmark suite
    print("🏃 Running benchmark suite for visualization...")
    results = await harness.run_test_suite(run_parallel=True, max_concurrent=3)

    print(
        f"✅ Generated {len(await logger.get_events())} log events and {len(results)} benchmark results"
    )

    return await logger.get_events(), results


async def main():
    """Generate visualizations for the unified framework."""
    print("🎨 Gary-Zero Unified Framework Visualization Generator")
    print("=" * 60)

    # Ensure output directory exists
    Path("./visualizations").mkdir(exist_ok=True)

    # Generate sample data
    events, results = await generate_sample_data()

    print(
        f"\n📈 Creating visualizations from {len(events)} events and {len(results)} benchmark results..."
    )

    # Change to visualizations directory
    import os

    os.chdir("./visualizations")

    # Create visualizations
    try:
        create_performance_timeline_chart(events)
    except Exception as e:
        print(f"❌ Error creating timeline chart: {e}")

    try:
        create_benchmark_comparison_chart(results)
    except Exception as e:
        print(f"❌ Error creating benchmark chart: {e}")

    try:
        create_event_distribution_chart(events)
    except Exception as e:
        print(f"❌ Error creating distribution chart: {e}")

    try:
        create_performance_summary_report(events, results)
    except Exception as e:
        print(f"❌ Error creating summary report: {e}")

    print("\n🎉 Visualization generation complete!")
    print("📁 Generated files:")
    print("   - performance_timeline.png")
    print("   - benchmark_comparison.png")
    print("   - event_distribution.png")
    print("   - performance_summary.html")
    print(
        "\n💡 Open performance_summary.html in your browser to view the complete report!"
    )


if __name__ == "__main__":
    try:
        import matplotlib.dates as mdates
        import matplotlib.pyplot as plt
    except ImportError:
        print(
            "❌ matplotlib is required for visualization. Install with: pip install matplotlib"
        )
        exit(1)

    asyncio.run(main())
