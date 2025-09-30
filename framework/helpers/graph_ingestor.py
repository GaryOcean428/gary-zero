"""
Graph Ingestor Agent - Agent A

This agent extracts entities and relationships from text sources and 
upserts them into the memory graph. It serves as the "ingestion" layer
that transforms unstructured text into structured graph nodes and edges.
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from framework.helpers.memory_graph import (
    MemoryGraph, Node, Edge, EntityType, RelationType
)

# Import log and print style conditionally
try:
    from framework.helpers.log import LogItem
except ImportError:
    LogItem = None

try:
    from framework.helpers.print_style import PrintStyle
except ImportError:
    class PrintStyle:
        @staticmethod
        def error(msg):
            print(f"ERROR: {msg}")


class GraphIngestor:
    """
    Agent A: Extracts entities and relationships from text and upserts to graph.
    
    This agent uses pattern matching and structured extraction to identify:
    - Services and their dependencies
    - Environment variables required by services
    - Incidents and their impacts
    - Features and their dependencies
    """

    def __init__(self, graph: MemoryGraph):
        self.graph = graph
        self.extraction_patterns = self._build_extraction_patterns()

    def _build_extraction_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build regex patterns for entity and relationship extraction."""
        return {
            "service_envvar": [
                {
                    "pattern": r"(\w+)\s+(?:requires?|needs?)\s+([A-Z_][A-Z0-9_]*(?:\s*,\s*[A-Z_][A-Z0-9_]*)*)",
                    "entity_types": [EntityType.SERVICE, EntityType.ENVVAR],
                    "relation_type": RelationType.SERVICE_REQUIRES_ENVVAR
                },
                {
                    "pattern": r"(\w+)\s+(?:on|requires?)\s+(\w+)\s+(?:requires?|needs?)\s+([A-Z_][A-Z0-9_]*(?:\s*,\s*[A-Z_][A-Z0-9_]*)*)",
                    "entity_types": [EntityType.SERVICE, EntityType.ENVVAR],
                    "relation_type": RelationType.SERVICE_REQUIRES_ENVVAR
                }
            ],
            "incident_service": [
                {
                    "pattern": r"(?:incident|issue|problem)\s+([A-Z]+-\d+|\w+)\s+(?:impacts?|affects?|blocks?)\s+(\w+)",
                    "entity_types": [EntityType.INCIDENT, EntityType.SERVICE],
                    "relation_type": RelationType.INCIDENT_IMPACTS_SERVICE
                },
                {
                    "pattern": r"([A-Z]+-\d+).*?(?:missing|failed|error).*?([A-Z_][A-Z0-9_]*).*?(?:impacts?|affects?)\s+(\w+)",
                    "entity_types": [EntityType.INCIDENT, EntityType.ENVVAR, EntityType.SERVICE],
                    "relation_type": RelationType.INCIDENT_IMPACTS_SERVICE
                }
            ],
            "service_integration": [
                {
                    "pattern": r"(\w+)\s+(?:integrates? with|connects? to|uses?)\s+(\w+)",
                    "entity_types": [EntityType.SERVICE, EntityType.SERVICE],
                    "relation_type": RelationType.SERVICE_INTEGRATES_WITH
                }
            ]
        }

    def ingest_text(self, text: str, source: Optional[str] = None, 
                   log_item: Optional[LogItem] = None) -> Dict[str, Any]:
        """
        Extract entities and relationships from text and upsert to graph.
        
        Args:
            text: Source text to process
            source: Source identifier for auditability
            log_item: Optional log item for progress tracking
        
        Returns:
            Dict with extraction results and statistics
        """
        if log_item:
            log_item.update(heading="Extracting entities and relationships...")
            log_item.update(source_text=text[:200] + "..." if len(text) > 200 else text)

        results = {
            "nodes_created": 0,
            "nodes_updated": 0,
            "edges_created": 0,
            "edges_updated": 0,
            "entities": [],
            "relationships": []
        }

        # Extract using patterns
        for category, patterns in self.extraction_patterns.items():
            for pattern_config in patterns:
                matches = re.finditer(pattern_config["pattern"], text, re.IGNORECASE)
                
                for match in matches:
                    extracted = self._process_match(
                        match, pattern_config, source, category
                    )
                    
                    if extracted:
                        # Update results
                        for node, is_new in extracted["nodes"]:
                            if is_new:
                                results["nodes_created"] += 1
                            else:
                                results["nodes_updated"] += 1
                            results["entities"].append(node.to_dict())
                        
                        for edge, is_new in extracted["edges"]:
                            if is_new:
                                results["edges_created"] += 1
                            else:
                                results["edges_updated"] += 1
                            results["relationships"].append(edge.to_dict())

        # Try structured extraction for specific formats
        structured_results = self._extract_structured_content(text, source)
        
        # Merge structured results
        for node, is_new in structured_results["nodes"]:
            if is_new:
                results["nodes_created"] += 1
            else:
                results["nodes_updated"] += 1
            results["entities"].append(node.to_dict())
        
        for edge, is_new in structured_results["edges"]:
            if is_new:
                results["edges_created"] += 1
            else:
                results["edges_updated"] += 1
            results["relationships"].append(edge.to_dict())

        if log_item:
            log_item.update(
                result=f"Extracted {results['nodes_created']} new nodes, "
                      f"{results['edges_created']} new edges",
                stats=results
            )

        return results

    def _process_match(self, match, pattern_config: Dict[str, Any], 
                      source: Optional[str], category: str) -> Optional[Dict[str, List]]:
        """Process a regex match and extract entities/relationships."""
        groups = match.groups()
        entity_types = pattern_config["entity_types"]
        relation_type = pattern_config["relation_type"]
        
        nodes = []
        edges = []
        
        try:
            if category == "service_envvar":
                service_name = groups[0].strip()
                env_vars_str = groups[-1]  # Last group is env vars
                
                # Create service node
                service_node = Node(
                    id=f"service:{service_name}",
                    type=EntityType.SERVICE,
                    props={"name": service_name},
                    source=source
                )
                is_new = self.graph.upsert_node(service_node)
                nodes.append((service_node, is_new))
                
                # Extract environment variables
                env_vars = [var.strip() for var in re.split(r'[,\s]+', env_vars_str) 
                           if var.strip() and var.strip().isupper()]
                
                for env_var in env_vars:
                    # Create env var node
                    env_node = Node(
                        id=f"envvar:{env_var}",
                        type=EntityType.ENVVAR,
                        props={"key": env_var},
                        source=source
                    )
                    is_new = self.graph.upsert_node(env_node)
                    nodes.append((env_node, is_new))
                    
                    # Create relationship
                    edge = Edge(
                        type=relation_type,
                        from_node=service_node.id,
                        to_node=env_node.id,
                        source=source
                    )
                    is_new = self.graph.upsert_edge(edge)
                    edges.append((edge, is_new))
            
            elif category == "incident_service":
                if len(groups) >= 2:
                    incident_id = groups[0].strip()
                    service_name = groups[-1].strip()  # Last group is service
                    
                    # Create incident node
                    incident_node = Node(
                        id=f"incident:{incident_id}",
                        type=EntityType.INCIDENT,
                        props={"id": incident_id, "description": match.group(0)},
                        source=source
                    )
                    is_new = self.graph.upsert_node(incident_node)
                    nodes.append((incident_node, is_new))
                    
                    # Create service node
                    service_node = Node(
                        id=f"service:{service_name}",
                        type=EntityType.SERVICE,
                        props={"name": service_name},
                        source=source
                    )
                    is_new = self.graph.upsert_node(service_node)
                    nodes.append((service_node, is_new))
                    
                    # Create relationship
                    edge = Edge(
                        type=relation_type,
                        from_node=incident_node.id,
                        to_node=service_node.id,
                        source=source
                    )
                    is_new = self.graph.upsert_edge(edge)
                    edges.append((edge, is_new))
            
            elif category == "service_integration":
                service1_name = groups[0].strip()
                service2_name = groups[1].strip()
                
                # Create service nodes
                for service_name in [service1_name, service2_name]:
                    service_node = Node(
                        id=f"service:{service_name}",
                        type=EntityType.SERVICE,
                        props={"name": service_name},
                        source=source
                    )
                    is_new = self.graph.upsert_node(service_node)
                    nodes.append((service_node, is_new))
                
                # Create relationship
                edge = Edge(
                    type=relation_type,
                    from_node=f"service:{service1_name}",
                    to_node=f"service:{service2_name}",
                    source=source
                )
                is_new = self.graph.upsert_edge(edge)
                edges.append((edge, is_new))
        
        except Exception as e:
            PrintStyle.error(f"Error processing match: {e}")
            return None
        
        return {"nodes": nodes, "edges": edges}

    def _extract_structured_content(self, text: str, source: Optional[str]) -> Dict[str, List]:
        """Extract from structured content like JSON, YAML, or specific formats."""
        nodes = []
        edges = []
        
        # Try to extract structured data
        try:
            # Look for JSON-like structures
            json_matches = re.finditer(r'\{[^{}]*\}', text)
            for match in json_matches:
                try:
                    data = json.loads(match.group())
                    extracted = self._process_json_structure(data, source)
                    nodes.extend(extracted["nodes"])
                    edges.extend(extracted["edges"])
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass
        
        # Extract environment variable definitions
        env_patterns = [
            r'([A-Z_][A-Z0-9_]*)\s*=\s*["\']?([^"\'\n]+)["\']?',
            r'export\s+([A-Z_][A-Z0-9_]*)\s*=\s*["\']?([^"\'\n]+)["\']?'
        ]
        
        for pattern in env_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                env_key = match.group(1)
                env_value = match.group(2)
                
                env_node = Node(
                    id=f"envvar:{env_key}",
                    type=EntityType.ENVVAR,
                    props={"key": env_key, "value": env_value},
                    source=source
                )
                is_new = self.graph.upsert_node(env_node)
                nodes.append((env_node, is_new))
        
        return {"nodes": nodes, "edges": edges}

    def _process_json_structure(self, data: Dict[str, Any], source: Optional[str]) -> Dict[str, List]:
        """Process JSON structure to extract entities and relationships."""
        nodes = []
        edges = []
        
        # Handle different JSON structures
        if "services" in data:
            for service_data in data["services"]:
                if isinstance(service_data, dict) and "name" in service_data:
                    service_node = Node(
                        id=f"service:{service_data['name']}",
                        type=EntityType.SERVICE,
                        props=service_data,
                        source=source
                    )
                    is_new = self.graph.upsert_node(service_node)
                    nodes.append((service_node, is_new))
        
        if "environment" in data or "env" in data:
            env_data = data.get("environment", data.get("env", {}))
            for key, value in env_data.items():
                env_node = Node(
                    id=f"envvar:{key}",
                    type=EntityType.ENVVAR,
                    props={"key": key, "value": str(value)},
                    source=source
                )
                is_new = self.graph.upsert_node(env_node)
                nodes.append((env_node, is_new))
        
        return {"nodes": nodes, "edges": edges}

    def ingest_deployment_log(self, log_text: str, service_name: str, 
                            source: Optional[str] = None) -> Dict[str, Any]:
        """
        Specialized ingestion for deployment logs.
        
        Args:
            log_text: Deployment log content
            service_name: Name of the service being deployed
            source: Source identifier
        
        Returns:
            Extraction results
        """
        # Create service node
        service_node = Node(
            id=f"service:{service_name}",
            type=EntityType.SERVICE,
            props={"name": service_name, "type": "deployment"},
            source=source
        )
        self.graph.upsert_node(service_node)
        
        # Extract environment variables from deployment logs
        env_pattern = r'(?:Missing|Required|Setting|Loading|Using)\s+(?:env(?:ironment)?\s+)?(?:var(?:iable)?:?\s*)?([A-Z_][A-Z0-9_]*)'
        
        results = {
            "nodes_created": 1,
            "nodes_updated": 0,
            "edges_created": 0,
            "edges_updated": 0,
            "entities": [service_node.to_dict()],
            "relationships": []
        }
        
        matches = re.finditer(env_pattern, log_text, re.IGNORECASE)
        for match in matches:
            env_var = match.group(1)
            
            # Create env var node
            env_node = Node(
                id=f"envvar:{env_var}",
                type=EntityType.ENVVAR,
                props={"key": env_var},
                source=source
            )
            is_new = self.graph.upsert_node(env_node)
            
            if is_new:
                results["nodes_created"] += 1
            else:
                results["nodes_updated"] += 1
            results["entities"].append(env_node.to_dict())
            
            # Create relationship
            edge = Edge(
                type=RelationType.SERVICE_REQUIRES_ENVVAR,
                from_node=service_node.id,
                to_node=env_node.id,
                source=source
            )
            is_new = self.graph.upsert_edge(edge)
            
            if is_new:
                results["edges_created"] += 1
            else:
                results["edges_updated"] += 1
            results["relationships"].append(edge.to_dict())
        
        return results

    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get statistics about extraction patterns and results."""
        return {
            "total_patterns": sum(len(patterns) for patterns in self.extraction_patterns.values()),
            "pattern_categories": list(self.extraction_patterns.keys()),
            "graph_stats": self.graph.stats()
        }