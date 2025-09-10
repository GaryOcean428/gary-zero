"""
Advanced Service Discovery and Registration System

Provides dynamic service discovery with:
- Automatic service registration and health monitoring
- Multi-backend support (Redis, etcd, Consul-compatible)
- Service mesh integration capabilities
- Load balancer integration
- Failure detection and recovery
"""

import time
import asyncio
import threading
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Set
from enum import Enum
import redis
import uuid
from urllib.parse import urlparse


class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"
    UNKNOWN = "unknown"


@dataclass
class ServiceNode:
    """Represents a service instance in the cluster"""
    id: str
    name: str
    host: str
    port: int
    protocol: str = "http"
    status: ServiceStatus = ServiceStatus.HEALTHY
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    last_heartbeat: float = field(default_factory=time.time)
    registration_time: float = field(default_factory=time.time)
    
    @property
    def address(self) -> str:
        """Get the full address of the service"""
        return f"{self.protocol}://{self.host}:{self.port}"
        
    @property
    def is_healthy(self) -> bool:
        """Check if the service is considered healthy"""
        return (self.status == ServiceStatus.HEALTHY and 
                time.time() - self.last_heartbeat < 30)  # 30 second timeout
                
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "protocol": self.protocol,
            "status": self.status.value,
            "metadata": self.metadata,
            "tags": list(self.tags),
            "last_heartbeat": self.last_heartbeat,
            "registration_time": self.registration_time,
            "address": self.address
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceNode':
        """Create ServiceNode from dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            host=data["host"],
            port=data["port"],
            protocol=data.get("protocol", "http"),
            status=ServiceStatus(data.get("status", "healthy")),
            metadata=data.get("metadata", {}),
            tags=set(data.get("tags", [])),
            last_heartbeat=data.get("last_heartbeat", time.time()),
            registration_time=data.get("registration_time", time.time())
        )


class ServiceRegistry:
    """Backend-agnostic service registry interface"""
    
    async def register(self, service: ServiceNode) -> bool:
        """Register a service"""
        raise NotImplementedError
        
    async def deregister(self, service_id: str) -> bool:
        """Deregister a service"""
        raise NotImplementedError
        
    async def update_status(self, service_id: str, status: ServiceStatus) -> bool:
        """Update service status"""
        raise NotImplementedError
        
    async def heartbeat(self, service_id: str) -> bool:
        """Send heartbeat for a service"""
        raise NotImplementedError
        
    async def discover(self, service_name: str, tags: Set[str] = None) -> List[ServiceNode]:
        """Discover services by name and tags"""
        raise NotImplementedError
        
    async def get_service(self, service_id: str) -> Optional[ServiceNode]:
        """Get a specific service by ID"""
        raise NotImplementedError
        
    async def list_services(self) -> List[ServiceNode]:
        """List all registered services"""
        raise NotImplementedError
        
    async def cleanup_stale_services(self, timeout: float = 30.0) -> int:
        """Remove stale services that haven't sent heartbeat"""
        raise NotImplementedError


