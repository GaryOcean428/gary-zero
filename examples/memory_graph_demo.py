"""
Memory Graph Demo - CRM7 Scenario

This demo showcases the memory graph system with a practical example
involving CRM7 deployment and incident management.

Demonstrates:
- Agent A (Ingestor) extracting entities from text
- Agent B (Planner) performing multi-hop reasoning  
- Practical deployment scenario with environment variables and incidents
"""

import asyncio
import json
import tempfile
import os
from typing import Dict, Any

from framework.helpers.memory_graph import MemoryGraph, Node, Edge, EntityType, RelationType
from framework.helpers.graph_ingestor import GraphIngestor  
from framework.helpers.graph_planner import GraphPlanner
from framework.helpers.print_style import PrintStyle


class MemoryGraphDemo:
    """Demo class showcasing memory graph capabilities."""

    def __init__(self):
        self.graph = MemoryGraph()
        self.ingestor = GraphIngestor(self.graph)
        self.planner = GraphPlanner(self.graph)

    def run_demo(self):
        """Run the complete memory graph demonstration."""
        print("\n🧠 === MEMORY GRAPH SYSTEM DEMONSTRATION ===")
        print("Implementing structured memory for multi-agent reasoning\n")

        # Step 1: Demonstrate Agent A - Ingestor
        self.demo_ingestor()
        
        # Step 2: Demonstrate Agent B - Planner
        self.demo_planner()
        
        # Step 3: Multi-hop reasoning
        self.demo_multi_hop_reasoning()
        
        # Step 4: Show graph persistence
        self.demo_persistence()
        
        print("\n✅ Memory Graph demonstration completed!")
        print("The system successfully demonstrated:")
        print("- Entity extraction from unstructured text")
        print("- Relationship modeling between entities")
        print("- Multi-hop reasoning and decision making")
        print("- Graph persistence and loading")

    def demo_ingestor(self):
        """Demonstrate Agent A - Graph Ingestor capabilities."""
        print("📥 === AGENT A: GRAPH INGESTOR ===")
        print("Extracting entities and relationships from text sources\n")

        # Sample deployment documentation
        deployment_text = """
        CRM7 on Vercel requires SUPABASE_URL, SUPABASE_ANON_KEY for database access.
        The service also needs STRIPE_SECRET_KEY and SENDGRID_API_KEY for payments and emails.
        CRM7 integrates with the notification-service for alerts.
        """

        print(f"📝 Processing deployment documentation:")
        print(f"Text: {deployment_text.strip()}\n")

        # Extract entities and relationships
        results = self.ingestor.ingest_text(deployment_text, source="deployment_docs.md")
        
        self._print_extraction_results(results)

        # Add deployment log example
        deployment_log = """
        [2024-01-15 10:30:00] Starting CRM7 deployment
        [2024-01-15 10:30:05] Missing environment variable: SUPABASE_URL
        [2024-01-15 10:30:06] Required env var STRIPE_SECRET_KEY not found
        [2024-01-15 10:30:07] Deployment failed due to missing configuration
        """

        print(f"\n📊 Processing deployment log:")
        print(f"Log snippet: {deployment_log.strip()[:100]}...\n")

        log_results = self.ingestor.ingest_deployment_log(
            deployment_log, "crm7", source="deployment_log_2024_01_15.txt"
        )
        
        self._print_extraction_results(log_results)

        # Add incident information
        incident_text = """
        Incident INC-101 impacts crm7 due to missing SUPABASE_URL configuration.
        The outage affects the main service and blocks new user registrations.
        """

        print(f"\n🚨 Processing incident report:")
        print(f"Text: {incident_text.strip()}\n")

        incident_results = self.ingestor.ingest_text(incident_text, source="incident_report.md")
        self._print_extraction_results(incident_results)

    def demo_planner(self):
        """Demonstrate Agent B - Graph Planner capabilities."""
        print("\n🎯 === AGENT B: GRAPH PLANNER ===")
        print("Performing graph-based reasoning and analysis\n")

        # Analyze what's blocking CRM7
        print("🔍 Query: What's blocking CRM7 rollout?")
        blocking_analysis = self.planner.what_blocks_service("crm7")
        
        self._print_blocking_analysis(blocking_analysis)

        # Get service dependencies
        print("\n📋 Query: What are CRM7's dependencies?")
        dependencies = self.planner.get_service_dependencies("crm7")
        
        self._print_dependencies(dependencies)

        # Get recommendations
        print("\n💡 Query: What actions should we take?")
        recommendations = self.planner.recommend_actions("crm7")
        
        self._print_recommendations(recommendations)

    def demo_multi_hop_reasoning(self):
        """Demonstrate multi-hop reasoning capabilities."""
        print("\n🔗 === MULTI-HOP REASONING ===")
        print("Demonstrating reasoning across multiple relationships\n")

        # First, add a second service that depends on the same env vars
        second_service_text = """
        The billing-service also requires SUPABASE_URL and STRIPE_SECRET_KEY.
        Incident INC-102 affects billing-service due to database connectivity issues.
        """

        print("📝 Adding additional service context:")
        print(f"Text: {second_service_text.strip()}\n")

        self.ingestor.ingest_text(second_service_text, source="billing_service_docs.md")

        # Now find related incidents across services
        print("🔍 Query: Which incidents are related to current rollout risks?")
        related_incidents = self.planner.find_related_incidents("crm7", max_hops=3)
        
        self._print_related_incidents(related_incidents)

        # Analyze impact radius
        print("\n📊 Query: What's the impact radius of incident INC-101?")
        impact_analysis = self.planner.analyze_impact_radius("incident:INC-101", max_hops=3)
        
        self._print_impact_analysis(impact_analysis)

    def demo_persistence(self):
        """Demonstrate graph persistence and loading."""
        print("\n💾 === GRAPH PERSISTENCE ===")
        print("Demonstrating saving and loading graph state\n")

        # Save graph to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            # Save current graph
            self.graph.save(temp_path)
            print(f"✅ Graph saved to: {temp_path}")
            
            # Show graph stats
            stats = self.graph.stats()
            print(f"📊 Graph statistics:")
            for key, value in stats.items():
                print(f"   {key}: {value}")

            # Load graph into new instance
            loaded_graph = MemoryGraph.load(temp_path)
            loaded_stats = loaded_graph.stats()
            
            print(f"\n✅ Graph loaded successfully")
            print(f"📊 Loaded graph statistics:")
            for key, value in loaded_stats.items():
                print(f"   {key}: {value}")

            # Verify data integrity
            if stats == loaded_stats:
                print("✅ Data integrity verified - all data preserved")
            else:
                print("❌ Data integrity check failed")

        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def _print_extraction_results(self, results: Dict[str, Any]):
        """Print extraction results in a formatted way."""
        print(f"📊 Extraction Results:")
        print(f"   Nodes created: {results['nodes_created']}")
        print(f"   Nodes updated: {results['nodes_updated']}")
        print(f"   Edges created: {results['edges_created']}")
        print(f"   Edges updated: {results['edges_updated']}")
        
        if results['entities']:
            print(f"\n   🏷️  Entities extracted:")
            for entity in results['entities']:
                entity_type = entity['type']
                name = entity['props'].get('name') or entity['props'].get('key') or entity['props'].get('id')
                print(f"      {entity_type}: {name}")
        
        if results['relationships']:
            print(f"\n   🔗 Relationships extracted:")
            for rel in results['relationships']:
                from_node = rel['from'].split(':')[-1]
                to_node = rel['to'].split(':')[-1]
                rel_type = rel['type'].replace('_', ' ').title()
                print(f"      {from_node} → {rel_type} → {to_node}")

    def _print_blocking_analysis(self, analysis: Dict[str, Any]):
        """Print blocking analysis results."""
        if not analysis['found']:
            print(f"❌ {analysis['error']}")
            return

        print(f"📊 Blocking Analysis for {analysis['service']}:")
        print(f"   Total blocking factors: {len(analysis['blocking_factors'])}")
        
        if analysis['blocking_factors']:
            print(f"\n   🚫 Blocking Factors:")
            for factor in analysis['blocking_factors']:
                print(f"      • {factor}")
        
        if analysis['missing_env_vars']:
            print(f"\n   ⚠️  Missing Environment Variables:")
            for env_var in analysis['missing_env_vars']:
                print(f"      • {env_var['key']}: {env_var['reason']}")
        
        if analysis['related_incidents']:
            print(f"\n   🚨 Related Incidents:")
            for incident in analysis['related_incidents']:
                print(f"      • {incident['id']}: {incident['description'][:50]}...")
        
        # Show reasoning paths
        if analysis['reasoning_paths']:
            print(f"\n   🧠 Reasoning:")
            explanation = self.planner.explain_reasoning(analysis['reasoning_paths'])
            print(f"      {explanation.replace(chr(10), chr(10) + '      ')}")

    def _print_dependencies(self, dependencies: Dict[str, Any]):
        """Print service dependencies."""
        if not dependencies['found']:
            print(f"❌ {dependencies['error']}")
            return

        print(f"📋 Dependencies for {dependencies['service']}:")
        
        if dependencies['environment_variables']:
            print(f"\n   🔧 Environment Variables ({dependencies['total_env_vars']}):")
            for env_var in dependencies['environment_variables']:
                status = "✅ Configured" if env_var['configured'] else "❌ Missing"
                print(f"      • {env_var['key']}: {status}")
        
        if dependencies['integrations']:
            print(f"\n   🔗 Service Integrations ({dependencies['total_integrations']}):")
            for integration in dependencies['integrations']:
                print(f"      • {integration['service_name']}")

    def _print_recommendations(self, recommendations: Dict[str, Any]):
        """Print action recommendations."""
        print(f"💡 Recommendations for {recommendations['service']}:")
        print(f"   Total recommendations: {recommendations['total_recommendations']}")
        
        priority_summary = recommendations['priority_summary']
        print(f"   Priority breakdown: Critical({priority_summary['critical']}), "
              f"High({priority_summary['high']}), Medium({priority_summary['medium']}), "
              f"Low({priority_summary['low']})")
        
        if recommendations['recommendations']:
            print(f"\n   📝 Action Items:")
            for i, rec in enumerate(recommendations['recommendations'], 1):
                priority_icon = {"critical": "🔴", "high": "🟡", "medium": "🟠", "low": "🟢"}.get(rec['priority'], "⚪")
                print(f"      {i}. {priority_icon} [{rec['priority'].upper()}] {rec['action']}")
                print(f"         Reasoning: {rec['reasoning']}")

    def _print_related_incidents(self, incidents: Dict[str, Any]):
        """Print related incidents."""
        print(f"🚨 Related Incidents for {incidents['service']}:")
        print(f"   Total incidents found: {incidents['total_incidents']}")
        
        if incidents['related_incidents']:
            print(f"\n   📋 Incident Details:")
            for rel_incident in incidents['related_incidents']:
                incident = rel_incident['incident']
                path_length = rel_incident['path_length']
                print(f"      • {incident['id']}: {incident['description'][:50]}...")
                print(f"        Distance: {path_length} hops")
                if rel_incident['shortest_path']:
                    path_str = " → ".join([node_id.split(":")[-1] for node_id in rel_incident['shortest_path']])
                    print(f"        Path: {path_str}")

    def _print_impact_analysis(self, analysis: Dict[str, Any]):
        """Print impact analysis."""
        if not analysis['found']:
            print(f"❌ {analysis['error']}")
            return

        print(f"📊 Impact Analysis for {analysis['entity_name']} ({analysis['entity_type']}):")
        print(f"   Total impacted entities: {analysis['total_impacted_entities']}")
        
        if analysis['impact_radius']:
            print(f"\n   🎯 Impact by Entity Type:")
            for entity_type, entities in analysis['impact_radius'].items():
                print(f"      {entity_type} ({len(entities)}):")
                for entity in entities[:3]:  # Show first 3
                    print(f"        • {entity['name']} (distance: {entity['shortest_path_length']})")
                if len(entities) > 3:
                    print(f"        ... and {len(entities) - 3} more")


def main():
    """Run the memory graph demonstration."""
    try:
        demo = MemoryGraphDemo()
        demo.run_demo()
    except Exception as e:
        PrintStyle.error(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()