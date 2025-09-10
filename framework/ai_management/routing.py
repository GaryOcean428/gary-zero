"""Intelligent model routing and load balancing system.

This module provides sophisticated routing capabilities for AI models including:
- Intelligent model selection based on request characteristics
- Load balancing across model instances
- Circuit breaker patterns for fault tolerance  
- Geographic and cost-based routing
- Performance-based routing decisions
"""

import asyncio
import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class RoutingStrategy(str, Enum):
    """Model routing strategies."""
    
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_BASED = "performance_based"
    GEOGRAPHIC = "geographic"
    CAPABILITY_BASED = "capability_based"


class LoadBalancingAlgorithm(str, Enum):
    """Load balancing algorithms."""
    
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    LEAST_LOADED = "least_loaded"
    RANDOM = "random"
    CONSISTENT_HASH = "consistent_hash"


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class ModelInstance:
    """Model instance configuration."""
    
    id: str
    model_name: str
    model_version: str
    provider: str
    endpoint_url: str
    region: str = "us-east-1"
    weight: float = 1.0
    max_connections: int = 100
    current_connections: int = 0
    response_time_ms: float = 0.0
    success_rate: float = 1.0
    cost_per_request: float = 0.0
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    health_status: str = "healthy"
    last_health_check: datetime = field(default_factory=datetime.now)


