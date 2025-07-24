# Unified Logging, Monitoring & Benchmarking Framework


## Overview

This framework provides a comprehensive unified approach to logging, monitoring, and benchmarking that integrates with existing Gary-Zero components while providing enhanced capabilities for data-driven improvements and GAIA-style evaluation.


## Architecture

### Core Components

1. **Unified Logger** (`framework.logging.unified_logger`)
   - Consolidates different logging approaches into a structured event format
   - Integrates with existing audit logger and performance monitor
   - Provides automatic data sanitization and privacy protection

2. **Persistent Storage** (`framework.logging.storage`)
   - SQLite-based storage for log events with proper indexing
   - Event querying and filtering capabilities
   - Automatic data cleanup and maintenance

3. **Logging Hooks** (`framework.logging.hooks`)
   - Decorators and context managers for automatic logging integration
   - Minimal code changes required for existing components
   - Support for both sync and async functions

4. **Benchmarking Harness** (`framework.benchmarking.harness`)
   - GAIA-style standardized task execution
   - Multiple configuration comparison
   - Parallel execution with concurrency control

5. **Standard Tasks** (`framework.benchmarking.tasks`)
   - Pre-defined benchmark tasks for common capabilities
   - Extensible task registry system
   - JSON import/export for custom task suites

6. **Analysis Tools** (`framework.benchmarking.analysis`)
   - Statistical analysis of benchmark results
   - Automated regression detection
   - Performance trend analysis

7. **API Endpoints** (`framework.api.monitoring`)
   - REST API for accessing logs and metrics
   - Health checks and system status
   - Performance metrics export


## Event Schema

### LogEvent Structure

```json
{
  "event_id": "uuid",
  "timestamp": 1234567890.123,
  "timestamp_iso": "2025-01-22T14:30:00.123Z",
  "event_type": "tool_execution|code_execution|gui_action|...",
  "level": "debug|info|warning|error|critical",
  "message": "Human-readable description",

  "agent_id": "optional_agent_identifier",
  "session_id": "optional_session_identifier",
  "user_id": "optional_user_identifier",

  "component": "optional_component_name",
  "function_name": "optional_function_name",
  "tool_name": "optional_tool_name",

  "input_data": {"sanitized": "input_parameters"},
  "output_data": {"sanitized": "output_results"},
  "metadata": {"additional": "context_information"},

  "duration_ms": 150.5,
  "cpu_usage": 45.2,
  "memory_usage": 128.7,

  "error_type": "optional_error_class",
  "error_message": "optional_error_description",
  "stack_trace": "optional_stack_trace"
}
```

### Event Types

- **User Interactions**: `user_input`, `user_action`
- **System Operations**: `tool_execution`, `code_execution`, `gui_action`, `knowledge_retrieval`, `memory_operation`
- **Infrastructure**: `performance_metric`, `system_event`, `config_change`
- **Security**: `authentication`, `authorization`, `security_violation`, `rate_limit`
- **Planning**: `agent_decision`, `task_created`, `task_completed`, `task_failed`
- **Diagnostics**: `error`, `exception`


## Usage Examples

### Basic Logging

```python
from framework.logging.unified_logger import get_unified_logger, LogLevel, EventType

logger = get_unified_logger()

# Log tool execution
await logger.log_tool_execution(
    tool_name="web_search",
    parameters={"query": "AI in healthcare", "limit": 10},
    success=True,
    duration_ms=250.5,
    user_id="user123",
    agent_id="agent456"
)

# Log code execution
await logger.log_code_execution(
    code_snippet="print('Hello World')",
    language="python",
    success=True,
    output="Hello World",
    user_id="user123"
)
```

### Automatic Logging with Hooks

```python
from framework.logging.hooks import log_tool_execution, log_operation

@log_tool_execution(tool_name="data_processor", user_id="user123")
async def process_data(data):
    # Function automatically logged
    return processed_data

# Context manager for operations
async with log_operation("database_query", EventType.SYSTEM_EVENT):
    results = await database.query("SELECT * FROM table")
```

### Benchmarking

```python
from framework.benchmarking.harness import BenchmarkHarness
from framework.benchmarking.tasks import StandardTasks

# Set up harness
harness = BenchmarkHarness(results_dir="./benchmark_results")

# Register standard tasks
task_registry = StandardTasks.get_all_standard_tasks()
for task_id, task in task_registry.tasks.items():
    harness.register_test_case(task)

# Register configurations
harness.register_configuration("gpt4_optimized", {
    "model": "gpt-4",
    "temperature": 0.3,
    "max_tokens": 2000
})

# Run benchmark suite
results = await harness.run_test_suite(
    task_ids=["summarize_research_paper"],
    config_names=["gpt4_optimized"],
    run_parallel=True
)
```

### Analysis and Reporting

```python
from framework.benchmarking.analysis import BenchmarkAnalysis, RegressionDetector
from framework.benchmarking.reporting import BenchmarkReporter

# Statistical analysis
stats = BenchmarkAnalysis.calculate_summary_stats(results)
comparison = BenchmarkAnalysis.compare_configurations(results)

# Regression detection
detector = RegressionDetector()
alerts = detector.detect_regressions(baseline_results, current_results)

# Generate reports
reporter = BenchmarkReporter()
report_file = reporter.generate_summary_report(results)
```


