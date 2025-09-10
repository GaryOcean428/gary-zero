"""
Distributed Systems Framework for Gary-Zero

Provides enterprise-grade distributed computing capabilities:
- Service discovery and registration
- Load balancing and failover
- Clustering and consensus
- Distributed coordination
- Message routing and communication
"""

from .discovery import ServiceDiscovery, ServiceRegistry, ServiceNode
from .balancing import LoadBalancer, BalancingStrategy, HealthAwareBalancer
from .cluster import ClusterManager, NodeManager, ConsensusProtocol
from .coordination import DistributedCoordinator, DistributedLock, LeaderElection
from .messaging import MessageRouter, DistributedEventBus, MessageDelivery

__all__ = [
    "ServiceDiscovery",
    "ServiceRegistry", 
    "ServiceNode",
    "LoadBalancer",
    "BalancingStrategy",
    "HealthAwareBalancer",
    "ClusterManager",
    "NodeManager",
    "ConsensusProtocol",
    "DistributedCoordinator",
    "DistributedLock",
    "LeaderElection",
    "MessageRouter",
    "DistributedEventBus",
    "MessageDelivery",
]