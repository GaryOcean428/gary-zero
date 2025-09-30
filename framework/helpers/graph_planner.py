"""
Graph Planner Agent - Agent B

This agent performs read-only queries on the memory graph to answer questions
and provide reasoning. It uses the structured graph data for multi-hop reasoning
and explainable decision making.
"""

from typing import Dict, List, Optional, Any, Set
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


class GraphPlanner:
    """
    Agent B: Read-only querying and planning agent using the memory graph.
    
    This agent provides:
    - Multi-hop reasoning across graph relationships
    - Explainable decision paths
    - Context compression through subgraph extraction
    - Structured query responses
    """

    def __init__(self, graph: MemoryGraph):
        self.graph = graph

    def what_blocks_service(self, service_name: str, 
                          log_item: Optional[LogItem] = None) -> Dict[str, Any]:
        """
        Analyze what's blocking a service rollout or operation.
        
        Args:
            service_name: Name of the service to analyze
            log_item: Optional log item for progress tracking
        
        Returns:
            Dict with blocking factors and reasoning paths
        """
        if log_item:
            log_item.update(heading=f"Analyzing blocks for service: {service_name}")

        service_id = f"service:{service_name}"
        service_node = self.graph.get_node(service_id)
        
        if not service_node:
            return {
                "service": service_name,
                "found": False,
                "error": f"Service '{service_name}' not found in graph"
            }

        result = {
            "service": service_name,
            "found": True,
            "blocking_factors": [],
            "missing_env_vars": [],
            "related_incidents": [],
            "dependency_issues": [],
            "reasoning_paths": []
        }

        # Find missing environment variables
        missing_envs = self._find_missing_env_vars(service_id)
        result["missing_env_vars"] = missing_envs["missing"]
        result["blocking_factors"].extend(missing_envs["blocking_factors"])
        result["reasoning_paths"].extend(missing_envs["paths"])

        # Find related incidents
        incidents = self._find_related_incidents(service_id)
        result["related_incidents"] = incidents["incidents"]
        result["blocking_factors"].extend(incidents["blocking_factors"])
        result["reasoning_paths"].extend(incidents["paths"])

        # Find dependency issues
        deps = self._find_dependency_issues(service_id)
        result["dependency_issues"] = deps["issues"]
        result["blocking_factors"].extend(deps["blocking_factors"])
        result["reasoning_paths"].extend(deps["paths"])

        if log_item:
            log_item.update(
                result=f"Found {len(result['blocking_factors'])} blocking factors",
                analysis=result
            )

        return result

    def _find_missing_env_vars(self, service_id: str) -> Dict[str, Any]:
        """Find missing environment variables for a service."""
        # Get required environment variables
        required_envs = self.graph.get_neighbors(
            service_id, 
            relation_types=[RelationType.SERVICE_REQUIRES_ENVVAR],
            direction="out"
        )

        missing = []
        blocking_factors = []
        paths = []

        for env_node in required_envs:
            # Check if env var has a value or is properly configured
            if not env_node.props.get("value") and not env_node.props.get("configured"):
                missing.append({
                    "key": env_node.props.get("key"),
                    "node_id": env_node.id,
                    "reason": "Environment variable has no value set"
                })
                
                blocking_factors.append(f"Missing environment variable: {env_node.props.get('key')}")
                
                paths.append({
                    "type": "missing_env_var",
                    "path": [service_id, env_node.id],
                    "explanation": f"Service requires {env_node.props.get('key')} but it's not configured"
                })

        return {
            "missing": missing,
            "blocking_factors": blocking_factors,
            "paths": paths
        }

    def _find_related_incidents(self, service_id: str) -> Dict[str, Any]:
        """Find incidents that impact the service."""
        incidents = self.graph.get_neighbors(
            service_id,
            relation_types=[RelationType.INCIDENT_IMPACTS_SERVICE],
            direction="in"  # Incidents point to services they impact
        )

        incident_list = []
        blocking_factors = []
        paths = []

        for incident_node in incidents:
            incident_info = {
                "id": incident_node.props.get("id"),
                "description": incident_node.props.get("description", ""),
                "node_id": incident_node.id,
                "created_at": incident_node.created_at
            }
            incident_list.append(incident_info)
            
            blocking_factors.append(f"Active incident: {incident_info['id']}")
            
            paths.append({
                "type": "incident_impact",
                "path": [incident_node.id, service_id],
                "explanation": f"Incident {incident_info['id']} impacts service operations"
            })

        return {
            "incidents": incident_list,
            "blocking_factors": blocking_factors,
            "paths": paths
        }

    def _find_dependency_issues(self, service_id: str) -> Dict[str, Any]:
        """Find dependency-related issues for the service."""
        # Find services this service integrates with
        integrated_services = self.graph.get_neighbors(
            service_id,
            relation_types=[RelationType.SERVICE_INTEGRATES_WITH],
            direction="out"
        )

        issues = []
        blocking_factors = []
        paths = []

        for dep_service in integrated_services:
            # Check if dependency service has incidents
            dep_incidents = self.graph.get_neighbors(
                dep_service.id,
                relation_types=[RelationType.INCIDENT_IMPACTS_SERVICE],
                direction="in"
            )
            
            if dep_incidents:
                for incident in dep_incidents:
                    issue = {
                        "type": "dependency_incident",
                        "dependency_service": dep_service.props.get("name"),
                        "incident_id": incident.props.get("id"),
                        "description": incident.props.get("description", "")
                    }
                    issues.append(issue)
                    
                    blocking_factors.append(
                        f"Dependency {dep_service.props.get('name')} affected by {incident.props.get('id')}"
                    )
                    
                    paths.append({
                        "type": "multi_hop_dependency",
                        "path": [service_id, dep_service.id, incident.id],
                        "explanation": f"Service depends on {dep_service.props.get('name')} which is affected by {incident.props.get('id')}"
                    })

        return {
            "issues": issues,
            "blocking_factors": blocking_factors,
            "paths": paths
        }

    def find_related_incidents(self, service_name: str, max_hops: int = 2) -> Dict[str, Any]:
        """
        Find all incidents related to a service within N hops.
        
        Args:
            service_name: Name of the service
            max_hops: Maximum relationship hops to search
        
        Returns:
            Dict with related incidents and reasoning paths
        """
        service_id = f"service:{service_name}"
        
        # Get subgraph around the service
        subgraph = self.graph.get_subgraph(service_id, hops=max_hops)
        
        # Find all incidents in the subgraph
        incidents = subgraph.query_by_type(EntityType.INCIDENT)
        
        related = []
        for incident in incidents:
            # Find path from service to incident
            paths = self.graph.find_path(service_id, incident.id, max_hops)
            
            if paths:
                related.append({
                    "incident": {
                        "id": incident.props.get("id"),
                        "description": incident.props.get("description", ""),
                        "created_at": incident.created_at
                    },
                    "shortest_path": paths[0] if paths else [],
                    "path_length": len(paths[0]) - 1 if paths else 0,
                    "all_paths": paths
                })

        return {
            "service": service_name,
            "related_incidents": related,
            "total_incidents": len(related),
            "subgraph_stats": subgraph.stats()
        }

    def get_service_dependencies(self, service_name: str) -> Dict[str, Any]:
        """
        Get all dependencies for a service (environment variables, integrations).
        
        Args:
            service_name: Name of the service
        
        Returns:
            Dict with dependency information
        """
        service_id = f"service:{service_name}"
        service_node = self.graph.get_node(service_id)
        
        if not service_node:
            return {
                "service": service_name,
                "found": False,
                "error": f"Service '{service_name}' not found"
            }

        # Get environment variable dependencies
        env_vars = self.graph.get_neighbors(
            service_id,
            relation_types=[RelationType.SERVICE_REQUIRES_ENVVAR],
            direction="out"
        )

        # Get service integrations
        integrations = self.graph.get_neighbors(
            service_id,
            relation_types=[RelationType.SERVICE_INTEGRATES_WITH],
            direction="out"
        )

        return {
            "service": service_name,
            "found": True,
            "environment_variables": [
                {
                    "key": env.props.get("key"),
                    "value": env.props.get("value"),
                    "configured": bool(env.props.get("value") or env.props.get("configured")),
                    "node_id": env.id
                }
                for env in env_vars
            ],
            "integrations": [
                {
                    "service_name": integration.props.get("name"),
                    "node_id": integration.id
                }
                for integration in integrations
            ],
            "total_env_vars": len(env_vars),
            "total_integrations": len(integrations)
        }

    def analyze_impact_radius(self, entity_id: str, max_hops: int = 3) -> Dict[str, Any]:
        """
        Analyze the impact radius of an entity (service, incident, etc.).
        
        Args:
            entity_id: ID of the entity to analyze
            max_hops: Maximum hops to analyze
        
        Returns:
            Dict with impact analysis
        """
        entity = self.graph.get_node(entity_id)
        if not entity:
            return {
                "entity_id": entity_id,
                "found": False,
                "error": "Entity not found"
            }

        # Get subgraph
        subgraph = self.graph.get_subgraph(entity_id, hops=max_hops)
        
        # Analyze by entity type
        impact_by_type = {}
        for node_id, node in subgraph.nodes.items():
            if node_id != entity_id:  # Exclude the source entity
                entity_type = node.type.value
                if entity_type not in impact_by_type:
                    impact_by_type[entity_type] = []
                
                # Find path from source to this node
                paths = self.graph.find_path(entity_id, node_id, max_hops)
                
                impact_by_type[entity_type].append({
                    "node_id": node_id,
                    "name": node.props.get("name") or node.props.get("key") or node.props.get("id"),
                    "shortest_path_length": len(paths[0]) - 1 if paths else 0,
                    "properties": node.props
                })

        return {
            "entity_id": entity_id,
            "entity_type": entity.type.value,
            "entity_name": entity.props.get("name") or entity.props.get("key") or entity.props.get("id"),
            "found": True,
            "impact_radius": impact_by_type,
            "total_impacted_entities": sum(len(entities) for entities in impact_by_type.values()),
            "subgraph_stats": subgraph.stats()
        }

    def recommend_actions(self, service_name: str) -> Dict[str, Any]:
        """
        Recommend actions based on graph analysis.
        
        Args:
            service_name: Name of the service
        
        Returns:
            Dict with recommendations
        """
        # Get blocking factors
        blocks = self.what_blocks_service(service_name)
        
        recommendations = []
        priority_order = []

        if blocks["missing_env_vars"]:
            for env_var in blocks["missing_env_vars"]:
                recommendations.append({
                    "type": "configure_environment",
                    "priority": "high",
                    "action": f"Configure environment variable: {env_var['key']}",
                    "details": env_var,
                    "reasoning": "Required environment variable is missing"
                })
                priority_order.append("configure_environment")

        if blocks["related_incidents"]:
            for incident in blocks["related_incidents"]:
                recommendations.append({
                    "type": "resolve_incident",
                    "priority": "critical",
                    "action": f"Resolve incident: {incident['id']}",
                    "details": incident,
                    "reasoning": "Active incident is blocking service"
                })
                priority_order.append("resolve_incident")

        if blocks["dependency_issues"]:
            for issue in blocks["dependency_issues"]:
                recommendations.append({
                    "type": "address_dependency",
                    "priority": "medium",
                    "action": f"Address dependency issue with {issue['dependency_service']}",
                    "details": issue,
                    "reasoning": "Dependency service has issues that may impact this service"
                })
                priority_order.append("address_dependency")

        # Sort by priority
        priority_map = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_map.get(x["priority"], 3))

        return {
            "service": service_name,
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
            "priority_summary": {
                "critical": len([r for r in recommendations if r["priority"] == "critical"]),
                "high": len([r for r in recommendations if r["priority"] == "high"]),
                "medium": len([r for r in recommendations if r["priority"] == "medium"]),
                "low": len([r for r in recommendations if r["priority"] == "low"])
            },
            "analysis_used": blocks
        }

    def query_graph(self, query_type: str, **kwargs) -> Dict[str, Any]:
        """
        General graph query interface.
        
        Args:
            query_type: Type of query to perform
            **kwargs: Query parameters
        
        Returns:
            Query results
        """
        if query_type == "missing_env_vars":
            service_name = kwargs.get("service")
            if service_name:
                return self._find_missing_env_vars(f"service:{service_name}")
        
        elif query_type == "related_incidents":
            service_name = kwargs.get("service")
            max_hops = kwargs.get("max_hops", 2)
            if service_name:
                return self.find_related_incidents(service_name, max_hops)
        
        elif query_type == "service_dependencies":
            service_name = kwargs.get("service")
            if service_name:
                return self.get_service_dependencies(service_name)
        
        elif query_type == "impact_radius":
            entity_id = kwargs.get("entity_id")
            max_hops = kwargs.get("max_hops", 3)
            if entity_id:
                return self.analyze_impact_radius(entity_id, max_hops)
        
        else:
            return {
                "error": f"Unknown query type: {query_type}",
                "supported_types": [
                    "missing_env_vars", "related_incidents", 
                    "service_dependencies", "impact_radius"
                ]
            }

    def explain_reasoning(self, reasoning_paths: List[Dict[str, Any]]) -> str:
        """
        Generate human-readable explanation of reasoning paths.
        
        Args:
            reasoning_paths: List of reasoning path dictionaries
        
        Returns:
            Human-readable explanation
        """
        if not reasoning_paths:
            return "No reasoning paths available."

        explanations = []
        for i, path in enumerate(reasoning_paths, 1):
            path_type = path.get("type", "unknown")
            explanation = path.get("explanation", "")
            node_path = path.get("path", [])
            
            if path_type == "missing_env_var":
                explanations.append(f"{i}. Environment Variable Issue: {explanation}")
            elif path_type == "incident_impact":
                explanations.append(f"{i}. Incident Impact: {explanation}")
            elif path_type == "multi_hop_dependency":
                explanations.append(f"{i}. Dependency Chain: {explanation}")
            else:
                explanations.append(f"{i}. {explanation}")
            
            if len(node_path) > 2:
                path_str = " → ".join([node_id.split(":")[-1] for node_id in node_path])
                explanations.append(f"   Path: {path_str}")

        return "\n".join(explanations)

    def get_graph_summary(self) -> Dict[str, Any]:
        """Get a summary of the current graph state."""
        stats = self.graph.stats()
        
        # Find top services by connectivity
        service_nodes = self.graph.query_by_type(EntityType.SERVICE)
        service_connectivity = []
        
        for service in service_nodes:
            neighbors = self.graph.get_neighbors(service.id)
            service_connectivity.append({
                "service": service.props.get("name"),
                "connections": len(neighbors),
                "node_id": service.id
            })
        
        service_connectivity.sort(key=lambda x: x["connections"], reverse=True)
        
        return {
            "graph_stats": stats,
            "top_connected_services": service_connectivity[:5],
            "total_services": len(service_nodes),
            "timestamp": datetime.utcnow().isoformat()
        }