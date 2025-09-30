# Memory Graph System

The Memory Graph System provides structured entity-relationship modeling for Gary-Zero, enabling multi-agent composability and reasoning through explicit connections between entities.

## Overview

The memory graph complements Gary-Zero's existing vector-based memory system by providing:

- **Structured Entity Storage**: Services, environment variables, incidents, features, and more
- **Explicit Relationship Modeling**: Clear connections between entities (requires, impacts, depends-on)
- **Multi-hop Reasoning**: Agents can reason across relationship chains
- **Composable Outputs**: Structured data that agents can query rather than parsing text
- **Context Compression**: Fetch only relevant subgraphs instead of large context windows
- **Explainable Decisions**: Reasoning paths are traceable and auditable

## Architecture

The system consists of three main components:

### 1. Core Graph Structure (`memory_graph.py`)

**Entities (Nodes)**:
- Service: Applications, microservices, deployments
- EnvVar: Environment variables and configuration
- Incident: Issues, outages, problems
- Feature: Capabilities, functionality, routes
- Customer, Plan, Module: Business entities

**Relationships (Edges)**:
- `SERVICE_REQUIRES_ENVVAR`: Service depends on environment variable
- `INCIDENT_IMPACTS_SERVICE`: Incident affects service operation
- `FEATURE_DEPENDS_ON`: Feature requires another component
- `SERVICE_INTEGRATES_WITH`: Service connects to another service

**Graph Operations**:
- Node/edge upsert with automatic deduplication
- Multi-hop path finding
- Subgraph extraction around entities
- Query by type with property filters
- Persistence to JSON storage

### 2. Agent A - Graph Ingestor (`graph_ingestor.py`)

The ingestor extracts entities and relationships from unstructured text:

**Pattern Matching**:
- Service dependencies: "crm7 requires SUPABASE_URL and STRIPE_SECRET_KEY"
- Incident impacts: "incident INC-101 impacts crm7"
- Service integrations: "crm7 integrates with notification-service"

**Specialized Processing**:
- Deployment log analysis
- Environment variable extraction
- JSON/YAML structure parsing

**Output**: Structured nodes and edges with source attribution for auditability

### 3. Agent B - Graph Planner (`graph_planner.py`)

The planner performs read-only reasoning on the graph:

**Analysis Capabilities**:
- Service blocking factors analysis
- Dependency resolution
- Impact radius calculation
- Multi-hop incident correlation
- Action recommendations with priority

**Query Interface**:
- Service dependencies
- Missing environment variables
- Related incidents
- Path finding between entities

## Usage Examples

### Basic Setup

```python
from framework.helpers.memory_graph import MemoryGraph
from framework.helpers.graph_ingestor import GraphIngestor
from framework.helpers.graph_planner import GraphPlanner

# Create graph and agents
graph = MemoryGraph()
ingestor = GraphIngestor(graph)
planner = GraphPlanner(graph)
```

### Agent A - Ingesting Text

```python
# Process deployment documentation
deployment_text = "crm7 on Vercel requires SUPABASE_URL, SUPABASE_ANON_KEY"
results = ingestor.ingest_text(deployment_text, source="deploy_docs.md")

# Process incident reports
incident_text = "Incident INC-101 impacts crm7 due to missing SUPABASE_URL"
ingestor.ingest_text(incident_text, source="incident_report.md")

# Process deployment logs
log_text = """
[2024-01-15] Missing environment variable: SUPABASE_URL
[2024-01-15] Required STRIPE_SECRET_KEY not found
"""
ingestor.ingest_deployment_log(log_text, "crm7", source="deploy.log")
```

### Agent B - Querying and Reasoning

```python
# Analyze what's blocking a service
blocking_analysis = planner.what_blocks_service("crm7")
print(f"Blocking factors: {blocking_analysis['blocking_factors']}")

# Get service dependencies
dependencies = planner.get_service_dependencies("crm7")
print(f"Environment variables: {dependencies['environment_variables']}")

# Find related incidents across multiple hops
incidents = planner.find_related_incidents("crm7", max_hops=3)
print(f"Related incidents: {incidents['related_incidents']}")

# Get action recommendations
recommendations = planner.recommend_actions("crm7")
for rec in recommendations['recommendations']:
    print(f"[{rec['priority']}] {rec['action']}")
```

### Multi-hop Reasoning Example

