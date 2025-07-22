#!/usr/bin/env python3
"""
CLI tool for Gary-Zero Unified Logging, Monitoring & Benchmarking Framework.

Provides command-line interface for querying logs, running benchmarks,
and generating reports.
"""

import asyncio
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from framework.logging.unified_logger import get_unified_logger, EventType, LogLevel
from framework.logging.storage import SqliteStorage
from framework.benchmarking.harness import BenchmarkHarness
from framework.benchmarking.tasks import StandardTasks
from framework.benchmarking.analysis import BenchmarkAnalysis, RegressionDetector
from framework.benchmarking.reporting import BenchmarkReporter
from integration_demo import GaryZeroTestExecutor


async def cmd_logs(args):
    """Command to query and display logs."""
    logger = get_unified_logger()
    
    # Parse filters
    event_type = None
    if args.event_type:
        try:
            event_type = EventType(args.event_type)
        except ValueError:
            print(f"❌ Invalid event type: {args.event_type}")
            print(f"Available types: {', '.join([e.value for e in EventType])}")
            return
    
    level = None
    if args.level:
        try:
            level = LogLevel(args.level)
        except ValueError:
            print(f"❌ Invalid log level: {args.level}")
            print(f"Available levels: {', '.join([l.value for l in LogLevel])}")
            return
    
    # Parse time range
    start_time = None
    end_time = None
    if args.since:
        try:
            hours = float(args.since)
            start_time = (datetime.now() - timedelta(hours=hours)).timestamp()
        except ValueError:
            print(f"❌ Invalid time format: {args.since}")
            return
    
    # Query events
    events = await logger.get_events(
        event_type=event_type,
        level=level,
        user_id=args.user_id,
        agent_id=args.agent_id,
        start_time=start_time,
        end_time=end_time,
        limit=args.limit
    )
    
    if not events:
        print("📭 No events found matching criteria")
        return
    
    print(f"📋 Found {len(events)} events:")
    print("-" * 80)
    
    for event in events:
        timestamp = datetime.fromtimestamp(event.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        duration = f" ({event.duration_ms:.1f}ms)" if event.duration_ms else ""
        
        print(f"[{timestamp}] {event.level.value.upper():<8} {event.event_type.value}")
        print(f"  {event.message}{duration}")
        
        if event.tool_name:
            print(f"  Tool: {event.tool_name}")
        
        if event.error_message:
            print(f"  Error: {event.error_message}")
        
        if args.verbose and event.metadata:
            print(f"  Metadata: {json.dumps(event.metadata, indent=2)}")
        
        print()


async def cmd_stats(args):
    """Command to display statistics."""
    logger = get_unified_logger()
    stats = logger.get_statistics()
    
    print("📊 Unified Logging Statistics")
    print("=" * 40)
    print(f"Total Events:        {stats['total_events']}")
    print(f"Events in Buffer:    {stats['events_in_buffer']}")
    print(f"Buffer Utilization:  {stats['buffer_utilization']:.1%}")
    print()
    
    print("Events by Type:")
    for event_type, count in sorted(stats['events_by_type'].items()):
        print(f"  {event_type:<20} {count:>8}")
    print()
    
    print("Events by Level:")
    for level, count in sorted(stats['events_by_level'].items()):
        print(f"  {level:<20} {count:>8}")


async def cmd_timeline(args):
    """Command to display execution timeline."""
    logger = get_unified_logger()
    
    # Parse time range
    start_time = None
    if args.since:
        try:
            hours = float(args.since)
            start_time = (datetime.now() - timedelta(hours=hours)).timestamp()
        except ValueError:
            print(f"❌ Invalid time format: {args.since}")
            return
    
    timeline = await logger.get_execution_timeline(
        user_id=args.user_id,
        agent_id=args.agent_id,
        start_time=start_time
    )
    
    if not timeline:
        print("📭 No timeline events found")
        return
    
    print(f"🕒 Execution Timeline ({len(timeline)} events):")
    print("-" * 80)
    
    for event in timeline:
        timestamp = datetime.fromtimestamp(event.timestamp).strftime('%H:%M:%S')
        duration = f" ({event.duration_ms:.1f}ms)" if event.duration_ms else ""
        
        print(f"[{timestamp}] {event.event_type.value:<20} {event.message}{duration}")
    

async def cmd_benchmark(args):
    """Command to run benchmarks."""
    print(f"🧪 Running benchmark suite...")
    
    # Set up harness
    harness = BenchmarkHarness(results_dir=args.output or "./benchmark_results")
    
    # Register tasks
    if args.tasks_file:
        try:
            task_registry = StandardTasks.load_tasks_from_file(args.tasks_file)
        except Exception as e:
            print(f"❌ Error loading tasks file: {e}")
            return
    else:
        task_registry = StandardTasks.get_all_standard_tasks()
    
    for task_id, task in task_registry.tasks.items():
        harness.register_test_case(task)
    
    print(f"✅ Registered {len(task_registry.tasks)} tasks")
    
    # Register executor
    harness.register_executor("gary_zero", GaryZeroTestExecutor())
    
    # Register configurations
    configs = {
        "default": {"model": "gpt-4", "temperature": 0.7},
        "optimized": {"model": "gpt-4", "temperature": 0.3},
        "creative": {"model": "gpt-4", "temperature": 0.8}
    }
    
    for config_name, config in configs.items():
        harness.register_configuration(config_name, config)
    
    # Run benchmarks
    task_ids = args.task_ids.split(',') if args.task_ids else None
    config_names = args.configs.split(',') if args.configs else None
    
    results = await harness.run_test_suite(
        task_ids=task_ids,
        config_names=config_names,
        run_parallel=not args.sequential,
        max_concurrent=args.parallel_count
    )
    
    print(f"✅ Completed {len(results)} benchmark runs")
    
    # Display summary
    successful = [r for r in results if r.status.value == "completed"]
    if successful:
        avg_score = sum(r.score for r in successful if r.score) / len([r for r in successful if r.score])
        print(f"📊 Success rate: {len(successful)/len(results):.1%}")
        print(f"📊 Average score: {avg_score:.3f}")
    
    # Generate report if requested
    if args.report:
        reporter = BenchmarkReporter(output_dir=args.output or "./benchmark_results")
        report_file = reporter.generate_summary_report(results, "CLI Benchmark Report")
        print(f"📄 Report saved to: {report_file}")


async def cmd_analyze(args):
    """Command to analyze benchmark results."""
    print(f"📈 Analyzing benchmark results from {args.results_dir}...")
    
    # Load results
    harness = BenchmarkHarness(results_dir=args.results_dir)
    results = await harness.load_results()
    
    if not results:
        print("❌ No benchmark results found")
        return
    
    print(f"📊 Loaded {len(results)} benchmark results")
    
    # Generate analysis
    analysis = BenchmarkAnalysis.calculate_summary_stats(results)
    
    if "error" in analysis:
        print(f"❌ Analysis error: {analysis['error']}")
        return
    
    print("\n📈 Summary Statistics:")
    print(f"  Total runs:        {analysis['total_runs']}")
    print(f"  Successful runs:   {analysis['successful_runs']}")
    print(f"  Success rate:      {analysis['success_rate']:.1%}")
    
    if 'score_stats' in analysis:
        score_stats = analysis['score_stats']
        print(f"  Average score:     {score_stats['mean']:.3f}")
        print(f"  Score std dev:     {score_stats['std_dev']:.3f}")
        print(f"  Score range:       {score_stats['min']:.3f} - {score_stats['max']:.3f}")
    
    # Configuration comparison
    if args.compare_configs:
        comparison = BenchmarkAnalysis.compare_configurations(results)
        print(f"\n🔍 Configuration Comparison:")
        
        for config_name, config_stats in comparison.items():
            if "error" not in config_stats:
                success_rate = config_stats.get('success_rate', 0)
                avg_score = config_stats.get('score_stats', {}).get('mean', 0)
                print(f"  {config_name:<15} {success_rate:.1%} success, {avg_score:.3f} avg score")
    
    # Regression detection
    if args.detect_regressions and args.baseline_period:
        try:
            hours = float(args.baseline_period)
            baseline_cutoff = (datetime.now() - timedelta(hours=hours)).timestamp()
            
            baseline_results = [r for r in results if r.timestamp < baseline_cutoff]
            current_results = [r for r in results if r.timestamp >= baseline_cutoff]
            
            if baseline_results and current_results:
                detector = RegressionDetector()
                alerts = detector.detect_regressions(baseline_results, current_results)
                
                if alerts:
                    print(f"\n⚠️  Regression Alerts ({len(alerts)}):")
                    for alert in alerts:
                        print(f"  {alert.task_id}: {alert.metric} degraded by {alert.change_percent:.1%} ({alert.severity})")
                else:
                    print(f"\n✅ No regressions detected")
            else:
                print(f"\n❌ Insufficient data for regression analysis")
        
        except ValueError:
            print(f"❌ Invalid baseline period: {args.baseline_period}")


async def cmd_export(args):
    """Command to export data."""
    if args.type == "logs":
        # Export logs
        if args.storage == "sqlite":
            storage = SqliteStorage(args.db_path or "./logs/events.db")
            events = await storage.get_events(limit=args.limit)
            
            output_file = args.output or "exported_logs.json"
            with open(output_file, 'w') as f:
                for event in events:
                    f.write(event.to_json() + '\n')
            
            print(f"✅ Exported {len(events)} log events to {output_file}")
        else:
            # Export from memory
            logger = get_unified_logger()
            events = await logger.get_events(limit=args.limit)
            
            output_file = args.output or "exported_logs.json"
            with open(output_file, 'w') as f:
                for event in events:
                    f.write(event.to_json() + '\n')
            
            print(f"✅ Exported {len(events)} log events to {output_file}")
    
    elif args.type == "benchmarks":
        # Export benchmark results
        harness = BenchmarkHarness(results_dir=args.results_dir or "./benchmark_results")
        results = await harness.load_results()
        
        output_file = args.output or "exported_benchmarks.json"
        with open(output_file, 'w') as f:
            json.dump([result.to_dict() for result in results], f, indent=2, default=str)
        
        print(f"✅ Exported {len(results)} benchmark results to {output_file}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Gary-Zero Unified Logging, Monitoring & Benchmarking CLI"
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Query and display log events')
    logs_parser.add_argument('--event-type', help='Filter by event type')
    logs_parser.add_argument('--level', help='Filter by log level')
    logs_parser.add_argument('--user-id', help='Filter by user ID')
    logs_parser.add_argument('--agent-id', help='Filter by agent ID')
    logs_parser.add_argument('--since', help='Show events from last N hours', type=str)
    logs_parser.add_argument('--limit', help='Maximum number of events', type=int, default=50)
    logs_parser.add_argument('--verbose', '-v', help='Show detailed information', action='store_true')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Display logging statistics')
    
    # Timeline command
    timeline_parser = subparsers.add_parser('timeline', help='Display execution timeline')
    timeline_parser.add_argument('--user-id', help='Filter by user ID')
    timeline_parser.add_argument('--agent-id', help='Filter by agent ID')
    timeline_parser.add_argument('--since', help='Show events from last N hours', type=str)
    
    # Benchmark command
    benchmark_parser = subparsers.add_parser('benchmark', help='Run benchmark suite')
    benchmark_parser.add_argument('--task-ids', help='Comma-separated task IDs to run')
    benchmark_parser.add_argument('--configs', help='Comma-separated config names to use')
    benchmark_parser.add_argument('--tasks-file', help='JSON file with custom tasks')
    benchmark_parser.add_argument('--output', help='Output directory for results')
    benchmark_parser.add_argument('--sequential', help='Run tests sequentially', action='store_true')
    benchmark_parser.add_argument('--parallel-count', help='Max parallel tests', type=int, default=3)
    benchmark_parser.add_argument('--report', help='Generate summary report', action='store_true')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze benchmark results')
    analyze_parser.add_argument('--results-dir', help='Directory with benchmark results', default='./benchmark_results')
    analyze_parser.add_argument('--compare-configs', help='Compare configurations', action='store_true')
    analyze_parser.add_argument('--detect-regressions', help='Detect regressions', action='store_true')
    analyze_parser.add_argument('--baseline-period', help='Baseline period in hours for regression detection')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export data')
    export_parser.add_argument('type', choices=['logs', 'benchmarks'], help='Type of data to export')
    export_parser.add_argument('--output', help='Output file path')
    export_parser.add_argument('--limit', help='Maximum number of records', type=int, default=1000)
    export_parser.add_argument('--storage', choices=['memory', 'sqlite'], default='memory', help='Storage backend for logs')
    export_parser.add_argument('--db-path', help='SQLite database path')
    export_parser.add_argument('--results-dir', help='Benchmark results directory', default='./benchmark_results')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Map commands to functions
    commands = {
        'logs': cmd_logs,
        'stats': cmd_stats,
        'timeline': cmd_timeline,
        'benchmark': cmd_benchmark,
        'analyze': cmd_analyze,
        'export': cmd_export
    }
    
    if args.command in commands:
        try:
            asyncio.run(commands[args.command](args))
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
        except Exception as e:
            print(f"❌ Error: {e}")
            if '--verbose' in sys.argv or '-v' in sys.argv:
                import traceback
                traceback.print_exc()
    else:
        print(f"❌ Unknown command: {args.command}")
        parser.print_help()


if __name__ == "__main__":
    main()