"""
Tests for Memory Graph System

Focused tests for the core memory graph functionality including:
- Node and Edge creation and serialization
- Graph operations (upsert, query, path finding)
- Ingestor entity extraction
- Planner reasoning capabilities
"""

import pytest
import tempfile
import json
import os
from typing import Dict, Any

from framework.helpers.memory_graph import (
    MemoryGraph, Node, Edge, EntityType, RelationType
)
from framework.helpers.graph_ingestor import GraphIngestor
from framework.helpers.graph_planner import GraphPlanner


class TestMemoryGraph:
    """Test core memory graph functionality."""

    def setup_method(self):
        """Set up test graph for each test."""
        self.graph = MemoryGraph()

    def test_node_creation_and_serialization(self):
        """Test node creation and dictionary conversion."""
        node = Node(
            id="service:crm7",
            type=EntityType.SERVICE,
            props={"name": "crm7", "platform": "vercel"}
        )
        
        assert node.id == "service:crm7"
        assert node.type == EntityType.SERVICE
        assert node.props["name"] == "crm7"
        
        # Test serialization
        node_dict = node.to_dict()
        assert node_dict["id"] == "service:crm7"
        assert node_dict["type"] == "Service"
        assert node_dict["props"]["name"] == "crm7"
        
        # Test deserialization
        restored_node = Node.from_dict(node_dict)
        assert restored_node.id == node.id
        assert restored_node.type == node.type
        assert restored_node.props == node.props

    def test_edge_creation_and_serialization(self):
        """Test edge creation and dictionary conversion."""
        edge = Edge(
            type=RelationType.SERVICE_REQUIRES_ENVVAR,
            from_node="service:crm7",
            to_node="envvar:SUPABASE_URL"
        )
        
        assert edge.type == RelationType.SERVICE_REQUIRES_ENVVAR  
        assert edge.from_node == "service:crm7"
        assert edge.to_node == "envvar:SUPABASE_URL"
        assert "SERVICE_REQUIRES_ENVVAR" in edge.id
        
        # Test serialization
        edge_dict = edge.to_dict()
        assert edge_dict["type"] == "SERVICE_REQUIRES_ENVVAR"
        assert edge_dict["from"] == "service:crm7"
        assert edge_dict["to"] == "envvar:SUPABASE_URL"
        
        # Test deserialization
        restored_edge = Edge.from_dict(edge_dict)
        assert restored_edge.type == edge.type
        assert restored_edge.from_node == edge.from_node
        assert restored_edge.to_node == edge.to_node

    def test_graph_upsert_operations(self):
        """Test upserting nodes and edges in the graph."""
        # Create and upsert nodes
        service_node = Node(
            id="service:crm7",
            type=EntityType.SERVICE,
            props={"name": "crm7"}
        )
        
        env_node = Node(
            id="envvar:SUPABASE_URL",
            type=EntityType.ENVVAR,
            props={"key": "SUPABASE_URL"}
        )
        
        # Test node upsert
        is_new_service = self.graph.upsert_node(service_node)
        is_new_env = self.graph.upsert_node(env_node)
        
        assert is_new_service == True
        assert is_new_env == True
        assert len(self.graph.nodes) == 2
        
        # Test updating existing node
        service_node.props["platform"] = "vercel"
        is_new_update = self.graph.upsert_node(service_node)
        assert is_new_update == False
        assert self.graph.nodes["service:crm7"].props["platform"] == "vercel"
        
        # Test edge upsert
        edge = Edge(
            type=RelationType.SERVICE_REQUIRES_ENVVAR,
            from_node="service:crm7",
            to_node="envvar:SUPABASE_URL"
        )
        
        is_new_edge = self.graph.upsert_edge(edge)
        assert is_new_edge == True
        assert len(self.graph.edges) == 1
        assert edge.id in self.graph.edges

    def test_graph_neighbors_and_queries(self):
        """Test neighbor finding and query operations."""
        # Set up test data
        self._setup_test_graph()
        
        # Test get neighbors
        service_neighbors = self.graph.get_neighbors("service:crm7", direction="out")
        assert len(service_neighbors) == 2  # Two env vars
        
        env_var_names = {neighbor.props.get("key") for neighbor in service_neighbors}
        assert "SUPABASE_URL" in env_var_names
        assert "STRIPE_SECRET_KEY" in env_var_names
        
        # Test filtered neighbors
        service_env_neighbors = self.graph.get_neighbors(
            "service:crm7",
            relation_types=[RelationType.SERVICE_REQUIRES_ENVVAR],
            direction="out"
        )
        assert len(service_env_neighbors) == 2
        
        # Test query by type
        services = self.graph.query_by_type(EntityType.SERVICE)
        assert len(services) == 1
        assert services[0].props["name"] == "crm7"
        
        env_vars = self.graph.query_by_type(EntityType.ENVVAR)
        assert len(env_vars) == 2

    def test_graph_path_finding(self):
        """Test path finding between nodes."""
        # Set up test data with path: service -> env_var -> incident
        self._setup_test_graph()
        
        # Add incident that affects the env var
        incident_node = Node(
            id="incident:INC-101",
            type=EntityType.INCIDENT,
            props={"id": "INC-101", "description": "Missing SUPABASE_URL"}
        )
        self.graph.upsert_node(incident_node)
        
        # Connect incident to service
        incident_edge = Edge(
            type=RelationType.INCIDENT_IMPACTS_SERVICE,
            from_node="incident:INC-101",
            to_node="service:crm7"
        )
        self.graph.upsert_edge(incident_edge)
        
        # Find path from service to incident
        paths = self.graph.find_path("service:crm7", "incident:INC-101", max_hops=2)
        assert len(paths) > 0
        
        # Check shortest path
        shortest_path = paths[0]
        assert shortest_path[0] == "service:crm7"
        assert shortest_path[-1] == "incident:INC-101"

    def test_graph_subgraph_extraction(self):
        """Test subgraph extraction around a node."""
        self._setup_test_graph()
        
        # Extract subgraph around service
        subgraph = self.graph.get_subgraph("service:crm7", hops=1)
        
        # Should contain service + 2 env vars = 3 nodes
        assert len(subgraph.nodes) == 3
        assert "service:crm7" in subgraph.nodes
        assert "envvar:SUPABASE_URL" in subgraph.nodes
        assert "envvar:STRIPE_SECRET_KEY" in subgraph.nodes
        
        # Should contain 2 edges (service -> env vars)
        assert len(subgraph.edges) == 2

    def test_graph_persistence(self):
        """Test saving and loading graphs."""
        self._setup_test_graph()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Save graph
            self.graph.save(temp_path)
            assert os.path.exists(temp_path)
            
            # Load graph
            loaded_graph = MemoryGraph.load(temp_path)
            
            # Verify loaded graph
            assert len(loaded_graph.nodes) == len(self.graph.nodes)
            assert len(loaded_graph.edges) == len(self.graph.edges)
            
            # Check specific nodes
            assert "service:crm7" in loaded_graph.nodes
            assert loaded_graph.nodes["service:crm7"].props["name"] == "crm7"
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_graph_statistics(self):
        """Test graph statistics generation."""
        self._setup_test_graph()
        
        stats = self.graph.stats()
        assert stats["total_nodes"] == 3
        assert stats["total_edges"] == 2
        assert "Service" in stats["node_types"]
        assert "EnvVar" in stats["node_types"] 
        assert stats["node_types"]["Service"] == 1
        assert stats["node_types"]["EnvVar"] == 2
        assert "SERVICE_REQUIRES_ENVVAR" in stats["edge_types"]

    def _setup_test_graph(self):
        """Set up a simple test graph with service and env vars."""
        # Create service node
        service_node = Node(
            id="service:crm7",
            type=EntityType.SERVICE,
            props={"name": "crm7", "platform": "vercel"}
        )
        self.graph.upsert_node(service_node)
        
        # Create env var nodes
        env_nodes = [
            Node(
                id="envvar:SUPABASE_URL",
                type=EntityType.ENVVAR,
                props={"key": "SUPABASE_URL"}
            ),
            Node(
                id="envvar:STRIPE_SECRET_KEY", 
                type=EntityType.ENVVAR,
                props={"key": "STRIPE_SECRET_KEY"}
            )
        ]
        
        for env_node in env_nodes:
            self.graph.upsert_node(env_node)
            
            # Create edge from service to env var
            edge = Edge(
                type=RelationType.SERVICE_REQUIRES_ENVVAR,
                from_node="service:crm7",
                to_node=env_node.id
            )
            self.graph.upsert_edge(edge)