```python
# Scenario: Issue #412 is blocked by missing env var in crm7 
# → relevant to deploy playbook → notify release bot

# 1. Ingest the problem
ingestor.ingest_text(
    "Issue #412 is blocked by missing SUPABASE_URL in crm7", 
    source="github_issue.md"
)

# 2. Ingest the deployment context
ingestor.ingest_text(
    "crm7 deployment requires SUPABASE_URL and affects release-bot notifications",
    source="deploy_playbook.md"
)

# 3. Find reasoning path
paths = graph.find_path("incident:#412", "service:release-bot", max_hops=3)

# 4. Get impact analysis
impact = planner.analyze_impact_radius("incident:#412", max_hops=3)
print(f"Entities impacted: {impact['total_impacted_entities']}")
```

## Integration with Existing Memory System

The memory graph extends the existing `Memory` class:

```python
from framework.helpers.memory import Memory

# Get memory instance (existing functionality)
memory = await Memory.get(agent)

# Access graph capabilities (new)
graph = memory.get_memory_graph()
ingestor = memory.get_graph_ingestor()
planner = memory.get_graph_planner()

# Graph is automatically persisted with memory
await memory.save_graph()
```

## CRM7 Deployment Scenario

Here's the complete 20-minute mini-experiment from the problem statement:

### 1. Pick Two Agents
- **Agent A (Ingestor)**: Extracts entities from deployment docs and logs
- **Agent B (Planner)**: Answers deployment questions using only graph data

### 2. Create Tiny Schema
```python
# Entities: Service, EnvVar, Incident
# Relations: SERVICE_REQUIRES_ENVVAR, INCIDENT_IMPACTS_SERVICE
```

### 3. Wire A → Graph
```python
# Process: "crm7 on Vercel requires SUPABASE_URL, SUPABASE_ANON_KEY"
results = ingestor.ingest_text(text, source="deploy_docs")

# Results in:
# - Node: Service(name="crm7")  
# - Node: EnvVar(key="SUPABASE_URL")
# - Node: EnvVar(key="SUPABASE_ANON_KEY")
# - Edge: SERVICE_REQUIRES_ENVVAR(crm7 → SUPABASE_URL)
# - Edge: SERVICE_REQUIRES_ENVVAR(crm7 → SUPABASE_ANON_KEY)
```

### 4. Query with B
```python
# Question: "What's blocking crm7 rollout?"
blocking = planner.what_blocks_service("crm7")

# Agent B returns missing EnvVar edges for Service=crm7
# Using only graph queries (no raw text)
```

### 5. Add Second Hop
```python
# Insert incident
ingestor.ingest_text(
    "Incident INC-101 cause missing SUPABASE_URL impacts crm7",
    source="incident_report"
)

# Query: "Which incidents are related to current rollout risks?"
related = planner.find_related_incidents("crm7", max_hops=2)

# Multi-hop reasoning: crm7 → SUPABASE_URL ← INC-101
```

## Performance and Scalability

### Context Compression
```python
# Instead of loading full conversation history:
subgraph = graph.get_subgraph("service:crm7", hops=2)

# Only relevant entities within 2 hops, reducing prompt size
# while maintaining complete context for reasoning
```

### Auditability
Every entity and relationship includes:
- Source attribution (file, line, run ID)
- Creation and update timestamps
- Structured properties for filtering

### Caching
```python
# Cache subgraphs for repeated queries
cached_subgraph = graph.get_subgraph("service:crm7", hops=2)

# Reuse for multiple planning operations without re-querying
```

## Testing

The system includes comprehensive tests:

```bash
# Run basic graph tests
python test_memory_graph_simple.py

# Run agent functionality tests  
python test_agents_simple.py

# Run full test suite
python -m pytest framework/tests/test_memory_graph.py -v
```

## Future Extensions

### Expanded Schema
- **Ticket**: Support tickets, GitHub issues
- **Customer**: Customer entities and relationships
- **Plan**: Service plans and modules
- **Permission**: Access control modeling

### Advanced Queries
- Graph traversal algorithms
- Similarity scoring between entities
- Temporal reasoning (time-based relationships)
- Probabilistic relationships

### Integration Points
- GitHub issue ingestion
- Deployment pipeline integration
- Monitoring system connections
- Customer support workflows

## Benefits for Multi-Agent Work

### Composability
Agent outputs become structured nodes/edges that other agents can query, eliminating text parsing between agents.

### Context Compression  
Agents fetch only relevant subgraphs (N hops) instead of full conversation histories, reducing token usage.

### Traceability
Decisions are explainable with clear reasoning paths: "chose Plan B because Node X linked to 3 outages last month".

### Consistency
Shared structured representation ensures all agents work with the same understanding of entities and relationships.

This memory graph system enables the vision of composable, explainable, and efficient multi-agent reasoning as outlined in the problem statement.