## API Endpoints

The framework exposes REST API endpoints for accessing logs and metrics:

- `GET /api/v1/monitoring/logs` - Retrieve log events with filtering
- `GET /api/v1/monitoring/logs/statistics` - Get logging statistics
- `GET /api/v1/monitoring/logs/timeline` - Get execution timeline
- `GET /api/v1/monitoring/performance` - Get performance metrics
- `GET /api/v1/monitoring/performance/export` - Export performance data
- `GET /api/v1/monitoring/health` - Health check endpoint
- `POST /api/v1/monitoring/logs/test` - Create test log event

### API Usage Examples

```bash
# Get recent log events
curl "http://localhost:8000/api/v1/monitoring/logs?limit=50&event_type=tool_execution"

# Get execution timeline for an agent
curl "http://localhost:8000/api/v1/monitoring/logs/timeline?agent_id=agent123"

# Get performance metrics
curl "http://localhost:8000/api/v1/monitoring/performance?duration_seconds=3600"

# Health check
curl "http://localhost:8000/api/v1/monitoring/health"
```


## Integration Guide

### 1. Add Logging to Existing Functions

```python
# Before
async def execute_tool(tool_name, params):
    result = await tool.run(params)
    return result

# After
from framework.logging.hooks import log_tool_execution

@log_tool_execution(tool_name="dynamic_tool")
async def execute_tool(tool_name, params):
    result = await tool.run(params)
    return result
```

### 2. Enable Performance Monitoring

```python
from framework.logging.unified_logger import get_unified_logger

logger = get_unified_logger()

# Track performance metrics
await logger.log_performance_metric(
    metric_name="response_time",
    value=response_time_ms,
    unit="ms",
    tags={"component": "llm_client"}
)
```

### 3. Set Up Benchmarking

```python
# Create custom task
from framework.benchmarking.harness import TestCase, TaskType

custom_task = TestCase(
    task_id="custom_analysis",
    name="Custom Analysis Task",
    description="Analyze data and provide insights",
    task_type=TaskType.DATA_ANALYSIS,
    input_data={"dataset": "sample_data.csv"},
    scoring_criteria={"accuracy": 0.4, "insight_quality": 0.6}
)

harness.register_test_case(custom_task)
```


## Configuration

### Environment Variables

- `GARY_ZERO_LOG_LEVEL` - Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `GARY_ZERO_LOG_STORAGE` - Storage backend (sqlite, memory)
- `GARY_ZERO_BENCHMARK_DIR` - Directory for benchmark results
- `GARY_ZERO_ENABLE_MONITORING` - Enable/disable monitoring (true/false)

### Storage Configuration

```python
from framework.logging.storage import SqliteStorage

# Configure persistent storage
storage = SqliteStorage("./logs/events.db")

# Cleanup old events (30 days retention)
deleted_count = await storage.cleanup_old_events(days_to_keep=30)
```


## Privacy and Security

### Data Sanitization

The framework automatically sanitizes sensitive data:

- API keys, tokens, passwords are replaced with `[REDACTED]`
- Large strings are truncated with `[TRUNCATED]` indicator
- Environment variables and secrets are not captured

### Compliance Features

- Configurable data retention periods
- Automatic PII detection and removal
- Audit trail for all system operations
- Role-based access control for API endpoints


## Testing

Run the comprehensive test suite:

```bash
# Basic functionality tests
python test_framework.py

# Integration demonstration
python integration_demo.py

# Run with pytest (if available)
python -m pytest tests/ -v
```


## Performance Considerations

### Resource Usage

- **Memory**: Event buffer limited to 10,000 events by default
- **Storage**: SQLite database with automatic indexing
- **CPU**: Minimal overhead with async processing
- **Network**: Configurable batch sizes for remote logging

### Optimization Tips

1. **Adjust buffer size** based on event volume
2. **Use appropriate log levels** to reduce noise
3. **Configure retention periods** to manage storage
4. **Enable parallel benchmarking** for faster execution
5. **Use filtering** in API queries to reduce response times


## Troubleshooting

### Common Issues

1. **High memory usage**: Reduce buffer size or increase cleanup frequency
2. **Slow benchmarks**: Enable parallel execution and optimize configurations
3. **Missing events**: Check log levels and ensure proper integration
4. **API timeouts**: Use pagination and filtering for large datasets

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
logging.getLogger("gary_zero.unified_logger").setLevel(logging.DEBUG)
```


## Future Enhancements

### Planned Features

- [ ] Real-time dashboard with charts and graphs
- [ ] Integration with external monitoring systems (Prometheus, Grafana)
- [ ] Machine learning-based anomaly detection
- [ ] Advanced benchmarking with A/B testing
- [ ] Custom scoring algorithms for task evaluation
- [ ] Export to industry-standard formats (OpenTelemetry)

### Extension Points

- **Custom storage backends**: Implement `LogStorage` interface
- **Custom test executors**: Implement `TestExecutor` interface
- **Custom scoring functions**: Extend benchmark analysis
- **Custom event types**: Add domain-specific event categories


## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on extending the framework.


## License

This framework is part of the Gary-Zero project and follows the same licensing terms.
