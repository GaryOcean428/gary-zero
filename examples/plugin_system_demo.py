"""
Gary-Zero Framework Plugin System

This module demonstrates how to create and use plugins with the framework's
dependency injection container, security, and performance features.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass
from datetime import datetime

from framework.container import get_container
from framework.interfaces import BaseService
from framework.security import InputValidator, AuditLogger
from framework.performance import cached, timer, PerformanceMonitor


@dataclass
class PluginMetadata:
    """Plugin metadata for registration and discovery."""
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class Plugin(ABC):
    """Base plugin interface."""
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Plugin metadata."""
        pass
    
    @abstractmethod
    async def initialize(self, container) -> None:
        """Initialize plugin with container access."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown plugin and cleanup resources."""
        pass


class PluginManager(BaseService):
    """Manages plugin lifecycle and registration."""
    
    def __init__(self):
        super().__init__()
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_metadata: Dict[str, PluginMetadata] = {}
        self.audit_logger = AuditLogger()
        self.validator = InputValidator()
        self.monitor = PerformanceMonitor()
        
    async def initialize(self):
        """Initialize plugin manager."""
        await super().initialize()
        self.audit_logger.log_user_input("plugin_manager", "initialize")
        
    async def shutdown(self):
        """Shutdown all plugins."""
        for plugin_name in list(self.plugins.keys()):
            await self.unload_plugin(plugin_name)
        await super().shutdown()
        
    @timer()
    async def load_plugin(self, plugin_class: Type[Plugin]) -> bool:
        """Load and initialize a plugin."""
        try:
            # Create plugin instance
            plugin = plugin_class()
            metadata = plugin.metadata
            
            # Validate plugin name
            if not self.validator.validate_user_input(metadata.name):
                self.audit_logger.log_security_violation(
                    "invalid_plugin_name", {"name": metadata.name}
                )
                return False
            
            # Check if plugin already loaded
            if metadata.name in self.plugins:
                return False
                
            # Check dependencies
            missing_deps = []
            for dep in metadata.dependencies:
                if dep not in self.plugins:
                    missing_deps.append(dep)
                    
            if missing_deps:
                self.audit_logger.log_security_violation(
                    "missing_plugin_dependencies", 
                    {"plugin": metadata.name, "missing": missing_deps}
                )
                return False
            
            # Initialize plugin
            container = get_container()
            await plugin.initialize(container)
            
            # Register plugin
            self.plugins[metadata.name] = plugin
            self.plugin_metadata[metadata.name] = metadata
            
            self.audit_logger.log_tool_execution(
                "load_plugin", {"name": metadata.name, "version": metadata.version}
            )
            
            return True
            
        except Exception as e:
            self.audit_logger.log_security_violation(
                "plugin_load_error", {"error": str(e)}
            )
            return False
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin."""
        if plugin_name not in self.plugins:
            return False
            
        try:
            plugin = self.plugins[plugin_name]
            await plugin.shutdown()
            
            del self.plugins[plugin_name]
            del self.plugin_metadata[plugin_name]
            
            self.audit_logger.log_tool_execution(
                "unload_plugin", {"name": plugin_name}
            )
            
            return True
            
        except Exception as e:
            self.audit_logger.log_security_violation(
                "plugin_unload_error", {"plugin": plugin_name, "error": str(e)}
            )
            return False
    
    @cached(ttl=60)
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all loaded plugins."""
        return [
            {
                "name": metadata.name,
                "version": metadata.version,
                "description": metadata.description,
                "author": metadata.author,
                "dependencies": metadata.dependencies,
                "loaded": True
            }
            for metadata in self.plugin_metadata.values()
        ]
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Get a loaded plugin by name."""
        return self.plugins.get(plugin_name)


# Example Plugin Implementations

class LoggingPlugin(Plugin):
    """Example logging plugin."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="logging_plugin",
            version="1.0.0",
            description="Enhanced logging capabilities",
            author="Framework Team"
        )
    
    async def initialize(self, container) -> None:
        """Initialize logging plugin."""
        self.container = container
        self.audit_logger = AuditLogger()
        
        # Register logging service
        container.register_singleton("enhanced_logger", self)
        
        self.audit_logger.log_tool_execution(
            "plugin_initialize", {"plugin": "logging_plugin"}
        )
    
    async def shutdown(self) -> None:
        """Shutdown logging plugin."""
        self.audit_logger.log_tool_execution(
            "plugin_shutdown", {"plugin": "logging_plugin"}
        )
    
    @timer()
    def log_with_context(self, level: str, message: str, context: Dict[str, Any] = None):
        """Enhanced logging with context."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "context": context or {},
            "plugin": "logging_plugin"
        }
        
        self.audit_logger.log_tool_execution("enhanced_log", log_entry)
        return log_entry


class CachePlugin(Plugin):
    """Example caching plugin with advanced features."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="cache_plugin",
            version="1.0.0",
            description="Advanced caching with analytics",
            author="Framework Team"
        )
    
    async def initialize(self, container) -> None:
        """Initialize cache plugin."""
        self.container = container
        self.cache_hits = 0
        self.cache_misses = 0
        self.monitor = PerformanceMonitor()
        
        # Register cache service
        container.register_singleton("advanced_cache", self)
    
    async def shutdown(self) -> None:
        """Shutdown cache plugin."""
        pass
    
    @timer()
    def get_with_analytics(self, key: str) -> Dict[str, Any]:
        """Get cached value with analytics."""
        with self.monitor.timing_context("cache_get"):
            # Simulate cache lookup
            import random
            hit = random.random() > 0.3  # 70% hit rate
            
            if hit:
                self.cache_hits += 1
                return {
                    "value": f"cached_value_{key}",
                    "hit": True,
                    "analytics": self.get_cache_analytics()
                }
            else:
                self.cache_misses += 1
                return {
                    "value": None,
                    "hit": False,
                    "analytics": self.get_cache_analytics()
                }
    
    def get_cache_analytics(self) -> Dict[str, Any]:
        """Get cache performance analytics."""
        total = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total if total > 0 else 0
        
        return {
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "hit_rate": hit_rate,
            "total_requests": total
        }


