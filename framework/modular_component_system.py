"""
Modular Component System for Gary-Zero Framework

This module implements a comprehensive, reusable component architecture that serves as the foundation
for the "Elevating the Vision" phase. It provides:

1. Self-contained, configurable components with standardized interfaces
2. A plugin-like system for extending functionality
3. Dynamic loading and lifecycle management
4. Event-driven communication between components
5. Built-in analytics and performance monitoring

Purpose:
- Enable rapid development of new features through component composition
- Provide a consistent user experience across all interface elements
- Support deep customization while maintaining system integrity
- Facilitate A/B testing and gradual feature rollouts

Architecture:
- BaseComponent: Abstract class defining the component interface
- ComponentRegistry: Central registry for component discovery and instantiation
- ComponentManager: Orchestrates component lifecycle and communication
- EventBus: Facilitates loose coupling between components
- ComponentAnalytics: Tracks component usage and performance

Future Expansion:
- Visual component editor for non-technical users
- Remote component loading for dynamic updates
- Component marketplace for third-party extensions
- Advanced caching and optimization strategies
"""

import asyncio
import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Union
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ComponentState(Enum):
    """Component lifecycle states"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing" 
    READY = "ready"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ERROR = "error"
    DESTROYED = "destroyed"


class ComponentType(Enum):
    """Component type classification for organization and discovery"""
    WIDGET = "widget"              # UI widgets (charts, tables, forms)
    PANEL = "panel"                # Larger UI sections (dashboards, settings)
    SERVICE = "service"            # Background services (analytics, sync)
    INTEGRATION = "integration"    # External system connectors
    WORKFLOW = "workflow"          # Process automation components
    VISUALIZATION = "visualization" # Data visualization components


@dataclass
class ComponentMetadata:
    """Rich metadata for component discovery and management"""
    id: str
    name: str
    version: str
    description: str
    author: str
    component_type: ComponentType
    category: str
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    min_framework_version: str = "1.0.0"
    max_framework_version: Optional[str] = None
    icon: Optional[str] = None
    thumbnail: Optional[str] = None
    documentation_url: Optional[str] = None
    support_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ComponentConfig:
    """Configuration structure for component instances"""
    instance_id: str
    component_id: str
    user_id: str
    workspace_id: str
    settings: Dict[str, Any] = field(default_factory=dict)
    layout: Dict[str, Any] = field(default_factory=dict)
    permissions: Dict[str, bool] = field(default_factory=dict)
    enabled: bool = True
    auto_start: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class EventBus:
    """
    Centralized event system for component communication.
    
    Enables loose coupling between components while providing
    powerful event-driven interactions and analytics.
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Dict] = []
        self._max_history = 1000
        
    def subscribe(self, event_type: str, callback: Callable) -> str:
        """Subscribe to an event type with automatic unsubscribe handling"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(callback)
        subscription_id = f"{event_type}_{id(callback)}"
        
        logger.debug(f"Subscribed to {event_type}: {subscription_id}")
        return subscription_id
    
    def unsubscribe(self, event_type: str, callback: Callable) -> bool:
        """Unsubscribe from an event type"""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from {event_type}")
                return True
            except ValueError:
                pass
        return False
    
    async def emit(self, event_type: str, data: Any = None, source: str = None) -> None:
        """Emit an event to all subscribers with analytics tracking"""
        event = {
            'id': str(uuid.uuid4()),
            'type': event_type,
            'data': data,
            'source': source,
            'timestamp': datetime.now().isoformat(),
            'subscriber_count': len(self._subscribers.get(event_type, []))
        }
        
        # Store event for analytics
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Notify subscribers
        if event_type in self._subscribers:
            tasks = []
            for callback in self._subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        tasks.append(callback(event))
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback for {event_type}: {e}")
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_event_stats(self) -> Dict[str, Any]:
        """Get analytics about event usage"""
        event_counts = {}
        for event in self._event_history:
            event_type = event['type']
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            'total_events': len(self._event_history),
            'event_types': len(self._subscribers),
            'event_counts': event_counts,
            'active_subscriptions': {
                event_type: len(callbacks) 
                for event_type, callbacks in self._subscribers.items()
            }
        }


class ComponentAnalytics:
    """
    Component usage and performance analytics system.
    
    Tracks component lifecycle, performance metrics, user interactions,
    and provides insights for optimization and feature development.
    """
    
    def __init__(self):
        self._metrics: Dict[str, List[Dict]] = {}
        self._performance_data: Dict[str, List[float]] = {}
        self._user_interactions: List[Dict] = []
        self._error_log: List[Dict] = []
    
    def track_component_lifecycle(self, component_id: str, state: ComponentState, 
                                 metadata: Optional[Dict] = None) -> None:
        """Track component state changes"""
        if component_id not in self._metrics:
            self._metrics[component_id] = []
        
        self._metrics[component_id].append({
            'timestamp': datetime.now().isoformat(),
            'state': state.value,
            'metadata': metadata or {}
        })
    
    def track_performance(self, component_id: str, operation: str, 
                         duration: float, metadata: Optional[Dict] = None) -> None:
        """Track component performance metrics"""
        key = f"{component_id}_{operation}"
        if key not in self._performance_data:
            self._performance_data[key] = []
        
        self._performance_data[key].append(duration)
        
        # Keep only recent data to prevent memory bloat
        if len(self._performance_data[key]) > 1000:
            self._performance_data[key] = self._performance_data[key][-500:]
    
    def track_user_interaction(self, component_id: str, action: str, 
                              user_id: str, metadata: Optional[Dict] = None) -> None:
        """Track user interactions for UX analysis"""
        self._user_interactions.append({
            'timestamp': datetime.now().isoformat(),
            'component_id': component_id,
            'action': action,
            'user_id': user_id,
            'metadata': metadata or {}
        })
        
        # Limit interaction history
        if len(self._user_interactions) > 10000:
            self._user_interactions = self._user_interactions[-5000:]
    
    def track_error(self, component_id: str, error: Exception, 
                   context: Optional[Dict] = None) -> None:
        """Track component errors for debugging and reliability metrics"""
        self._error_log.append({
            'timestamp': datetime.now().isoformat(),
            'component_id': component_id,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {}
        })
        
        # Limit error log
        if len(self._error_log) > 5000:
            self._error_log = self._error_log[-2500:]
    
    def get_component_analytics(self, component_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for a specific component"""
        component_metrics = self._metrics.get(component_id, [])
        
        # Calculate uptime and state distribution
        state_counts = {}
        total_time = 0
        for metric in component_metrics:
            state = metric['state']
            state_counts[state] = state_counts.get(state, 0) + 1
        
        # Performance metrics
        perf_keys = [key for key in self._performance_data.keys() 
                    if key.startswith(component_id)]
        performance_summary = {}
        for key in perf_keys:
            operation = key.replace(f"{component_id}_", "")
            durations = self._performance_data[key]
            if durations:
                performance_summary[operation] = {
                    'avg': sum(durations) / len(durations),
                    'min': min(durations),
                    'max': max(durations),
                    'count': len(durations)
                }
        
        # User interaction summary
        interactions = [i for i in self._user_interactions 
                       if i['component_id'] == component_id]
        
        # Error summary
        errors = [e for e in self._error_log if e['component_id'] == component_id]
        
        return {
            'component_id': component_id,
            'lifecycle_events': len(component_metrics),
            'state_distribution': state_counts,
            'performance': performance_summary,
            'user_interactions': len(interactions),
            'errors': len(errors),
            'last_activity': component_metrics[-1]['timestamp'] if component_metrics else None,
            'health_score': self._calculate_health_score(component_id)
        }
    
    def _calculate_health_score(self, component_id: str) -> float:
        """Calculate a health score (0-100) based on various metrics"""
        # Simple health score calculation - can be made more sophisticated
        errors = len([e for e in self._error_log if e['component_id'] == component_id])
        interactions = len([i for i in self._user_interactions 
                           if i['component_id'] == component_id])
        
        if interactions == 0:
            return 50.0  # Neutral score for unused components
        
        error_rate = min(errors / interactions, 1.0) if interactions > 0 else 0
        return max(0, 100 - (error_rate * 100))