@dataclass
class RoutingRequest:
    """Request for model routing."""
    
    prompt: str
    parameters: Dict[str, Any]
    required_capabilities: List[str] = field(default_factory=list)
    preferred_region: Optional[str] = None
    max_cost: Optional[float] = None
    max_latency_ms: Optional[float] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingResult:
    """Result of model routing decision."""
    
    selected_instance: ModelInstance
    routing_reason: str
    backup_instances: List[ModelInstance] = field(default_factory=list)
    estimated_cost: float = 0.0
    estimated_latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class CircuitBreaker:
    """Circuit breaker for model instances."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.half_open_max_calls = half_open_max_calls
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitBreakerState.CLOSED
        self.half_open_calls = 0
    
    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        now = datetime.now()
        
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        elif self.state == CircuitBreakerState.OPEN:
            if (
                self.last_failure_time and
                now - self.last_failure_time > timedelta(seconds=self.timeout_seconds)
            ):
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False
        
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return self.half_open_calls < self.half_open_max_calls
        
        return False
    
    def record_success(self):
        """Record successful execution."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0
    
    def record_failure(self):
        """Record failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
        elif (
            self.state == CircuitBreakerState.CLOSED and
            self.failure_count >= self.failure_threshold
        ):
            self.state = CircuitBreakerState.OPEN


class LoadBalancer(ABC):
    """Abstract load balancer."""
    
    @abstractmethod
    def select_instance(
        self,
        instances: List[ModelInstance],
        request: RoutingRequest
    ) -> Optional[ModelInstance]:
        """Select instance using load balancing algorithm."""
        pass


class RoundRobinBalancer(LoadBalancer):
    """Round-robin load balancer."""
    
    def __init__(self):
        self.current_index = 0
    
    def select_instance(
        self,
        instances: List[ModelInstance],
        request: RoutingRequest
    ) -> Optional[ModelInstance]:
        """Select next instance in round-robin fashion."""
        if not instances:
            return None
        
        instance = instances[self.current_index % len(instances)]
        self.current_index += 1
        return instance


class WeightedRoundRobinBalancer(LoadBalancer):
    """Weighted round-robin load balancer."""
    
    def __init__(self):
        self.current_weights: Dict[str, float] = {}
    
    def select_instance(
        self,
        instances: List[ModelInstance],
        request: RoutingRequest
    ) -> Optional[ModelInstance]:
        """Select instance using weighted round-robin."""
        if not instances:
            return None
        
        # Initialize weights if needed
        for instance in instances:
            if instance.id not in self.current_weights:
                self.current_weights[instance.id] = 0
        
        # Find instance with highest current weight
        best_instance = None
        best_weight = -1
        
        for instance in instances:
            self.current_weights[instance.id] += instance.weight
            if self.current_weights[instance.id] > best_weight:
                best_weight = self.current_weights[instance.id]
                best_instance = instance
        
        # Reduce selected instance's current weight
        if best_instance:
            total_weight = sum(i.weight for i in instances)
            self.current_weights[best_instance.id] -= total_weight
        
        return best_instance


class LeastConnectionsBalancer(LoadBalancer):
    """Least connections load balancer."""
    
    def select_instance(
        self,
        instances: List[ModelInstance],
        request: RoutingRequest
    ) -> Optional[ModelInstance]:
        """Select instance with least connections."""
        if not instances:
            return None
        
        return min(instances, key=lambda i: i.current_connections)


class LeastResponseTimeBalancer(LoadBalancer):
    """Least response time load balancer."""
    
    def select_instance(
        self,
        instances: List[ModelInstance],
        request: RoutingRequest
    ) -> Optional[ModelInstance]:
        """Select instance with lowest response time."""
        if not instances:
            return None
        
        return min(instances, key=lambda i: i.response_time_ms)


class CostOptimizedBalancer(LoadBalancer):
    """Cost-optimized load balancer."""
    
    def select_instance(
        self,
        instances: List[ModelInstance],
        request: RoutingRequest
    ) -> Optional[ModelInstance]:
        """Select most cost-effective instance."""
        if not instances:
            return None
        
        # Filter by max cost if specified
        if request.max_cost:
            instances = [i for i in instances if i.cost_per_request <= request.max_cost]
        
        if not instances:
            return None
        
        # Select cheapest instance with good performance
        return min(
            instances,
            key=lambda i: i.cost_per_request * (2 - i.success_rate)
        )


class ModelRouter:
    """Intelligent model routing system."""
    
    def __init__(self):
        self.instances: Dict[str, List[ModelInstance]] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.load_balancers: Dict[LoadBalancingAlgorithm, LoadBalancer] = {
            LoadBalancingAlgorithm.ROUND_ROBIN: RoundRobinBalancer(),
            LoadBalancingAlgorithm.WEIGHTED: WeightedRoundRobinBalancer(),
            LoadBalancingAlgorithm.LEAST_LOADED: LeastConnectionsBalancer(),
            LoadBalancingAlgorithm.RANDOM: self._create_random_balancer(),
        }
        self.routing_stats: Dict[str, Dict[str, Any]] = {}
    
    def _create_random_balancer(self) -> LoadBalancer:
        """Create random load balancer."""
        class RandomBalancer(LoadBalancer):
            def select_instance(self, instances, request):
                return random.choice(instances) if instances else None
        return RandomBalancer()
    
    def register_instance(self, instance: ModelInstance):
        """Register a model instance."""
        model_key = f"{instance.model_name}:{instance.model_version}"
        
        if model_key not in self.instances:
            self.instances[model_key] = []
        
        self.instances[model_key].append(instance)
        self.circuit_breakers[instance.id] = CircuitBreaker()
        
        logger.info(f"Registered model instance {instance.id} for {model_key}")
    
    def unregister_instance(self, instance_id: str):
        """Unregister a model instance."""
        for model_key, instances in self.instances.items():
            self.instances[model_key] = [
                i for i in instances if i.id != instance_id
            ]
        
        if instance_id in self.circuit_breakers:
            del self.circuit_breakers[instance_id]
        
        logger.info(f"Unregistered model instance {instance_id}")
    
    async def route_request(
        self,
        model_name: str,
        model_version: str,
        request: RoutingRequest,
        strategy: RoutingStrategy = RoutingStrategy.PERFORMANCE_BASED
    ) -> Optional[RoutingResult]:
        """Route request to best available model instance."""
        model_key = f"{model_name}:{model_version}"
        instances = self.instances.get(model_key, [])
        
        if not instances:
            logger.error(f"No instances available for {model_key}")
            return None
        
        # Filter healthy instances
        healthy_instances = await self._filter_healthy_instances(instances)
        
        if not healthy_instances:
            logger.error(f"No healthy instances available for {model_key}")
            return None
        
        # Apply routing strategy
        selected_instance = await self._apply_routing_strategy(
            healthy_instances, request, strategy
        )
        
        if not selected_instance:
            logger.error(f"No suitable instance found for {model_key}")
            return None
        
        # Calculate estimates
        estimated_cost = self._estimate_cost(selected_instance, request)
        estimated_latency = self._estimate_latency(selected_instance, request)
        
        # Get backup instances
        backup_instances = [
            i for i in healthy_instances 
            if i.id != selected_instance.id
        ][:2]  # Top 2 backups
        
        result = RoutingResult(
            selected_instance=selected_instance,
            routing_reason=f"Selected by {strategy.value} strategy",
            backup_instances=backup_instances,
            estimated_cost=estimated_cost,
            estimated_latency_ms=estimated_latency,
            metadata={
                'total_instances': len(instances),
                'healthy_instances': len(healthy_instances),
                'strategy': strategy.value
            }
        )
        
        # Update statistics
        self._update_routing_stats(model_key, selected_instance.id, strategy)
        
        return result
    
    async def _filter_healthy_instances(
        self,
        instances: List[ModelInstance]
    ) -> List[ModelInstance]:
        """Filter instances by health status and circuit breaker state."""
        healthy = []
        
        for instance in instances:
            # Check circuit breaker
            circuit_breaker = self.circuit_breakers.get(instance.id)
            if circuit_breaker and not circuit_breaker.can_execute():
                continue
            
            # Check health status
            if instance.health_status != "healthy":
                continue
            
            # Check connection limits
            if instance.current_connections >= instance.max_connections:
                continue
            
            healthy.append(instance)
        
        return healthy
    
    async def _apply_routing_strategy(
        self,
        instances: List[ModelInstance],
        request: RoutingRequest,
        strategy: RoutingStrategy
    ) -> Optional[ModelInstance]:
        """Apply routing strategy to select instance."""
        if strategy == RoutingStrategy.ROUND_ROBIN:
            return self.load_balancers[LoadBalancingAlgorithm.ROUND_ROBIN].select_instance(
                instances, request
            )
        
        elif strategy == RoutingStrategy.WEIGHTED_ROUND_ROBIN:
            return self.load_balancers[LoadBalancingAlgorithm.WEIGHTED].select_instance(
                instances, request
            )
        
        elif strategy == RoutingStrategy.LEAST_CONNECTIONS:
            return self.load_balancers[LoadBalancingAlgorithm.LEAST_LOADED].select_instance(
                instances, request
            )
        
        elif strategy == RoutingStrategy.LEAST_RESPONSE_TIME:
            return min(instances, key=lambda i: i.response_time_ms)
        
        elif strategy == RoutingStrategy.COST_OPTIMIZED:
            return self._select_cost_optimized(instances, request)
        
        elif strategy == RoutingStrategy.PERFORMANCE_BASED:
            return self._select_performance_based(instances, request)
        
        elif strategy == RoutingStrategy.GEOGRAPHIC:
            return self._select_geographic(instances, request)
        
        elif strategy == RoutingStrategy.CAPABILITY_BASED:
            return self._select_capability_based(instances, request)
        
        else:
            # Default to round-robin
            return self.load_balancers[LoadBalancingAlgorithm.ROUND_ROBIN].select_instance(
                instances, request
            )
    
    def _select_cost_optimized(
        self,
        instances: List[ModelInstance],
        request: RoutingRequest
    ) -> Optional[ModelInstance]:
        """Select instance optimized for cost."""
        # Filter by max cost
        if request.max_cost:
            instances = [i for i in instances if i.cost_per_request <= request.max_cost]
        
        if not instances:
            return None
        
        # Balance cost and performance
        scored_instances = []
        for instance in instances:
            cost_score = 1 / (instance.cost_per_request + 0.001)  # Avoid division by zero
            performance_score = instance.success_rate / (instance.response_time_ms + 1)
            total_score = 0.7 * cost_score + 0.3 * performance_score
            scored_instances.append((instance, total_score))
        
        return max(scored_instances, key=lambda x: x[1])[0]
    
    def _select_performance_based(
        self,
        instances: List[ModelInstance],
        request: RoutingRequest
    ) -> Optional[ModelInstance]:
        """Select instance optimized for performance."""
        # Filter by max latency
        if request.max_latency_ms:
            instances = [i for i in instances if i.response_time_ms <= request.max_latency_ms]
        
        if not instances:
            return None
        
        # Score based on multiple performance factors
        scored_instances = []
        for instance in instances:
            response_time_score = 1 / (instance.response_time_ms + 1)
            success_rate_score = instance.success_rate
            load_score = 1 / (instance.current_connections + 1)
            
            total_score = (
                0.4 * response_time_score +
                0.4 * success_rate_score +
                0.2 * load_score
            )
            scored_instances.append((instance, total_score))
        
        return max(scored_instances, key=lambda x: x[1])[0]
    
    def _select_geographic(
        self,
        instances: List[ModelInstance],
        request: RoutingRequest
    ) -> Optional[ModelInstance]:
        """Select instance based on geographic proximity."""
        if request.preferred_region:
            # Prefer instances in the same region
            same_region = [i for i in instances if i.region == request.preferred_region]
            if same_region:
                # Use performance-based selection within the region
                return self._select_performance_based(same_region, request)
        
        # Fallback to performance-based selection
        return self._select_performance_based(instances, request)
    
    def _select_capability_based(
        self,
        instances: List[ModelInstance],
        request: RoutingRequest
    ) -> Optional[ModelInstance]:
        """Select instance based on required capabilities."""
        if request.required_capabilities:
            # Filter instances that have all required capabilities
            capable_instances = []
            for instance in instances:
                if all(cap in instance.capabilities for cap in request.required_capabilities):
                    capable_instances.append(instance)
            
            if capable_instances:
                return self._select_performance_based(capable_instances, request)
        
        # Fallback to performance-based selection
        return self._select_performance_based(instances, request)
    
    def _estimate_cost(
        self,
        instance: ModelInstance,
        request: RoutingRequest
    ) -> float:
        """Estimate cost for the request."""
        # Simple estimation based on prompt length and model cost
        base_cost = instance.cost_per_request
        prompt_factor = len(request.prompt) / 1000  # Cost per 1K characters
        return base_cost * (1 + prompt_factor)
    
    def _estimate_latency(
        self,
        instance: ModelInstance,
        request: RoutingRequest
    ) -> float:
        """Estimate latency for the request."""
        # Simple estimation based on current load and typical response time
        base_latency = instance.response_time_ms
        load_factor = instance.current_connections / instance.max_connections
        return base_latency * (1 + load_factor * 0.5)
    
    def _update_routing_stats(
        self,
        model_key: str,
        instance_id: str,
        strategy: RoutingStrategy
    ):
        """Update routing statistics."""
        if model_key not in self.routing_stats:
            self.routing_stats[model_key] = {
                'total_requests': 0,
                'instances': {},
                'strategies': {}
            }
        
        stats = self.routing_stats[model_key]
        stats['total_requests'] += 1
        
        if instance_id not in stats['instances']:
            stats['instances'][instance_id] = 0
        stats['instances'][instance_id] += 1
        
        strategy_key = strategy.value
        if strategy_key not in stats['strategies']:
            stats['strategies'][strategy_key] = 0
        stats['strategies'][strategy_key] += 1
    
    async def record_request_result(
        self,
        instance_id: str,
        success: bool,
        response_time_ms: float,
        cost: float = 0.0
    ):
        """Record the result of a request for metrics and circuit breaker."""
        circuit_breaker = self.circuit_breakers.get(instance_id)
        if circuit_breaker:
            if success:
                circuit_breaker.record_success()
            else:
                circuit_breaker.record_failure()
        
        # Update instance metrics
        for instances in self.instances.values():
            for instance in instances:
                if instance.id == instance_id:
                    # Update response time (rolling average)
                    instance.response_time_ms = (
                        instance.response_time_ms * 0.9 + response_time_ms * 0.1
                    )
                    
                    # Update success rate (rolling average)
                    if success:
                        instance.success_rate = instance.success_rate * 0.95 + 0.05
                    else:
                        instance.success_rate = instance.success_rate * 0.95
                    
                    # Update cost
                    if cost > 0:
                        instance.cost_per_request = (
                            instance.cost_per_request * 0.9 + cost * 0.1
                        )
                    
                    break
    
    async def update_instance_connections(
        self,
        instance_id: str,
        delta: int
    ):
        """Update connection count for an instance."""
        for instances in self.instances.values():
            for instance in instances:
                if instance.id == instance_id:
                    instance.current_connections = max(
                        0, instance.current_connections + delta
                    )
                    break
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        stats = {
            'total_models': len(self.instances),
            'total_instances': sum(len(instances) for instances in self.instances.values()),
            'circuit_breaker_states': {},
            'model_stats': self.routing_stats.copy()
        }
        
        # Circuit breaker states
        for instance_id, cb in self.circuit_breakers.items():
            stats['circuit_breaker_states'][instance_id] = {
                'state': cb.state.value,
                'failure_count': cb.failure_count,
                'last_failure': cb.last_failure_time.isoformat() if cb.last_failure_time else None
            }
        
        return stats
    
    def get_instance_health(self) -> Dict[str, Any]:
        """Get health status of all instances."""
        health_data = {}
        
        for model_key, instances in self.instances.items():
            health_data[model_key] = []
            
            for instance in instances:
                circuit_breaker = self.circuit_breakers.get(instance.id)
                
                health_data[model_key].append({
                    'instance_id': instance.id,
                    'health_status': instance.health_status,
                    'circuit_breaker_state': circuit_breaker.state.value if circuit_breaker else 'unknown',
                    'current_connections': instance.current_connections,
                    'max_connections': instance.max_connections,
                    'response_time_ms': instance.response_time_ms,
                    'success_rate': instance.success_rate,
                    'last_health_check': instance.last_health_check.isoformat()
                })
        
        return health_data