class MonitoringPlugin(Plugin):
    """Example monitoring plugin."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="monitoring_plugin",
            version="1.0.0",
            description="System monitoring and alerting",
            author="Framework Team",
            dependencies=["logging_plugin"]  # Depends on logging plugin
        )
    
    async def initialize(self, container) -> None:
        """Initialize monitoring plugin."""
        self.container = container
        self.monitor = PerformanceMonitor()
        self.metrics = {}
        
        # Get dependency
        self.logger = container.get("enhanced_logger")
        
        # Register monitoring service
        container.register_singleton("system_monitor", self)
        
        # Start background monitoring
        self._monitoring_task = asyncio.create_task(self._monitor_system())
    
    async def shutdown(self) -> None:
        """Shutdown monitoring plugin."""
        if hasattr(self, '_monitoring_task'):
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_system(self):
        """Background system monitoring."""
        while True:
            try:
                # Collect metrics
                metrics = self.monitor.get_metrics_summary()
                self.metrics.update(metrics)
                
                # Log metrics using dependency
                if self.logger:
                    self.logger.log_with_context(
                        "INFO", "System metrics collected", {"metrics": metrics}
                    )
                
                # Check for alerts
                await self._check_alerts(metrics)
                
                await asyncio.sleep(10)  # Monitor every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.logger:
                    self.logger.log_with_context(
                        "ERROR", "Monitoring error", {"error": str(e)}
                    )
                await asyncio.sleep(5)
    
    async def _check_alerts(self, metrics: Dict[str, Any]):
        """Check for alert conditions."""
        # Example alert logic
        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)) and value > 100:  # Example threshold
                if self.logger:
                    self.logger.log_with_context(
                        "WARN", f"High {metric_name}", {"value": value, "threshold": 100}
                    )
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        return self.metrics.copy()


# Plugin System Demo

async def demonstrate_plugin_system():
    """Demonstrate the plugin system in action."""
    print("🔌 Starting Plugin System Demo\n")
    
    # Initialize container and plugin manager
    container = get_container()
    plugin_manager = PluginManager()
    
    container.register_singleton("plugin_manager", plugin_manager)
    await container.initialize_services()
    
    print("📦 Plugin Manager initialized")
    
    # Load plugins in dependency order
    plugins_to_load = [
        LoggingPlugin,    # No dependencies
        CachePlugin,      # No dependencies
        MonitoringPlugin  # Depends on logging_plugin
    ]
    
    print("\n🔄 Loading plugins...")
    for plugin_class in plugins_to_load:
        plugin_instance = plugin_class()
        success = await plugin_manager.load_plugin(plugin_class)
        print(f"  {'✅' if success else '❌'} {plugin_instance.metadata.name} v{plugin_instance.metadata.version}")
    
    # List loaded plugins
    print("\n📋 Loaded plugins:")
    plugins = plugin_manager.list_plugins()
    for plugin in plugins:
        print(f"  • {plugin['name']} v{plugin['version']} - {plugin['description']}")
        if plugin['dependencies']:
            print(f"    Dependencies: {', '.join(plugin['dependencies'])}")
    
    print("\n🧪 Testing plugin functionality...")
    
    # Test logging plugin
    logger = container.get("enhanced_logger")
    if logger:
        log_entry = logger.log_with_context("INFO", "Testing enhanced logging", {"test": True})
        print(f"  ✅ Enhanced logging: {log_entry['message']}")
    
    # Test cache plugin
    cache = container.get("advanced_cache")
    if cache:
        result1 = cache.get_with_analytics("test_key")
        result2 = cache.get_with_analytics("test_key")
        analytics = cache.get_cache_analytics()
        print(f"  ✅ Advanced cache: {analytics['total_requests']} requests, {analytics['hit_rate']:.2f} hit rate")
    
    # Test monitoring plugin
    monitor = container.get("system_monitor")
    if monitor:
        await asyncio.sleep(1)  # Let it collect some metrics
        metrics = monitor.get_current_metrics()
        print(f"  ✅ System monitoring: {len(metrics)} metrics collected")
    
    print("\n⏱️  Running plugins for 5 seconds...")
    await asyncio.sleep(5)
    
    # Show plugin metrics
    print("\n📊 Plugin Performance Metrics:")
    performance_monitor = PerformanceMonitor()
    metrics = performance_monitor.get_metrics_summary()
    for key, value in metrics.items():
        if isinstance(value, (int, float)):
            print(f"  • {key}: {value:.4f}")
    
    # Unload plugins
    print("\n🔄 Unloading plugins...")
    for plugin in plugins:
        success = await plugin_manager.unload_plugin(plugin['name'])
        print(f"  {'✅' if success else '❌'} {plugin['name']} unloaded")
    
    # Shutdown
    await container.shutdown_services()
    print("\n✅ Plugin system demo completed!")


if __name__ == "__main__":
    # Run the plugin system demo
    try:
        asyncio.run(demonstrate_plugin_system())
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()