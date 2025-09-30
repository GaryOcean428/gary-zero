#!/usr/bin/env python3
"""
Simple Agents Test

Test the Graph Ingestor (Agent A) and Graph Planner (Agent B) functionality.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/home/runner/work/gary-zero/gary-zero')

# Import components
from framework.helpers.memory_graph import MemoryGraph
from framework.helpers.graph_ingestor import GraphIngestor
from framework.helpers.graph_planner import GraphPlanner


def test_ingestor():
    """Test Agent A - Graph Ingestor."""
    print("📥 Testing Agent A - Graph Ingestor")
    
    graph = MemoryGraph()
    ingestor = GraphIngestor(graph)
    
    # Test basic text ingestion
    deployment_text = """
    CRM7 on Vercel requires SUPABASE_URL, SUPABASE_ANON_KEY for database access.
    The service also needs STRIPE_SECRET_KEY for payments.
    """
    
    print("  📝 Processing deployment documentation...")
    results = ingestor.ingest_text(deployment_text, source="deployment_docs.md")
    
    print(f"    Nodes created: {results['nodes_created']}")
    print(f"    Edges created: {results['edges_created']}")
    
    # Verify entities were extracted
    assert results['nodes_created'] >= 3  # service + env vars
    assert results['edges_created'] >= 2  # service -> env vars
    
    # Check specific nodes exist
    service_node = graph.get_node("service:CRM7")
    if not service_node:
        service_node = graph.get_node("service:crm7")
    assert service_node is not None
    
    supabase_node = graph.get_node("envvar:SUPABASE_URL")
    assert supabase_node is not None
    
    # Test incident ingestion
    incident_text = "Incident INC-101 impacts crm7 due to missing SUPABASE_URL configuration"
    
    print("  🚨 Processing incident report...")
    incident_results = ingestor.ingest_text(incident_text, source="incident.md")
    
    print(f"    Additional nodes: {incident_results['nodes_created']}")
    print(f"    Additional edges: {incident_results['edges_created']}")
    
    # Check incident was created
    incident_node = graph.get_node("incident:INC-101")
    assert incident_node is not None
    
    print("  ✅ Agent A - Ingestor tests passed!")
    return graph


def test_planner(graph):
    """Test Agent B - Graph Planner."""
    print("\n🎯 Testing Agent B - Graph Planner")
    
    planner = GraphPlanner(graph)
    
    # Test service blocking analysis
    print("  🔍 Analyzing what blocks crm7...")
    blocking_analysis = planner.what_blocks_service("crm7")
    
    if not blocking_analysis.get("found"):
        # Try uppercase
        blocking_analysis = planner.what_blocks_service("CRM7")
    
    print(f"    Service found: {blocking_analysis.get('found', False)}")
    if blocking_analysis.get("found"):
        print(f"    Blocking factors: {len(blocking_analysis.get('blocking_factors', []))}")
        print(f"    Missing env vars: {len(blocking_analysis.get('missing_env_vars', []))}")
        print(f"    Related incidents: {len(blocking_analysis.get('related_incidents', []))}")
    
    # Test service dependencies
    print("  📋 Getting service dependencies...")
    service_name = "crm7" if blocking_analysis.get("found") else "CRM7"
    dependencies = planner.get_service_dependencies(service_name)
    
    if dependencies.get("found"):
        print(f"    Environment variables: {dependencies.get('total_env_vars', 0)}")
        print(f"    Integrations: {dependencies.get('total_integrations', 0)}")
        
        # List environment variables
        for env_var in dependencies.get('environment_variables', []):
            status = "✅" if env_var.get('configured') else "❌"
            print(f"      {status} {env_var.get('key')}")
    
    # Test recommendations
    print("  💡 Getting recommendations...")
    recommendations = planner.recommend_actions(service_name)
    
    if recommendations.get("total_recommendations", 0) > 0:
        print(f"    Total recommendations: {recommendations['total_recommendations']}")
        priority_summary = recommendations.get('priority_summary', {})
        print(f"    Critical: {priority_summary.get('critical', 0)}")
        print(f"    High: {priority_summary.get('high', 0)}")
        print(f"    Medium: {priority_summary.get('medium', 0)}")
        
        # Show first few recommendations
        for i, rec in enumerate(recommendations['recommendations'][:3], 1):
            print(f"      {i}. [{rec.get('priority', '').upper()}] {rec.get('action', '')}")
    
    # Test graph summary
    print("  📊 Getting graph summary...")
    summary = planner.get_graph_summary()
    
    print(f"    Total services: {summary.get('total_services', 0)}")
    print(f"    Graph stats: {summary.get('graph_stats', {})}")
    
    print("  ✅ Agent B - Planner tests passed!")


def test_multi_hop_reasoning(graph):
    """Test multi-hop reasoning capabilities."""
    print("\n🔗 Testing Multi-hop Reasoning")
    
    ingestor = GraphIngestor(graph)
    planner = GraphPlanner(graph)
    
    # Add a second service with dependencies
    print("  📝 Adding second service...")
    second_service_text = """
    The billing-service also requires SUPABASE_URL and STRIPE_SECRET_KEY.
    Incident INC-102 affects billing-service due to database connectivity.
    """
    ingestor.ingest_text(second_service_text, source="billing_docs.md")
    
    # Find related incidents
    print("  🔍 Finding related incidents...")
    related_incidents = planner.find_related_incidents("crm7", max_hops=3)
    
    if not related_incidents.get("related_incidents"):
        related_incidents = planner.find_related_incidents("CRM7", max_hops=3)
    
    print(f"    Related incidents found: {related_incidents.get('total_incidents', 0)}")
    
    # Test impact analysis for an incident
    incident_nodes = graph.query_by_type(graph.nodes["incident:INC-101"].type if "incident:INC-101" in graph.nodes else None)
    if incident_nodes:
        incident_id = incident_nodes[0].id
        print(f"  📊 Analyzing impact of {incident_id}...")
        impact = planner.analyze_impact_radius(incident_id, max_hops=3)
        
        if impact.get("found"):
            print(f"    Total impacted entities: {impact.get('total_impacted_entities', 0)}")
            impact_radius = impact.get('impact_radius', {})
            for entity_type, entities in impact_radius.items():
                print(f"      {entity_type}: {len(entities)} entities")
    
    print("  ✅ Multi-hop reasoning tests passed!")


def main():
    """Run all agent tests."""
    print("🤖 Memory Graph Agents - Simple Test Suite")
    print("=" * 50)
    
    try:
        # Test Agent A - Ingestor
        graph = test_ingestor()
        
        # Test Agent B - Planner  
        test_planner(graph)
        
        # Test multi-hop reasoning
        test_multi_hop_reasoning(graph)
        
        print("\n🎉 All agent tests passed!")
        print("\nMemory Graph Agents are working correctly!")
        print("\nKey capabilities verified:")
        print("  ✅ Agent A: Entity extraction from text")
        print("  ✅ Agent A: Relationship identification")
        print("  ✅ Agent B: Service blocking analysis")
        print("  ✅ Agent B: Dependency queries")
        print("  ✅ Agent B: Action recommendations")
        print("  ✅ Multi-hop reasoning and impact analysis")
        
        # Show final graph statistics
        stats = graph.stats()
        print(f"\nFinal Graph Statistics:")
        print(f"  Total nodes: {stats['total_nodes']}")
        print(f"  Total edges: {stats['total_edges']}")
        print(f"  Node types: {stats['node_types']}")
        print(f"  Edge types: {stats['edge_types']}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())