class TestGraphIngestor:
    """Test graph ingestor functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.graph = MemoryGraph()
        self.ingestor = GraphIngestor(self.graph)

    def test_basic_text_ingestion(self):
        """Test basic entity extraction from text."""
        text = "crm7 requires SUPABASE_URL and STRIPE_SECRET_KEY for operation"
        
        results = self.ingestor.ingest_text(text, source="test.txt")
        
        assert results["nodes_created"] >= 3  # service + 2 env vars
        assert results["edges_created"] >= 2  # service -> env vars
        
        # Check that service was created
        service_node = self.graph.get_node("service:crm7")
        assert service_node is not None
        assert service_node.props["name"] == "crm7"
        
        # Check env vars were created
        supabase_node = self.graph.get_node("envvar:SUPABASE_URL")
        stripe_node = self.graph.get_node("envvar:STRIPE_SECRET_KEY")
        assert supabase_node is not None
        assert stripe_node is not None

    def test_incident_extraction(self):
        """Test incident extraction from text."""
        text = "incident INC-101 impacts crm7 due to missing configuration"
        
        results = self.ingestor.ingest_text(text, source="incident.txt")
        
        assert results["nodes_created"] >= 2  # incident + service
        assert results["edges_created"] >= 1  # incident -> service
        
        # Check incident was created
        incident_node = self.graph.get_node("incident:INC-101")
        assert incident_node is not None
        assert incident_node.props["id"] == "INC-101"

    def test_deployment_log_ingestion(self):
        """Test specialized deployment log processing."""
        log_text = """
        [2024-01-15] Starting deployment
        [2024-01-15] Missing environment variable: SUPABASE_URL
        [2024-01-15] Required STRIPE_SECRET_KEY not found
        """
        
        results = self.ingestor.ingest_deployment_log(log_text, "crm7", source="deploy.log")
        
        assert results["nodes_created"] >= 3  # service + env vars  
        assert results["edges_created"] >= 2  # service -> env vars
        
        # Verify service exists
        service_node = self.graph.get_node("service:crm7")
        assert service_node is not None


class TestGraphPlanner:
    """Test graph planner functionality."""

    def setup_method(self):
        """Set up test environment with sample data."""
        self.graph = MemoryGraph()
        self.ingestor = GraphIngestor(self.graph)
        self.planner = GraphPlanner(self.graph)
        
        # Set up test scenario
        self._setup_test_scenario()

    def test_service_blocking_analysis(self):
        """Test analysis of what's blocking a service."""
        result = self.planner.what_blocks_service("crm7")
        
        assert result["found"] == True
        assert result["service"] == "crm7"
        assert len(result["missing_env_vars"]) > 0
        assert len(result["blocking_factors"]) > 0

    def test_service_dependencies_query(self):
        """Test querying service dependencies."""
        result = self.planner.get_service_dependencies("crm7")
        
        assert result["found"] == True
        assert result["total_env_vars"] >= 2
        assert len(result["environment_variables"]) >= 2
        
        # Check specific env vars
        env_keys = {env["key"] for env in result["environment_variables"]}
        assert "SUPABASE_URL" in env_keys
        assert "STRIPE_SECRET_KEY" in env_keys

    def test_related_incidents_finding(self):
        """Test finding related incidents."""
        result = self.planner.find_related_incidents("crm7", max_hops=2)
        
        assert result["service"] == "crm7"
        assert result["total_incidents"] >= 1
        
        if result["related_incidents"]:
            incident = result["related_incidents"][0]
            assert "incident" in incident
            assert "shortest_path" in incident

    def test_recommendations_generation(self):
        """Test action recommendations."""
        result = self.planner.recommend_actions("crm7")
        
        assert result["service"] == "crm7"
        assert result["total_recommendations"] > 0
        assert "priority_summary" in result
        
        # Should have recommendations for missing env vars
        recommendations = result["recommendations"]
        env_recommendations = [r for r in recommendations if r["type"] == "configure_environment"]
        assert len(env_recommendations) > 0

    def test_impact_analysis(self):
        """Test impact radius analysis."""
        # Add incident first
        incident_node = Node(
            id="incident:INC-101",
            type=EntityType.INCIDENT,
            props={"id": "INC-101", "description": "Test incident"}
        )
        self.graph.upsert_node(incident_node)
        
        edge = Edge(
            type=RelationType.INCIDENT_IMPACTS_SERVICE,
            from_node="incident:INC-101",
            to_node="service:crm7"
        )
        self.graph.upsert_edge(edge)
        
        result = self.planner.analyze_impact_radius("incident:INC-101", max_hops=2)
        
        assert result["found"] == True
        assert result["entity_type"] == "Incident"
        assert result["total_impacted_entities"] > 0

    def test_query_interface(self):
        """Test general query interface."""
        # Test missing env vars query
        result = self.planner.query_graph("missing_env_vars", service="crm7")
        assert "missing" in result
        
        # Test service dependencies query
        result = self.planner.query_graph("service_dependencies", service="crm7")
        assert result.get("found") == True
        
        # Test invalid query type
        result = self.planner.query_graph("invalid_query")
        assert "error" in result

    def _setup_test_scenario(self):
        """Set up test scenario with CRM7 service and dependencies."""
        # Ingest service requirements
        text = "crm7 requires SUPABASE_URL and STRIPE_SECRET_KEY"
        self.ingestor.ingest_text(text, source="test_setup")
        
        # Add incident
        incident_text = "incident INC-101 impacts crm7"
        self.ingestor.ingest_text(incident_text, source="test_incident")


