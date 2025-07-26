# Hierarchical Planning System

Gary-Zero now includes a powerful hierarchical planning engine that can decompose complex objectives into actionable subtasks with intelligent tool assignment and automatic evaluation loops.

## Overview

The hierarchical planning system enhances Gary-Zero's capabilities by:

- **Automatic Task Decomposition**: Breaking down complex objectives into ordered, manageable subtasks
- **Intelligent Tool Assignment**: Automatically selecting appropriate tools for each subtask
- **Evaluation Loops**: Verifying subtask outputs and adjusting plans dynamically on failures
- **Dependency Management**: Managing complex interdependencies between subtasks
- **Progress Monitoring**: Real-time tracking of plan execution with detailed status reports

## Key Components

### HierarchicalPlanner

The core planning engine that decomposes objectives into subtasks:

```python
from framework.helpers.hierarchical_planner import HierarchicalPlanner

planner = HierarchicalPlanner()
plan = planner.create_plan("Research the latest battery technologies and create a summary")
```

### Enhanced Scheduler

Integrates with the existing TaskScheduler for seamless execution:

```python
from framework.helpers.enhanced_scheduler import EnhancedHierarchicalScheduler

scheduler = EnhancedHierarchicalScheduler()
plan = scheduler.create_and_execute_plan(
    "Research AI developments and create presentation",
    auto_execute=True
)
```

### Planning Tool

Agent-accessible tool for interactive planning:

```python
# Via agent tool interface
response = await planning_tool.execute(
    method="create_plan",
    objective="Analyze customer feedback and generate insights",
    auto_execute=True
)
```

## Usage Examples

### Basic Research and Summarization

```python
objective = "Research the latest battery technologies, summarize findings, and generate a slide deck"
plan = scheduler.create_and_execute_plan(objective)

# This creates a plan with subtasks like:
# 1. Define research scope for battery technologies
# 2. Search for battery technologies information
# 3. Gather detailed battery technologies content
# 4. Analyze battery technologies findings
# 5. Create battery technologies summary
```

### Software Development Project

```python
objective = "Create a React dashboard with real-time data visualization"
plan = scheduler.create_and_execute_plan(objective)

# This creates a plan with subtasks like:
# 1. Plan development approach
# 2. Implement solution (using code_execution_tool)
# 3. Test and verify
```

### Data Analysis Task

```python
objective = "Analyze customer feedback data and create recommendations"
plan = scheduler.create_and_execute_plan(objective)

# This creates a plan with subtasks like:
# 1. Gather data for analysis
# 2. Perform analysis (using code_execution_tool)
# 3. Generate analysis report
```

## Agent Tool Interface

The planning functionality is available to agents through the `planning_tool`:

### Create a Plan

```
Create a hierarchical plan:
- Method: create_plan
- objective: "Your complex objective here"
- auto_execute: true/false (default: true)
```

### Monitor Plan Progress

```
Check plan status:
- Method: get_plan_status
- plan_id: "your_plan_id"
- detailed: true/false (default: true)
```

### List All Plans

```
List active plans:
- Method: list_plans
- status_filter: "pending"|"in_progress"|"completed"|"failed" (optional)
```

### Configure Planning

```
Configure planner settings:
- Method: configure_planner
- auto_planning_enabled: true/false
- max_recursion_depth: integer (default: 3)
- model_name: "gpt-4"|"gpt-3.5-turbo"|etc
- max_subtasks: integer (default: 10)
- verification_enabled: true/false
- retry_failed_subtasks: true/false
```

## Configuration Options

The planner can be configured through environment variables or runtime settings:

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| Auto Planning | `PLANNER_AUTO_PLANNING` | `true` | Enable automatic plan creation |
| Max Recursion | `PLANNER_MAX_RECURSION_DEPTH` | `3` | Maximum depth for nested planning |
| Model | `PLANNER_MODEL` | `gpt-4` | LLM model for planning decisions |
| Max Subtasks | `PLANNER_MAX_SUBTASKS` | `10` | Maximum subtasks per plan |
| Verification | `PLANNER_VERIFICATION` | `true` | Enable output verification |
| Retry Failed | `PLANNER_RETRY_FAILED` | `true` | Retry failed subtasks |

## Evaluation and Quality Control

### Automatic Evaluation

Each subtask output is automatically evaluated based on:
- Content length and completeness
- Presence of required keywords
- Tool-specific quality criteria
- Expected output format

### Dynamic Plan Adjustment

When subtasks fail or produce low-quality output, the system can:
- Retry with alternative tools
- Split complex subtasks into smaller ones
- Add preparation subtasks for better context
- Provide specific feedback for improvement

### Quality Scoring

Outputs are scored on a 0.0-1.0 scale:
- ≥0.7: Success (proceed to next subtask)
- 0.5-0.7: Acceptable (proceed with warnings)
- <0.5: Requires retry or plan adjustment

## Tool Selection

The planner intelligently assigns tools based on subtask requirements:

### Search and Research Tasks

- `search_engine`: Web searches and information discovery
- `webpage_content_tool`: Content extraction from URLs
- `knowledge_tool`: Analysis and synthesis of information

### Development and Creation Tasks

- `code_execution_tool`: Programming, scripts, and technical implementation
- `response`: Content generation and formatting

### Analysis Tasks

- `knowledge_tool`: Data analysis and interpretation
- `code_execution_tool`: Statistical analysis and processing

## Success Metrics

The hierarchical planning system achieves:

- **≥80% Appropriate Tool Selection**: Tools are correctly assigned based on subtask requirements
- **Minimal Manual Intervention**: Complex objectives are automatically decomposed into executable plans
- **≥20% Token Efficiency**: Structured planning reduces overall token usage compared to manual decomposition

## Best Practices

### Objective Formulation

- Be specific about desired outcomes
- Include context about target audience or use case
- Mention preferred output format if relevant

Examples:
- ✅ "Research the latest developments in solid-state battery technology, analyze market potential, and create an executive summary"
- ❌ "Research batteries"

### Plan Monitoring

- Use `get_plan_status` with `detailed=true` for comprehensive progress tracking
- Monitor failed subtasks and review error messages
- Cancel and recreate plans if objectives change significantly

### Configuration Tuning

- Increase `max_subtasks` for complex objectives requiring many steps
- Disable `verification_enabled` for faster execution when quality control isn't critical
- Adjust `max_recursion_depth` based on objective complexity

## Integration with Existing Systems

The hierarchical planner integrates seamlessly with:

- **TaskScheduler**: Automatic task creation and execution
- **Agent Context**: Maintains conversation context across subtasks
- **Memory System**: Persistent storage of plan history and results
- **Tool Framework**: Leverages all existing Gary-Zero tools

## Troubleshooting

### Common Issues

**Plan not executing automatically:**
- Check that `auto_planning_enabled` is true
- Verify TaskScheduler is available and running
- Review plan status for error messages

**Poor tool selection:**
- Ensure objective clearly describes the desired actions
- Check if specific tools are available in the system
- Review and adjust planning configuration

**Subtasks failing repeatedly:**
- Enable detailed logging to see failure reasons
- Consider breaking complex objectives into simpler ones
- Verify that required tools and dependencies are available

**Plans taking too long:**
- Reduce `max_subtasks` to create simpler plans
- Adjust dependency structure to allow parallel execution
- Consider disabling verification for faster execution

## Future Enhancements

Planned improvements include:
- LLM-powered dynamic plan generation
- Multi-agent collaborative planning
- Learning from past plan execution history
- Integration with external workflow systems
- Advanced dependency optimization