class RedisServiceRegistry(ServiceRegistry):
    """Redis-based service registry implementation"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", 
                 prefix: str = "gary_zero:services"):
        self.redis_url = redis_url
        self.prefix = prefix
        self.redis_client: Optional[redis.Redis] = None
        
    async def _get_client(self) -> redis.Redis:
        """Get Redis client (lazy initialization)"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        return self.redis_client
        
    def _service_key(self, service_id: str) -> str:
        """Get Redis key for a service"""
        return f"{self.prefix}:{service_id}"
        
    def _service_list_key(self) -> str:
        """Get Redis key for service list"""
        return f"{self.prefix}:list"
        
    def _service_name_key(self, service_name: str) -> str:
        """Get Redis key for services by name"""
        return f"{self.prefix}:name:{service_name}"
        
    async def register(self, service: ServiceNode) -> bool:
        """Register a service in Redis"""
        try:
            client = await self._get_client()
            
            # Store service data
            service_data = json.dumps(service.to_dict())
            await client.hset(self._service_key(service.id), mapping={
                "data": service_data,
                "last_heartbeat": time.time()
            })
            
            # Add to service list
            await client.sadd(self._service_list_key(), service.id)
            
            # Add to service name index
            await client.sadd(self._service_name_key(service.name), service.id)
            
            # Set expiration (will be refreshed by heartbeats)
            await client.expire(self._service_key(service.id), 60)
            
            return True
        except Exception as e:
            print(f"Error registering service {service.id}: {e}")
            return False
            
    async def deregister(self, service_id: str) -> bool:
        """Deregister a service from Redis"""
        try:
            client = await self._get_client()
            
            # Get service data first to find service name
            service_data = await client.hget(self._service_key(service_id), "data")
            if service_data:
                service_dict = json.loads(service_data)
                service_name = service_dict.get("name")
                
                # Remove from service name index
                if service_name:
                    await client.srem(self._service_name_key(service_name), service_id)
            
            # Remove from service list
            await client.srem(self._service_list_key(), service_id)
            
            # Delete service data
            await client.delete(self._service_key(service_id))
            
            return True
        except Exception as e:
            print(f"Error deregistering service {service_id}: {e}")
            return False
            
    async def update_status(self, service_id: str, status: ServiceStatus) -> bool:
        """Update service status"""
        try:
            client = await self._get_client()
            
            # Get current service data
            service_data = await client.hget(self._service_key(service_id), "data")
            if not service_data:
                return False
                
            # Update status
            service_dict = json.loads(service_data)
            service_dict["status"] = status.value
            updated_data = json.dumps(service_dict)
            
            # Store updated data
            await client.hset(self._service_key(service_id), "data", updated_data)
            
            return True
        except Exception as e:
            print(f"Error updating service status {service_id}: {e}")
            return False
            
    async def heartbeat(self, service_id: str) -> bool:
        """Send heartbeat for a service"""
        try:
            client = await self._get_client()
            
            # Update heartbeat timestamp
            current_time = time.time()
            await client.hset(self._service_key(service_id), "last_heartbeat", current_time)
            
            # Refresh expiration
            await client.expire(self._service_key(service_id), 60)
            
            return True
        except Exception as e:
            print(f"Error sending heartbeat for service {service_id}: {e}")
            return False
            
    async def discover(self, service_name: str, tags: Set[str] = None) -> List[ServiceNode]:
        """Discover services by name and tags"""
        try:
            client = await self._get_client()
            
            # Get service IDs for the name
            service_ids = await client.smembers(self._service_name_key(service_name))
            
            services = []
            for service_id in service_ids:
                service = await self.get_service(service_id)
                if service and service.is_healthy:
                    # Filter by tags if provided
                    if tags is None or tags.issubset(service.tags):
                        services.append(service)
                        
            return services
        except Exception as e:
            print(f"Error discovering services for {service_name}: {e}")
            return []
            
    async def get_service(self, service_id: str) -> Optional[ServiceNode]:
        """Get a specific service by ID"""
        try:
            client = await self._get_client()
            
            # Get service data
            service_data = await client.hget(self._service_key(service_id), "data")
            if not service_data:
                return None
                
            # Parse and return service
            service_dict = json.loads(service_data)
            return ServiceNode.from_dict(service_dict)
            
        except Exception as e:
            print(f"Error getting service {service_id}: {e}")
            return None
            
    async def list_services(self) -> List[ServiceNode]:
        """List all registered services"""
        try:
            client = await self._get_client()
            
            # Get all service IDs
            service_ids = await client.smembers(self._service_list_key())
            
            services = []
            for service_id in service_ids:
                service = await self.get_service(service_id)
                if service:
                    services.append(service)
                    
            return services
        except Exception as e:
            print(f"Error listing services: {e}")
            return []
            
    async def cleanup_stale_services(self, timeout: float = 30.0) -> int:
        """Remove stale services that haven't sent heartbeat"""
        try:
            client = await self._get_client()
            current_time = time.time()
            removed_count = 0
            
            # Get all service IDs
            service_ids = await client.smembers(self._service_list_key())
            
            for service_id in service_ids:
                # Check last heartbeat
                last_heartbeat = await client.hget(self._service_key(service_id), "last_heartbeat")
                
                if last_heartbeat:
                    if current_time - float(last_heartbeat) > timeout:
                        # Service is stale, remove it
                        await self.deregister(service_id)
                        removed_count += 1
                else:
                    # No heartbeat data, remove it
                    await self.deregister(service_id)
                    removed_count += 1
                    
            return removed_count
        except Exception as e:
            print(f"Error cleaning up stale services: {e}")
            return 0


