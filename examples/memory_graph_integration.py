#!/usr/bin/env python3
"""
Memory Graph Integration Example

Shows how to integrate the memory graph system with Gary-Zero's existing
memory and agent infrastructure.
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, '/home/runner/work/gary-zero/gary-zero')

# Import memory graph components
from framework.helpers.memory_graph import MemoryGraph, EntityType, RelationType
from framework.helpers.graph_ingestor import GraphIngestor
from framework.helpers.graph_planner import GraphPlanner


class MemoryGraphIntegration:
    """
    Integration example showing how to use memory graph with Gary-Zero.
    
    This demonstrates the complete workflow from the problem statement:
    - Agent A extracts entities from text sources
    - Agent B answers questions using only the graph
    - Multi-hop reasoning across relationships
    """

    def __init__(self):
        self.graph = MemoryGraph()
        self.ingestor = GraphIngestor(self.graph)  # Agent A
        self.planner = GraphPlanner(self.graph)   # Agent B

    def demonstrate_crm7_scenario(self):
        """
        Complete CRM7 deployment scenario from the problem statement.
        """
        print("🏢 === CRM7 DEPLOYMENT SCENARIO ===")
        print("Demonstrating the 20-minute mini-experiment\n")

        # Step 1: Agent A processes deployment documentation
        print("📥 STEP 1: Agent A (Ingestor) processes documentation")
        deployment_docs = """
        CRM7 on Vercel requires SUPABASE_URL, SUPABASE_ANON_KEY for database access.
        The service also needs STRIPE_SECRET_KEY and SENDGRID_API_KEY.
        CRM7 integrates with notification-service for alerts.
        """

        print(f"Input: {deployment_docs.strip()[:100]}...")
        results = self.ingestor.ingest_text(deployment_docs, source="deployment_docs.md")
        
        print(f"✅ Extracted {results['nodes_created']} entities, {results['edges_created']} relationships")
        self._show_entities()

        # Step 2: Agent B answers deployment questions using only graph
        print("\n🎯 STEP 2: Agent B (Planner) answers using graph-only queries")
        
        print("❓ Question: What's blocking crm7 rollout?")
        blocking_analysis = self.planner.what_blocks_service("crm7")
        if not blocking_analysis.get("found"):
            blocking_analysis = self.planner.what_blocks_service("CRM7")
        
        if blocking_analysis.get("found"):
            print(f"📊 Found {len(blocking_analysis.get('blocking_factors', []))} blocking factors")
            for factor in blocking_analysis.get('blocking_factors', []):
                print(f"   • {factor}")
        else:
            print("ℹ️  No blocking factors found (service ready for deployment)")

        # Step 3: Add incident for multi-hop reasoning
        print("\n🚨 STEP 3: Adding incident for multi-hop reasoning")
        incident_report = """
        Incident INC-101 impacts crm7 due to missing SUPABASE_URL configuration.
        The outage affects user authentication and new registrations.
        """

        print(f"Input: {incident_report.strip()[:80]}...")
        self.ingestor.ingest_text(incident_report, source="incident_INC-101.md")
        
        # Now query related incidents
        print("\n❓ Question: Which incidents are related to current rollout risks?")
        service_name = "crm7" if blocking_analysis.get("found") else "CRM7"
        related_incidents = self.planner.find_related_incidents(service_name, max_hops=2)
        
        print(f"📊 Found {related_incidents.get('total_incidents', 0)} related incidents")
        for incident_info in related_incidents.get('related_incidents', []):
            incident = incident_info['incident']
            path_length = incident_info['path_length']
            print(f"   • {incident['id']}: {incident['description'][:50]}... (distance: {path_length} hops)")

        # Step 4: Multi-hop reasoning demonstration
        print("\n🔗 STEP 4: Multi-hop reasoning demonstration")
        
        # Add second service that shares dependencies
        second_service_docs = """
        The billing-service also requires SUPABASE_URL and STRIPE_SECRET_KEY.
        Incident INC-102 affects billing-service due to payment gateway timeout.
        """

        print("📝 Adding billing-service context...")
        self.ingestor.ingest_text(second_service_docs, source="billing_service_docs.md")

        # Analyze impact radius
        print("\n❓ Question: What's the impact radius of incident INC-101?")
        impact_analysis = self.planner.analyze_impact_radius("incident:INC-101", max_hops=3)
        
        if impact_analysis.get("found"):
            print(f"📊 Impact analysis for {impact_analysis['entity_name']}:")
            print(f"   Total impacted entities: {impact_analysis['total_impacted_entities']}")
            
            impact_radius = impact_analysis.get('impact_radius', {})
            for entity_type, entities in impact_radius.items():
                print(f"   {entity_type}: {len(entities)} entities affected")
                for entity in entities[:2]:  # Show first 2
                    print(f"     - {entity['name']} (distance: {entity['shortest_path_length']})")

        # Step 5: Get actionable recommendations
        print("\n💡 STEP 5: Get actionable recommendations")
        recommendations = self.planner.recommend_actions(service_name)
        
        print(f"📋 Action recommendations for {service_name}:")
        print(f"   Total recommendations: {recommendations['total_recommendations']}")
        
        priority_summary = recommendations.get('priority_summary', {})
        print(f"   Priority breakdown: Critical({priority_summary.get('critical', 0)}), "
              f"High({priority_summary.get('high', 0)}), Medium({priority_summary.get('medium', 0)})")

        if recommendations.get('recommendations'):
            print("\n   📝 Prioritized actions:")
            for i, rec in enumerate(recommendations['recommendations'][:3], 1):
                priority_icon = {"critical": "🔴", "high": "🟡", "medium": "🟠", "low": "🟢"}.get(rec.get('priority'), "⚪")
                print(f"      {i}. {priority_icon} [{rec.get('priority', '').upper()}] {rec.get('action', '')}")
                print(f"         💭 {rec.get('reasoning', '')}")

        # Final graph statistics
        print(f"\n📊 Final Graph State:")
        stats = self.graph.stats()
        print(f"   Nodes: {stats['total_nodes']} | Edges: {stats['total_edges']}")
        print(f"   Entity types: {stats['node_types']}")
        print(f"   Relationship types: {stats['edge_types']}")

    def demonstrate_context_compression(self):
        """
        Demonstrate context compression capabilities.
        """
        print("\n📦 === CONTEXT COMPRESSION DEMO ===")
        print("Showing how subgraphs reduce context size\n")

        # Get full graph stats
        full_stats = self.graph.stats()
        print(f"Full graph: {full_stats['total_nodes']} nodes, {full_stats['total_edges']} edges")

        # Extract subgraph around CRM7
        service_name = "crm7"
        if not self.graph.get_node(f"service:{service_name}"):
            service_name = "CRM7"

        subgraph = self.graph.get_subgraph(f"service:{service_name}", hops=2)
        sub_stats = subgraph.stats()
        
        print(f"CRM7 subgraph (2 hops): {sub_stats['total_nodes']} nodes, {sub_stats['total_edges']} edges")
        
        compression_ratio = (1 - sub_stats['total_nodes'] / full_stats['total_nodes']) * 100
        print(f"Context compression: {compression_ratio:.1f}% reduction in entities")
        
        print("\n💡 This subgraph contains all relevant context for CRM7 planning")
        print("   without the noise of unrelated entities, enabling efficient agent reasoning.")

    def demonstrate_explainable_reasoning(self):
        """
        Demonstrate explainable reasoning paths.
        """
        print("\n🧠 === EXPLAINABLE REASONING DEMO ===")
        print("Showing traceable decision paths\n")

        # Get blocking analysis with reasoning paths
        service_name = "crm7" if self.graph.get_node("service:crm7") else "CRM7"
        analysis = self.planner.what_blocks_service(service_name)

        if analysis.get('reasoning_paths'):
            print("🔍 Reasoning paths for blocking factors:")
            explanation = self.planner.explain_reasoning(analysis['reasoning_paths'])
            print(f"   {explanation.replace(chr(10), chr(10) + '   ')}")
        else:
            print("ℹ️  No complex reasoning paths found (straightforward case)")

        print("\n💡 Every decision is traceable back to source entities and relationships")
        print("   enabling full auditability of agent reasoning.")

    def _show_entities(self):
        """Show extracted entities by type."""
        stats = self.graph.stats()
        
        print("📋 Extracted entities by type:")
        for entity_type, count in stats['node_types'].items():
            print(f"   {entity_type}: {count}")
            
            # Show some examples
            entities = self.graph.query_by_type(EntityType(entity_type))
            for entity in entities[:2]:  # Show first 2
                name = entity.props.get('name') or entity.props.get('key') or entity.props.get('id')
                print(f"     - {name}")

    def run_integration_demo(self):
        """Run the complete integration demonstration."""
        print("🧠 Gary-Zero Memory Graph Integration")
        print("=" * 50)
        print("Demonstrating structured memory for multi-agent reasoning\n")

        try:
            # Main scenario
            self.demonstrate_crm7_scenario()
            
            # Context compression
            self.demonstrate_context_compression()
            
            # Explainable reasoning
            self.demonstrate_explainable_reasoning()

            print("\n🎉 Integration demonstration completed successfully!")
            print("\n✅ Key capabilities demonstrated:")
            print("   • Agent A: Entity extraction from unstructured text")
            print("   • Agent B: Graph-only reasoning and planning")
            print("   • Multi-hop reasoning across entity relationships")
            print("   • Context compression through subgraph extraction") 
            print("   • Explainable decision paths with full traceability")
            print("   • Composable agent outputs (structured graph vs text)")

        except Exception as e:
            print(f"\n❌ Integration demo failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

        return 0


def main():
    """Run the memory graph integration demonstration."""
    demo = MemoryGraphIntegration()
    return demo.run_integration_demo()


if __name__ == "__main__":
    exit(main())