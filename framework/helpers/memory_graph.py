"""
Memory Graph System for Gary-Zero

This module provides a structured memory graph system that enables multi-agent
composability and reasoning through explicit entity-relationship modeling.

The graph complements the existing vector-based memory system by providing:
- Structured entity storage (Service, EnvVar, Incident, etc.)
- Explicit relationship modeling between entities
- Multi-hop reasoning capabilities for agents
- Composable outputs that can be queried by other agents
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict

# Import log conditionally to avoid dependency issues
try:
    from framework.helpers.log import LogItem
except ImportError:
    LogItem = None

# Import print style conditionally
try:
    from framework.helpers.print_style import PrintStyle
except ImportError:
    class PrintStyle:
        @staticmethod
        def error(msg):
            print(f"ERROR: {msg}")
        
        @staticmethod
        def standard(msg):
            print(msg)


class EntityType(Enum):
    """Supported entity types in the memory graph."""
    SERVICE = "Service"
    ENVVAR = "EnvVar"
    INCIDENT = "Incident"
    FEATURE = "Feature"
    ROUTE = "Route"
    PERMISSION = "Permission"
    INTEGRATION = "Integration"
    TICKET = "Ticket"
    CUSTOMER = "Customer"
    PLAN = "Plan"
    MODULE = "Module"


class RelationType(Enum):
    """Supported relationship types in the memory graph."""
    SERVICE_REQUIRES_ENVVAR = "SERVICE_REQUIRES_ENVVAR"
    INCIDENT_IMPACTS_SERVICE = "INCIDENT_IMPACTS_SERVICE"
    FEATURE_DEPENDS_ON = "FEATURE_DEPENDS_ON"
    ROUTE_REQUIRES_PERMISSION = "ROUTE_REQUIRES_PERMISSION"
    SERVICE_INTEGRATES_WITH = "SERVICE_INTEGRATES_WITH"
    TICKET_ASSIGNED_TO = "TICKET_ASSIGNED_TO"
    CUSTOMER_HAS_PLAN = "CUSTOMER_HAS_PLAN"
    PLAN_INCLUDES_MODULE = "PLAN_INCLUDES_MODULE"
    TICKET_RELATES_TO = "TICKET_RELATES_TO"


@dataclass
class Node:
    """Represents an entity node in the memory graph."""
    id: str
    type: EntityType
    props: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    source: Optional[str] = None  # Source pointer for auditability

    def __post_init__(self):
        if not self.id:
            # Generate ID based on type and key properties
            key_prop = self.props.get('name') or self.props.get('key') or self.props.get('id')
            if key_prop:
                self.id = f"{self.type.value.lower()}:{key_prop}"
            else:
                self.id = f"{self.type.value.lower()}:{uuid.uuid4().hex[:8]}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            "id": self.id,
            "type": self.type.value,
            "props": self.props,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source": self.source
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        """Create node from dictionary representation."""
        return cls(
            id=data["id"],
            type=EntityType(data["type"]),
            props=data.get("props", {}),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
            source=data.get("source")
        )


@dataclass
class Edge:
    """Represents a relationship edge in the memory graph."""
    type: RelationType
    from_node: str
    to_node: str
    props: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    source: Optional[str] = None  # Source pointer for auditability

    @property
    def id(self) -> str:
        """Generate unique edge ID."""
        return f"{self.from_node}--{self.type.value}-->{self.to_node}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert edge to dictionary representation."""
        return {
            "type": self.type.value,
            "from": self.from_node,
            "to": self.to_node,
            "props": self.props,
            "created_at": self.created_at,
            "source": self.source
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Edge':
        """Create edge from dictionary representation."""
        return cls(
            type=RelationType(data["type"]),
            from_node=data["from"],
            to_node=data["to"],
            props=data.get("props", {}),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            source=data.get("source")
        )


class MemoryGraph:
    """
    Memory graph for structured entity-relationship storage and querying.
    
    Provides multi-hop reasoning capabilities and composable agent outputs.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Edge] = {}
        self.node_edges: Dict[str, Set[str]] = defaultdict(set)  # node_id -> edge_ids
        self.storage_path = storage_path

    def upsert_node(self, node: Node) -> bool:
        """
        Insert or update a node in the graph.
        
        Returns:
            bool: True if node was created, False if updated
        """
        is_new = node.id not in self.nodes
        if not is_new:
            node.updated_at = datetime.utcnow().isoformat()
        
        self.nodes[node.id] = node
        return is_new

    def upsert_edge(self, edge: Edge) -> bool:
        """
        Insert or update an edge in the graph.
        
        Returns:
            bool: True if edge was created, False if updated
        """
        edge_id = edge.id
        is_new = edge_id not in self.edges
        
        self.edges[edge_id] = edge
        self.node_edges[edge.from_node].add(edge_id)
        self.node_edges[edge.to_node].add(edge_id)
        
        return is_new

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_neighbors(self, node_id: str, 
                     relation_types: Optional[List[RelationType]] = None,
                     direction: str = "both") -> List[Node]:
        """
        Get neighboring nodes connected to the given node.
        
        Args:
            node_id: ID of the source node
            relation_types: Filter by specific relationship types
            direction: "out", "in", or "both"
        
        Returns:
            List of neighboring nodes
        """
        neighbors = []
        edge_ids = self.node_edges.get(node_id, set())
        
        for edge_id in edge_ids:
            edge = self.edges.get(edge_id)
            if not edge:
                continue
                
            # Filter by relation type
            if relation_types and edge.type not in relation_types:
                continue
            
            # Determine neighbor based on direction
            neighbor_id = None
            if direction in ("out", "both") and edge.from_node == node_id:
                neighbor_id = edge.to_node
            elif direction in ("in", "both") and edge.to_node == node_id:
                neighbor_id = edge.from_node
            
            if neighbor_id and neighbor_id in self.nodes:
                neighbors.append(self.nodes[neighbor_id])
        
        return neighbors

    def find_path(self, from_node_id: str, to_node_id: str, 
                  max_hops: int = 3) -> List[List[str]]:
        """
        Find paths between two nodes using BFS.
        
        Args:
            from_node_id: Starting node ID
            to_node_id: Target node ID  
            max_hops: Maximum number of hops to search
        
        Returns:
            List of paths, where each path is a list of node IDs
        """
        if from_node_id == to_node_id:
            return [[from_node_id]]
        
        paths = []
        queue = [(from_node_id, [from_node_id])]
        visited = set()
        
        while queue:
            current_node, path = queue.pop(0)
            
            if len(path) > max_hops + 1:
                continue
                
            if current_node in visited and len(path) > 2:
                continue
                
            visited.add(current_node)
            
            neighbors = self.get_neighbors(current_node, direction="out")
            
            for neighbor in neighbors:
                new_path = path + [neighbor.id]
                
                if neighbor.id == to_node_id:
                    paths.append(new_path)
                elif len(new_path) <= max_hops + 1:
                    queue.append((neighbor.id, new_path))
        
        return paths

    def query_by_type(self, entity_type: EntityType, 
                     filters: Optional[Dict[str, Any]] = None) -> List[Node]:
        """
        Query nodes by entity type with optional property filters.
        
        Args:
            entity_type: Type of entities to find
            filters: Dict of property filters (key: value pairs)
        
        Returns:
            List of matching nodes
        """
        results = []
        
        for node in self.nodes.values():
            if node.type != entity_type:
                continue
                
            if filters:
                match = True
                for key, value in filters.items():
                    if node.props.get(key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            results.append(node)
        
        return results

    def get_subgraph(self, center_node_id: str, hops: int = 2) -> 'MemoryGraph':
        """
        Extract a subgraph around a central node within N hops.
        
        Args:
            center_node_id: ID of the central node
            hops: Number of hops to include
        
        Returns:
            New MemoryGraph containing the subgraph
        """
        subgraph = MemoryGraph()
        visited_nodes = set()
        current_layer = {center_node_id}
        
        # Add center node
        if center_node_id in self.nodes:
            subgraph.upsert_node(self.nodes[center_node_id])
            visited_nodes.add(center_node_id)
        
        # Expand by hops
        for _ in range(hops):
            next_layer = set()
            
            for node_id in current_layer:
                neighbors = self.get_neighbors(node_id)
                
                for neighbor in neighbors:
                    if neighbor.id not in visited_nodes:
                        subgraph.upsert_node(neighbor)
                        visited_nodes.add(neighbor.id)
                        next_layer.add(neighbor.id)
                
                # Add edges for current node
                edge_ids = self.node_edges.get(node_id, set())
                for edge_id in edge_ids:
                    edge = self.edges.get(edge_id)
                    if edge and (edge.from_node in visited_nodes and 
                               edge.to_node in visited_nodes):
                        subgraph.upsert_edge(edge)
            
            current_layer = next_layer
            if not current_layer:
                break
        
        return subgraph

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary representation."""
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges.values()]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], storage_path: Optional[str] = None) -> 'MemoryGraph':
        """Create graph from dictionary representation."""
        graph = cls(storage_path)
        
        # Load nodes
        for node_data in data.get("nodes", []):
            node = Node.from_dict(node_data)
            graph.upsert_node(node)
        
        # Load edges  
        for edge_data in data.get("edges", []):
            edge = Edge.from_dict(edge_data)
            graph.upsert_edge(edge)
        
        return graph

    def save(self, path: Optional[str] = None) -> None:
        """Save graph to JSON file."""
        file_path = path or self.storage_path
        if not file_path:
            raise ValueError("No storage path specified")
        
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> 'MemoryGraph':
        """Load graph from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data, storage_path=path)

    def stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        node_types = defaultdict(int)
        edge_types = defaultdict(int)
        
        for node in self.nodes.values():
            node_types[node.type.value] += 1
        
        for edge in self.edges.values():
            edge_types[edge.type.value] += 1
        
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": dict(node_types),
            "edge_types": dict(edge_types)
        }