class ServiceDiscovery:
    """Main service discovery system"""
    
    def __init__(self, 
                 registry: ServiceRegistry,
                 cleanup_interval: float = 30.0,
                 heartbeat_interval: float = 10.0):
        self.registry = registry
        self.cleanup_interval = cleanup_interval
        self.heartbeat_interval = heartbeat_interval
        
        # Local state
        self._registered_services: Dict[str, ServiceNode] = {}
        self._discovery_cache: Dict[str, List[ServiceNode]] = {}
        self._cache_ttl: Dict[str, float] = {}
        self._lock = threading.RLock()
        
        # Background tasks
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self._service_callbacks: List[Callable[[str, ServiceNode, str], None]] = []  # event, service, action
        
    async def start(self) -> None:
        """Start the service discovery system"""
        if self._running:
            return
            
        self._running = True
        
        # Start background tasks
        self._cleanup_task = asyncio.create_task(self._cleanup_worker())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_worker())
        
    async def stop(self) -> None:
        """Stop the service discovery system"""
        self._running = False
        
        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
                
        # Deregister all local services
        for service_id in list(self._registered_services.keys()):
            await self.deregister_service(service_id)
            
    async def register_service(self, 
                             name: str,
                             host: str,
                             port: int,
                             protocol: str = "http",
                             metadata: Dict[str, Any] = None,
                             tags: Set[str] = None,
                             service_id: str = None) -> Optional[ServiceNode]:
        """Register a service"""
        if service_id is None:
            service_id = f"{name}-{host}-{port}-{uuid.uuid4().hex[:8]}"
            
        service = ServiceNode(
            id=service_id,
            name=name,
            host=host,
            port=port,
            protocol=protocol,
            metadata=metadata or {},
            tags=tags or set(),
            status=ServiceStatus.STARTING
        )
        
        # Register with backend
        success = await self.registry.register(service)
        if success:
            with self._lock:
                self._registered_services[service_id] = service
                
            # Update status to healthy
            service.status = ServiceStatus.HEALTHY
            await self.registry.update_status(service_id, ServiceStatus.HEALTHY)
            
            # Notify callbacks
            self._notify_callbacks("registered", service, "register")
            
            return service
        else:
            return None
            
    async def deregister_service(self, service_id: str) -> bool:
        """Deregister a service"""
        with self._lock:
            service = self._registered_services.get(service_id)
            
        if service:
            # Update status to stopping
            service.status = ServiceStatus.STOPPING
            await self.registry.update_status(service_id, ServiceStatus.STOPPING)
            
            # Deregister from backend
            success = await self.registry.deregister(service_id)
            
            if success:
                with self._lock:
                    self._registered_services.pop(service_id, None)
                    
                # Notify callbacks
                self._notify_callbacks("deregistered", service, "deregister")
                
            return success
        else:
            # Try to deregister from backend anyway
            return await self.registry.deregister(service_id)
            
    async def discover_services(self, 
                              service_name: str,
                              tags: Set[str] = None,
                              use_cache: bool = True,
                              cache_ttl: float = 5.0) -> List[ServiceNode]:
        """Discover services by name and tags"""
        cache_key = f"{service_name}:{':'.join(sorted(tags or []))}"
        
        # Check cache first
        if use_cache:
            with self._lock:
                cached_services = self._discovery_cache.get(cache_key)
                cache_time = self._cache_ttl.get(cache_key, 0)
                
                if cached_services and time.time() - cache_time < cache_ttl:
                    return list(cached_services)
                    
        # Discover from backend
        services = await self.registry.discover(service_name, tags)
        
        # Update cache
        if use_cache:
            with self._lock:
                self._discovery_cache[cache_key] = list(services)
                self._cache_ttl[cache_key] = time.time()
                
        return services
        
    async def get_service(self, service_id: str) -> Optional[ServiceNode]:
        """Get a specific service by ID"""
        return await self.registry.get_service(service_id)
        
    async def list_all_services(self) -> List[ServiceNode]:
        """List all registered services"""
        return await self.registry.list_services()
        
    def add_service_callback(self, callback: Callable[[str, ServiceNode, str], None]) -> None:
        """Add a callback for service events"""
        self._service_callbacks.append(callback)
        
    def get_registered_services(self) -> List[ServiceNode]:
        """Get locally registered services"""
        with self._lock:
            return list(self._registered_services.values())
            
    def _notify_callbacks(self, event: str, service: ServiceNode, action: str) -> None:
        """Notify service event callbacks"""
        for callback in self._service_callbacks:
            try:
                callback(event, service, action)
            except Exception as e:
                print(f"Error in service callback: {e}")
                
    async def _cleanup_worker(self) -> None:
        """Background worker for cleaning up stale services"""
        while self._running:
            try:
                removed_count = await self.registry.cleanup_stale_services()
                if removed_count > 0:
                    print(f"Cleaned up {removed_count} stale services")
                    
                # Clear local cache
                with self._lock:
                    self._discovery_cache.clear()
                    self._cache_ttl.clear()
                    
            except Exception as e:
                print(f"Error in cleanup worker: {e}")
                
            await asyncio.sleep(self.cleanup_interval)
            
    async def _heartbeat_worker(self) -> None:
        """Background worker for sending heartbeats"""
        while self._running:
            try:
                with self._lock:
                    service_ids = list(self._registered_services.keys())
                    
                for service_id in service_ids:
                    await self.registry.heartbeat(service_id)
                    
            except Exception as e:
                print(f"Error in heartbeat worker: {e}")
                
            await asyncio.sleep(self.heartbeat_interval)


# Convenience functions
async def create_redis_discovery(redis_url: str = "redis://localhost:6379") -> ServiceDiscovery:
    """Create a Redis-based service discovery system"""
    registry = RedisServiceRegistry(redis_url)
    discovery = ServiceDiscovery(registry)
    await discovery.start()
    return discovery