class BaseComponent(ABC):
    """
    Abstract base class for all components in the Gary-Zero framework.
    
    Provides standardized lifecycle management, configuration handling,
    event communication, and analytics integration. All components must
    inherit from this class to ensure consistency and interoperability.
    """
    
    def __init__(self, metadata: ComponentMetadata, config: ComponentConfig, 
                 event_bus: EventBus, analytics: ComponentAnalytics):
        self.metadata = metadata
        self.config = config
        self.event_bus = event_bus
        self.analytics = analytics
        self.state = ComponentState.UNINITIALIZED
        self.start_time: Optional[float] = None
        self.children: Set[str] = set()
        self.parent: Optional[str] = None
        
        # Subscribe to framework events
        self.event_bus.subscribe('framework.shutdown', self._handle_shutdown)
        self.event_bus.subscribe('component.config_updated', self._handle_config_update)
        
        logger.info(f"Component created: {self.metadata.name} ({self.config.instance_id})")
    
    async def initialize(self) -> None:
        """Initialize the component with error handling and analytics"""
        try:
            self.state = ComponentState.INITIALIZING
            self.analytics.track_component_lifecycle(
                self.config.instance_id, 
                self.state,
                {'component_type': self.metadata.component_type.value}
            )
            
            start_time = time.time()
            await self._initialize()
            duration = time.time() - start_time
            
            self.analytics.track_performance(
                self.config.instance_id, 
                'initialize', 
                duration
            )
            
            self.state = ComponentState.READY
            self.analytics.track_component_lifecycle(self.config.instance_id, self.state)
            
            await self.event_bus.emit(
                'component.initialized', 
                {'instance_id': self.config.instance_id},
                self.config.instance_id
            )
            
        except Exception as e:
            self.state = ComponentState.ERROR
            self.analytics.track_error(self.config.instance_id, e, {'phase': 'initialization'})
            self.analytics.track_component_lifecycle(self.config.instance_id, self.state)
            logger.error(f"Component initialization failed: {e}")
            raise
    
    async def start(self) -> None:
        """Start the component with lifecycle management"""
        if self.state != ComponentState.READY:
            raise RuntimeError(f"Component not ready to start. Current state: {self.state}")
        
        try:
            start_time = time.time()
            await self._start()
            duration = time.time() - start_time
            
            self.analytics.track_performance(self.config.instance_id, 'start', duration)
            
            self.state = ComponentState.ACTIVE
            self.start_time = time.time()
            self.analytics.track_component_lifecycle(self.config.instance_id, self.state)
            
            await self.event_bus.emit(
                'component.started',
                {'instance_id': self.config.instance_id},
                self.config.instance_id
            )
            
        except Exception as e:
            self.state = ComponentState.ERROR
            self.analytics.track_error(self.config.instance_id, e, {'phase': 'start'})
            self.analytics.track_component_lifecycle(self.config.instance_id, self.state)
            raise
    
    async def stop(self) -> None:
        """Stop the component gracefully"""
        if self.state not in [ComponentState.ACTIVE, ComponentState.SUSPENDED]:
            return
        
        try:
            start_time = time.time()
            await self._stop()
            duration = time.time() - start_time
            
            self.analytics.track_performance(self.config.instance_id, 'stop', duration)
            
            self.state = ComponentState.READY
            self.analytics.track_component_lifecycle(self.config.instance_id, self.state)
            
            await self.event_bus.emit(
                'component.stopped',
                {'instance_id': self.config.instance_id},
                self.config.instance_id
            )
            
        except Exception as e:
            self.state = ComponentState.ERROR
            self.analytics.track_error(self.config.instance_id, e, {'phase': 'stop'})
            raise
    
    async def destroy(self) -> None:
        """Destroy the component and clean up resources"""
        try:
            await self.stop()
            await self._destroy()
            
            self.state = ComponentState.DESTROYED
            self.analytics.track_component_lifecycle(self.config.instance_id, self.state)
            
            # Unsubscribe from events
            self.event_bus.unsubscribe('framework.shutdown', self._handle_shutdown)
            self.event_bus.unsubscribe('component.config_updated', self._handle_config_update)
            
            await self.event_bus.emit(
                'component.destroyed',
                {'instance_id': self.config.instance_id},
                self.config.instance_id
            )
            
        except Exception as e:
            self.analytics.track_error(self.config.instance_id, e, {'phase': 'destroy'})
            raise
    
    def update_config(self, new_settings: Dict[str, Any]) -> None:
        """Update component configuration with validation"""
        try:
            # Validate new settings
            validated_settings = self._validate_settings(new_settings)
            
            # Update configuration
            old_settings = self.config.settings.copy()
            self.config.settings.update(validated_settings)
            self.config.updated_at = datetime.now()
            
            # Notify component of config change
            self._on_config_changed(old_settings, self.config.settings)
            
            self.analytics.track_component_lifecycle(
                self.config.instance_id,
                self.state,
                {'action': 'config_updated', 'changes': list(validated_settings.keys())}
            )
            
        except Exception as e:
            self.analytics.track_error(self.config.instance_id, e, {'phase': 'config_update'})
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get current component status and metrics"""
        uptime = time.time() - self.start_time if self.start_time else 0
        
        return {
            'instance_id': self.config.instance_id,
            'component_id': self.metadata.id,
            'name': self.metadata.name,
            'state': self.state.value,
            'uptime': uptime,
            'children': list(self.children),
            'parent': self.parent,
            'last_updated': self.config.updated_at.isoformat(),
            'analytics': self.analytics.get_component_analytics(self.config.instance_id),
            'custom_status': self._get_custom_status()
        }
    
    # Abstract methods that must be implemented by concrete components
    @abstractmethod
    async def _initialize(self) -> None:
        """Component-specific initialization logic"""
        pass
    
    @abstractmethod
    async def _start(self) -> None:
        """Component-specific start logic"""
        pass
    
    @abstractmethod
    async def _stop(self) -> None:
        """Component-specific stop logic"""
        pass
    
    @abstractmethod
    async def _destroy(self) -> None:
        """Component-specific cleanup logic"""
        pass
    
    @abstractmethod
    def _validate_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize component settings"""
        pass
    
    @abstractmethod
    def _on_config_changed(self, old_settings: Dict[str, Any], 
                          new_settings: Dict[str, Any]) -> None:
        """Handle configuration changes"""
        pass
    
    @abstractmethod
    def _get_custom_status(self) -> Dict[str, Any]:
        """Return component-specific status information"""
        pass
    
    # Event handlers
    async def _handle_shutdown(self, event: Dict) -> None:
        """Handle framework shutdown"""
        logger.info(f"Shutting down component: {self.config.instance_id}")
        await self.destroy()
    
    async def _handle_config_update(self, event: Dict) -> None:
        """Handle external configuration updates"""
        data = event.get('data', {})
        if data.get('instance_id') == self.config.instance_id:
            new_settings = data.get('settings', {})
            self.update_config(new_settings)