def test_integration_scenario():
    """Integration test with complete scenario."""
    graph = MemoryGraph()
    ingestor = GraphIngestor(graph)
    planner = GraphPlanner(graph)
    
    # Step 1: Ingest deployment documentation
    deployment_text = """
    CRM7 on Vercel requires SUPABASE_URL, SUPABASE_ANON_KEY for database.
    The service integrates with notification-service for alerts.
    """
    ingestor.ingest_text(deployment_text, source="docs")
    
    # Step 2: Ingest incident information
    incident_text = "Incident INC-101 impacts crm7 due to missing SUPABASE_URL"
    ingestor.ingest_text(incident_text, source="incident")
    
    # Step 3: Analyze service
    blocking_analysis = planner.what_blocks_service("crm7")
    assert blocking_analysis["found"] == True
    assert len(blocking_analysis["blocking_factors"]) > 0
    
    # Step 4: Get recommendations
    recommendations = planner.recommend_actions("crm7")
    assert recommendations["total_recommendations"] > 0
    
    # Step 5: Verify graph state
    stats = graph.stats()
    assert stats["total_nodes"] >= 4  # service, env vars, incident
    assert stats["total_edges"] >= 3  # service->env vars, incident->service


if __name__ == "__main__":
    pytest.main([__file__, "-v"])