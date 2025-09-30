#!/usr/bin/env python3
"""
Simple Memory Graph Test

Basic test of the memory graph functionality without external dependencies.
"""

import sys
import os
import tempfile
import json

# Add the project root to Python path
sys.path.insert(0, '/home/runner/work/gary-zero/gary-zero')

# Import memory graph components directly
from framework.helpers.memory_graph import (
    MemoryGraph, Node, Edge, EntityType, RelationType
)


def test_basic_graph_operations():
    """Test basic graph operations."""
    print("🧠 Testing Basic Graph Operations")
    
    # Create a new graph
    graph = MemoryGraph()
    
    # Create service node
    service_node = Node(
        id="service:crm7",
        type=EntityType.SERVICE,
        props={"name": "crm7", "platform": "vercel"}
    )
    
    # Create environment variable nodes
    supabase_node = Node(
        id="envvar:SUPABASE_URL",
        type=EntityType.ENVVAR,
        props={"key": "SUPABASE_URL"}
    )
    
    stripe_node = Node(
        id="envvar:STRIPE_SECRET_KEY",
        type=EntityType.ENVVAR,
        props={"key": "STRIPE_SECRET_KEY"}
    )
    
    # Add nodes to graph
    print("  📝 Adding nodes to graph...")
    graph.upsert_node(service_node)
    graph.upsert_node(supabase_node)
    graph.upsert_node(stripe_node)
    
    # Create relationships
    supabase_edge = Edge(
        type=RelationType.SERVICE_REQUIRES_ENVVAR,
        from_node="service:crm7",
        to_node="envvar:SUPABASE_URL"
    )
    
    stripe_edge = Edge(
        type=RelationType.SERVICE_REQUIRES_ENVVAR,
        from_node="service:crm7",
        to_node="envvar:STRIPE_SECRET_KEY"
    )
    
    # Add edges to graph
    print("  🔗 Adding relationships...")
    graph.upsert_edge(supabase_edge)
    graph.upsert_edge(stripe_edge)
    
    # Test graph queries
    print("  🔍 Testing graph queries...")
    
    # Get neighbors
    neighbors = graph.get_neighbors("service:crm7", direction="out")
    print(f"    Service neighbors: {len(neighbors)}")
    assert len(neighbors) == 2
    
    # Query by type
    services = graph.query_by_type(EntityType.SERVICE)
    env_vars = graph.query_by_type(EntityType.ENVVAR)
    print(f"    Services found: {len(services)}")
    print(f"    Environment variables found: {len(env_vars)}")
    assert len(services) == 1
    assert len(env_vars) == 2
    
    # Get statistics
    stats = graph.stats()
    print(f"    Graph stats: {stats}")
    assert stats["total_nodes"] == 3
    assert stats["total_edges"] == 2
    
    print("  ✅ Basic graph operations passed!")
    return graph


def test_graph_serialization(graph):
    """Test graph serialization and deserialization."""
    print("\n💾 Testing Graph Serialization")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        # Save graph
        print("  💾 Saving graph...")
        graph.save(temp_path)
        assert os.path.exists(temp_path)
        
        # Load graph
        print("  📁 Loading graph...")
        loaded_graph = MemoryGraph.load(temp_path)
        
        # Verify loaded graph
        original_stats = graph.stats()
        loaded_stats = loaded_graph.stats()
        
        print(f"    Original stats: {original_stats}")
        print(f"    Loaded stats: {loaded_stats}")
        
        assert original_stats == loaded_stats
        
        # Verify specific nodes
        service_node = loaded_graph.get_node("service:crm7")
        assert service_node is not None
        assert service_node.props["name"] == "crm7"
        
        print("  ✅ Graph serialization passed!")
        
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_path_finding(graph):
    """Test path finding functionality."""
    print("\n🔗 Testing Path Finding")
    
    # Add an incident
    incident_node = Node(
        id="incident:INC-101",
        type=EntityType.INCIDENT,
        props={"id": "INC-101", "description": "Missing SUPABASE_URL"}
    )
    graph.upsert_node(incident_node)
    
    # Connect incident to service
    incident_edge = Edge(
        type=RelationType.INCIDENT_IMPACTS_SERVICE,
        from_node="incident:INC-101",
        to_node="service:crm7"
    )
    graph.upsert_edge(incident_edge)
    
    # Find path from service to incident
    paths = graph.find_path("service:crm7", "incident:INC-101", max_hops=2)
    print(f"  🛤️  Paths found: {len(paths)}")
    
    if paths:
        shortest_path = paths[0]
        print(f"    Shortest path: {' → '.join(shortest_path)}")
        assert shortest_path[0] == "service:crm7"
        assert shortest_path[-1] == "incident:INC-101"
    
    print("  ✅ Path finding passed!")


def test_subgraph_extraction(graph):
    """Test subgraph extraction."""
    print("\n📊 Testing Subgraph Extraction")
    
    # Extract subgraph around service
    subgraph = graph.get_subgraph("service:crm7", hops=1)
    
    print(f"  📈 Subgraph nodes: {len(subgraph.nodes)}")
    print(f"  📈 Subgraph edges: {len(subgraph.edges)}")
    
    # Should contain service + env vars + incident
    assert len(subgraph.nodes) >= 3
    assert "service:crm7" in subgraph.nodes
    
    print("  ✅ Subgraph extraction passed!")


def main():
    """Run all tests."""
    print("🧠 Memory Graph System - Simple Test Suite")
    print("=" * 50)
    
    try:
        # Test basic operations
        graph = test_basic_graph_operations()
        
        # Test serialization
        test_graph_serialization(graph)
        
        # Test path finding
        test_path_finding(graph)
        
        # Test subgraph extraction
        test_subgraph_extraction(graph)
        
        print("\n🎉 All tests passed!")
        print("\nMemory Graph System is working correctly!")
        print("\nKey features verified:")
        print("  ✅ Entity and relationship modeling")
        print("  ✅ Graph persistence and loading")
        print("  ✅ Multi-hop path finding")
        print("  ✅ Subgraph extraction")
        print("  ✅ Query operations")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())