class ComponentRegistry:
    """
    Central registry for component discovery and management.
    
    Maintains a catalog of available components, handles component
    instantiation, and provides discovery mechanisms for the UI.
    """
    
    def __init__(self):
        self._components: Dict[str, type] = {}
        self._metadata: Dict[str, ComponentMetadata] = {}
        
    def register(self, component_class: type, metadata: ComponentMetadata) -> None:
        """Register a new component type"""
        self._components[metadata.id] = component_class
        self._metadata[metadata.id] = metadata
        logger.info(f"Registered component: {metadata.name} ({metadata.id})")
    
    def unregister(self, component_id: str) -> bool:
        """Unregister a component type"""
        if component_id in self._components:
            del self._components[component_id]
            del self._metadata[component_id]
            logger.info(f"Unregistered component: {component_id}")
            return True
        return False
    
    def get_component_class(self, component_id: str) -> Optional[type]:
        """Get component class by ID"""
        return self._components.get(component_id)
    
    def get_metadata(self, component_id: str) -> Optional[ComponentMetadata]:
        """Get component metadata by ID"""
        return self._metadata.get(component_id)
    
    def list_components(self, component_type: Optional[ComponentType] = None, 
                       category: Optional[str] = None,
                       tags: Optional[List[str]] = None) -> List[ComponentMetadata]:
        """List available components with filtering"""
        components = list(self._metadata.values())
        
        if component_type:
            components = [c for c in components if c.component_type == component_type]
        
        if category:
            components = [c for c in components if c.category == category]
        
        if tags:
            components = [c for c in components if any(tag in c.tags for tag in tags)]
        
        return sorted(components, key=lambda c: c.name)
    
    def search_components(self, query: str) -> List[ComponentMetadata]:
        """Search components by name, description, or tags"""
        query_lower = query.lower()
        results = []
        
        for metadata in self._metadata.values():
            if (query_lower in metadata.name.lower() or
                query_lower in metadata.description.lower() or
                any(query_lower in tag.lower() for tag in metadata.tags)):
                results.append(metadata)
        
        return sorted(results, key=lambda c: c.name)


class ComponentManager:
    """
    Central orchestrator for component lifecycle and communication.
    
    Manages component instances, handles dependency resolution,
    coordinates inter-component communication, and provides
    monitoring and debugging capabilities.
    """
    
    def __init__(self):
        self.registry = ComponentRegistry()
        self.event_bus = EventBus()
        self.analytics = ComponentAnalytics()
        self._instances: Dict[str, BaseComponent] = {}
        self._dependency_graph: Dict[str, Set[str]] = {}
        
    async def create_component(self, component_id: str, config: ComponentConfig) -> str:
        """Create and initialize a new component instance"""
        # Get component class and metadata
        component_class = self.registry.get_component_class(component_id)
        metadata = self.registry.get_metadata(component_id)
        
        if not component_class or not metadata:
            raise ValueError(f"Component not found: {component_id}")
        
        # Check dependencies
        await self._resolve_dependencies(metadata.dependencies)
        
        # Create instance
        instance = component_class(metadata, config, self.event_bus, self.analytics)
        
        # Initialize
        await instance.initialize()
        
        # Store instance
        self._instances[config.instance_id] = instance
        
        # Auto-start if configured
        if config.auto_start:
            await instance.start()
        
        logger.info(f"Created component instance: {config.instance_id}")
        return config.instance_id
    
    async def destroy_component(self, instance_id: str) -> None:
        """Destroy a component instance"""
        if instance_id in self._instances:
            instance = self._instances[instance_id]
            await instance.destroy()
            del self._instances[instance_id]
            logger.info(f"Destroyed component instance: {instance_id}")
    
    async def start_component(self, instance_id: str) -> None:
        """Start a component instance"""
        if instance_id in self._instances:
            await self._instances[instance_id].start()
    
    async def stop_component(self, instance_id: str) -> None:
        """Stop a component instance"""
        if instance_id in self._instances:
            await self._instances[instance_id].stop()
    
    def get_component(self, instance_id: str) -> Optional[BaseComponent]:
        """Get component instance by ID"""
        return self._instances.get(instance_id)
    
    def list_instances(self, component_id: Optional[str] = None,
                      state: Optional[ComponentState] = None) -> List[Dict[str, Any]]:
        """List component instances with filtering"""
        instances = []
        
        for instance in self._instances.values():
            if component_id and instance.metadata.id != component_id:
                continue
            if state and instance.state != state:
                continue
            
            instances.append(instance.get_status())
        
        return instances
    
    async def _resolve_dependencies(self, dependencies: List[str]) -> None:
        """Resolve component dependencies"""
        for dep_id in dependencies:
            if not any(instance.metadata.id == dep_id 
                      for instance in self._instances.values()
                      if instance.state == ComponentState.ACTIVE):
                raise RuntimeError(f"Dependency not satisfied: {dep_id}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status and metrics"""
        instances_by_state = {}
        for instance in self._instances.values():
            state = instance.state.value
            instances_by_state[state] = instances_by_state.get(state, 0) + 1
        
        return {
            'total_instances': len(self._instances),
            'instances_by_state': instances_by_state,
            'event_stats': self.event_bus.get_event_stats(),
            'registered_components': len(self.registry._components),
            'uptime': time.time()  # Will be relative to manager creation
        }


# Example concrete component implementation
class DashboardWidget(BaseComponent):
    """
    Example implementation of a dashboard widget component.
    
    Demonstrates how to create a concrete component with specific
    functionality while leveraging the base component infrastructure.
    """
    
    async def _initialize(self) -> None:
        """Initialize dashboard widget"""
        # Initialize widget-specific resources
        self.data_cache = {}
        self.refresh_interval = self.config.settings.get('refresh_interval', 30)
        self.widget_type = self.config.settings.get('widget_type', 'chart')
        
        # Subscribe to data update events
        self.event_bus.subscribe('data.updated', self._handle_data_update)
        
        logger.info(f"Dashboard widget initialized: {self.widget_type}")
    
    async def _start(self) -> None:
        """Start the widget"""
        # Start periodic data refresh
        asyncio.create_task(self._refresh_loop())
        logger.info(f"Dashboard widget started: {self.config.instance_id}")
    
    async def _stop(self) -> None:
        """Stop the widget"""
        # Stop refresh loop (would need proper task management in real implementation)
        logger.info(f"Dashboard widget stopped: {self.config.instance_id}")
    
    async def _destroy(self) -> None:
        """Clean up widget resources"""
        # Unsubscribe from events
        self.event_bus.unsubscribe('data.updated', self._handle_data_update)
        
        # Clear cache
        self.data_cache.clear()
        
        logger.info(f"Dashboard widget destroyed: {self.config.instance_id}")
    
    def _validate_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate widget settings"""
        validated = {}
        
        if 'refresh_interval' in settings:
            interval = settings['refresh_interval']
            if isinstance(interval, (int, float)) and interval > 0:
                validated['refresh_interval'] = max(1, int(interval))
        
        if 'widget_type' in settings:
            widget_type = settings['widget_type']
            if widget_type in ['chart', 'table', 'metric', 'text']:
                validated['widget_type'] = widget_type
        
        if 'data_source' in settings:
            validated['data_source'] = str(settings['data_source'])
        
        return validated
    
    def _on_config_changed(self, old_settings: Dict[str, Any], 
                          new_settings: Dict[str, Any]) -> None:
        """Handle configuration changes"""
        if old_settings.get('refresh_interval') != new_settings.get('refresh_interval'):
            self.refresh_interval = new_settings.get('refresh_interval', 30)
            logger.info(f"Widget refresh interval updated: {self.refresh_interval}")
        
        if old_settings.get('widget_type') != new_settings.get('widget_type'):
            self.widget_type = new_settings.get('widget_type', 'chart')
            # Would trigger widget re-rendering in real implementation
            logger.info(f"Widget type changed: {self.widget_type}")
    
    def _get_custom_status(self) -> Dict[str, Any]:
        """Get widget-specific status"""
        return {
            'widget_type': self.widget_type,
            'refresh_interval': self.refresh_interval,
            'cache_size': len(self.data_cache),
            'last_refresh': getattr(self, 'last_refresh', None)
        }
    
    async def _refresh_loop(self) -> None:
        """Periodic data refresh loop"""
        while self.state == ComponentState.ACTIVE:
            try:
                await self._refresh_data()
                await asyncio.sleep(self.refresh_interval)
            except Exception as e:
                self.analytics.track_error(self.config.instance_id, e, {'operation': 'refresh'})
                await asyncio.sleep(self.refresh_interval)
    
    async def _refresh_data(self) -> None:
        """Refresh widget data"""
        start_time = time.time()
        
        # Simulate data fetching
        await asyncio.sleep(0.1)
        
        # Update cache
        self.data_cache['last_update'] = datetime.now()
        self.last_refresh = datetime.now().isoformat()
        
        # Track performance
        duration = time.time() - start_time
        self.analytics.track_performance(
            self.config.instance_id, 
            'data_refresh', 
            duration
        )
        
        # Emit data update event
        await self.event_bus.emit(
            'widget.data_updated',
            {
                'instance_id': self.config.instance_id,
                'widget_type': self.widget_type,
                'update_time': self.last_refresh
            },
            self.config.instance_id
        )
    
    async def _handle_data_update(self, event: Dict) -> None:
        """Handle external data updates"""
        data = event.get('data', {})
        if data.get('source') == self.config.settings.get('data_source'):
            # Update widget with new data
            await self._refresh_data()
            
            self.analytics.track_user_interaction(
                self.config.instance_id,
                'external_data_update',
                event.get('source', 'system')
            )


# Factory function for easy component creation
def create_component_manager() -> ComponentManager:
    """Factory function to create a fully configured component manager"""
    manager = ComponentManager()
    
    # Register example components
    dashboard_metadata = ComponentMetadata(
        id="dashboard_widget",
        name="Dashboard Widget",
        version="1.0.0",
        description="Configurable dashboard widget for data visualization",
        author="Gary-Zero Framework",
        component_type=ComponentType.WIDGET,
        category="visualization",
        tags=["dashboard", "widget", "chart", "data"],
        permissions=["read_data", "refresh_data"]
    )
    
    manager.registry.register(DashboardWidget, dashboard_metadata)
    
    logger.info("Component manager created with example components")
    return manager


# Example usage and demo
async def demo_component_system():
    """
    Demonstration of the component system capabilities.
    
    Shows how to create, configure, and manage components
    in a realistic usage scenario.
    """
    print("🚀 Gary-Zero Modular Component System Demo")
    print("=" * 50)
    
    # Create component manager
    manager = create_component_manager()
    
    # List available components
    print("\n📦 Available Components:")
    components = manager.registry.list_components()
    for comp in components:
        print(f"  • {comp.name} ({comp.id}) - {comp.description}")
    
    # Create component configurations
    widget_config = ComponentConfig(
        instance_id="widget_001",
        component_id="dashboard_widget",
        user_id="demo_user",
        workspace_id="demo_workspace",
        settings={
            'widget_type': 'chart',
            'refresh_interval': 5,
            'data_source': 'analytics_db'
        }
    )
    
    # Create and start component
    print(f"\n🔧 Creating component: {widget_config.instance_id}")
    instance_id = await manager.create_component("dashboard_widget", widget_config)
    
    # Show component status
    component = manager.get_component(instance_id)
    print(f"✅ Component created: {component.metadata.name}")
    print(f"   State: {component.state.value}")
    print(f"   Type: {component.metadata.component_type.value}")
    
    # Simulate some activity
    print("\n⚡ Simulating component activity...")
    await asyncio.sleep(2)
    
    # Update component configuration
    print("🔄 Updating component configuration...")
    component.update_config({'refresh_interval': 10, 'widget_type': 'table'})
    
    # Get analytics
    await asyncio.sleep(3)
    analytics = manager.analytics.get_component_analytics(instance_id)
    print(f"\n📊 Component Analytics:")
    print(f"   Health Score: {analytics['health_score']:.1f}/100")
    print(f"   Lifecycle Events: {analytics['lifecycle_events']}")
    print(f"   Performance Operations: {len(analytics['performance'])}")
    
    # System status
    system_status = manager.get_system_status()
    print(f"\n🖥️  System Status:")
    print(f"   Total Instances: {system_status['total_instances']}")
    print(f"   Registered Components: {system_status['registered_components']}")
    print(f"   Event Stats: {system_status['event_stats']['total_events']} total events")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    await manager.destroy_component(instance_id)
    print("✅ Demo completed successfully!")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run demo
    asyncio.run(demo_component_system())