"""
Resource optimization utilities.

Provides intelligent resource optimization including:
- Memory usage optimization
- CPU usage optimization  
- I/O optimization
- Automatic resource management
"""

import gc
import os
import psutil
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable, Union
import logging
import weakref
from functools import wraps

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Result of an optimization operation."""
    optimization_type: str
    before_value: float
    after_value: float
    improvement: float
    improvement_percent: float
    duration_seconds: float
    recommendations: List[str]


class BaseOptimizer(ABC):
    """Base class for resource optimizers."""
    
    def __init__(self, name: str):
        self.name = name
        self._enabled = True
        self._last_optimization = 0
        self._optimization_count = 0
        self._total_improvement = 0.0
    
    @abstractmethod
    def optimize(self) -> OptimizationResult:
        """Perform optimization and return results."""
        pass
    
    @abstractmethod
    def get_current_usage(self) -> float:
        """Get current resource usage value."""
        pass
    
    def is_optimization_needed(self, threshold: float = 0.8) -> bool:
        """Check if optimization is needed based on threshold."""
        return self.get_current_usage() > threshold
    
    def enable(self) -> None:
        """Enable this optimizer."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable this optimizer."""
        self._enabled = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get optimizer statistics."""
        return {
            'name': self.name,
            'enabled': self._enabled,
            'optimization_count': self._optimization_count,
            'total_improvement': self._total_improvement,
            'last_optimization': self._last_optimization,
            'current_usage': self.get_current_usage()
        }


class MemoryOptimizer(BaseOptimizer):
    """Memory usage optimizer with garbage collection and cache management."""
    
    def __init__(self):
        super().__init__("MemoryOptimizer")
        self._weak_cache_refs: List[weakref.ref] = []
        self._cache_cleanup_funcs: List[Callable] = []
    
    def register_cache_cleanup(self, cleanup_func: Callable) -> None:
        """Register a cache cleanup function."""
        self._cache_cleanup_funcs.append(cleanup_func)
    
    def register_weak_cache(self, cache_obj: Any) -> None:
        """Register a cache object for weak reference tracking."""
        self._weak_cache_refs.append(weakref.ref(cache_obj))
    
    def get_current_usage(self) -> float:
        """Get current memory usage as a percentage."""
        try:
            memory = psutil.virtual_memory()
            return memory.percent / 100.0
        except Exception as e:
            logger.warning(f"Failed to get memory usage: {e}")
            return 0.0
    
    def get_memory_info(self) -> Dict[str, float]:
        """Get detailed memory information."""
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            system_memory = psutil.virtual_memory()
            
            return {
                'process_rss_mb': memory_info.rss / 1024 / 1024,
                'process_vms_mb': memory_info.vms / 1024 / 1024,
                'system_used_mb': system_memory.used / 1024 / 1024,
                'system_available_mb': system_memory.available / 1024 / 1024,
                'system_percent': system_memory.percent,
                'process_percent': process.memory_percent()
            }
        except Exception as e:
            logger.warning(f"Failed to get detailed memory info: {e}")
            return {}
    
    def cleanup_weak_references(self) -> int:
        """Clean up dead weak references and return count cleaned."""
        initial_count = len(self._weak_cache_refs)
        self._weak_cache_refs = [ref for ref in self._weak_cache_refs if ref() is not None]
        return initial_count - len(self._weak_cache_refs)
    
    def cleanup_caches(self) -> int:
        """Run registered cache cleanup functions."""
        cleaned_count = 0
        for cleanup_func in self._cache_cleanup_funcs:
            try:
                result = cleanup_func()
                if isinstance(result, int):
                    cleaned_count += result
                else:
                    cleaned_count += 1
            except Exception as e:
                logger.warning(f"Cache cleanup function failed: {e}")
        return cleaned_count
    
    def force_garbage_collection(self) -> Dict[str, int]:
        """Force garbage collection and return collection stats."""
        before_objects = len(gc.get_objects())
        
        # Run garbage collection for all generations
        collected = {
            'gen0': gc.collect(0),
            'gen1': gc.collect(1),
            'gen2': gc.collect(2)
        }
        
        after_objects = len(gc.get_objects())
        collected['objects_freed'] = before_objects - after_objects
        
        return collected
    
    def optimize(self) -> OptimizationResult:
        """Perform memory optimization."""
        start_time = time.time()
        before_usage = self.get_current_usage()
        before_info = self.get_memory_info()
        
        recommendations = []
        
        # Clean up weak references
        weak_refs_cleaned = self.cleanup_weak_references()
        if weak_refs_cleaned > 0:
            recommendations.append(f"Cleaned {weak_refs_cleaned} dead weak references")
        
        # Clean up registered caches
        caches_cleaned = self.cleanup_caches()
        if caches_cleaned > 0:
            recommendations.append(f"Cleaned {caches_cleaned} cache entries")
        
        # Force garbage collection
        gc_stats = self.force_garbage_collection()
        total_collected = sum(gc_stats[key] for key in ['gen0', 'gen1', 'gen2'])
        if total_collected > 0:
            recommendations.append(
                f"Garbage collected {total_collected} objects "
                f"({gc_stats['objects_freed']} total objects freed)"
            )
        
        # Get after measurements
        after_usage = self.get_current_usage()
        after_info = self.get_memory_info()
        
        improvement = before_usage - after_usage
        improvement_percent = (improvement / max(before_usage, 0.01)) * 100
        
        # Add memory-specific recommendations
        if after_info.get('system_percent', 0) > 80:
            recommendations.append("System memory usage is high - consider reducing cache sizes")
        
        if after_info.get('process_percent', 0) > 50:
            recommendations.append("Process memory usage is high - consider memory profiling")
        
        duration = time.time() - start_time
        
        # Update stats
        self._optimization_count += 1
        self._total_improvement += improvement
        self._last_optimization = time.time()
        
        result = OptimizationResult(
            optimization_type="memory",
            before_value=before_usage,
            after_value=after_usage,
            improvement=improvement,
            improvement_percent=improvement_percent,
            duration_seconds=duration,
            recommendations=recommendations
        )
        
        logger.info(
            f"Memory optimization completed: "
            f"{improvement_percent:.2f}% improvement, "
            f"freed {before_info.get('process_rss_mb', 0) - after_info.get('process_rss_mb', 0):.1f}MB"
        )
        
        return result


class CPUOptimizer(BaseOptimizer):
    """CPU usage optimizer with process prioritization and thread management."""
    
    def __init__(self):
        super().__init__("CPUOptimizer")
        self._process = psutil.Process(os.getpid())
        self._thread_pools: List[Any] = []
    
    def register_thread_pool(self, pool: Any) -> None:
        """Register a thread pool for optimization."""
        self._thread_pools.append(pool)
    
    def get_current_usage(self) -> float:
        """Get current CPU usage as a percentage."""
        try:
            return psutil.cpu_percent(interval=0.1) / 100.0
        except Exception as e:
            logger.warning(f"Failed to get CPU usage: {e}")
            return 0.0
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """Get detailed CPU information."""
        try:
            return {
                'system_cpu_percent': psutil.cpu_percent(interval=0.1),
                'process_cpu_percent': self._process.cpu_percent(),
                'cpu_count_logical': psutil.cpu_count(logical=True),
                'cpu_count_physical': psutil.cpu_count(logical=False),
                'process_num_threads': self._process.num_threads(),
                'process_nice': self._process.nice(),
                'load_average': getattr(psutil, 'getloadavg', lambda: [0, 0, 0])()
            }
        except Exception as e:
            logger.warning(f"Failed to get CPU info: {e}")
            return {}
    
    def optimize_process_priority(self) -> str:
        """Optimize process priority based on current load."""
        try:
            cpu_info = self.get_cpu_info()
            current_nice = cpu_info.get('process_nice', 0)
            system_cpu = cpu_info.get('system_cpu_percent', 0)
            
            # Adjust priority based on system load
            if system_cpu > 80:
                # System is under high load, lower our priority
                target_nice = min(current_nice + 1, 19)
            elif system_cpu < 20:
                # System has plenty of resources, raise our priority
                target_nice = max(current_nice - 1, -20)
            else:
                # System load is moderate, keep current priority
                target_nice = current_nice
            
            if target_nice != current_nice:
                self._process.nice(target_nice)
                return f"Adjusted process priority from {current_nice} to {target_nice}"
            else:
                return "Process priority unchanged"
            
        except Exception as e:
            logger.warning(f"Failed to optimize process priority: {e}")
            return f"Priority optimization failed: {e}"
    
    def optimize_thread_pools(self) -> List[str]:
        """Optimize registered thread pools."""
        results = []
        cpu_count = psutil.cpu_count(logical=True) or 4
        
        for i, pool in enumerate(self._thread_pools):
            try:
                # Try to adjust thread pool size based on CPU count
                if hasattr(pool, '_max_workers'):
                    current_workers = pool._max_workers
                    optimal_workers = min(cpu_count * 2, current_workers)
                    
                    if hasattr(pool, '_adjust_worker_count'):
                        pool._adjust_worker_count(optimal_workers)
                        results.append(
                            f"Thread pool {i}: adjusted from {current_workers} to {optimal_workers} workers"
                        )
                    else:
                        results.append(f"Thread pool {i}: no adjustment method available")
                else:
                    results.append(f"Thread pool {i}: unable to determine worker count")
                    
            except Exception as e:
                results.append(f"Thread pool {i} optimization failed: {e}")
        
        return results
    
    def optimize(self) -> OptimizationResult:
        """Perform CPU optimization."""
        start_time = time.time()
        before_usage = self.get_current_usage()
        before_info = self.get_cpu_info()
        
        recommendations = []
        
        # Optimize process priority
        priority_result = self.optimize_process_priority()
        recommendations.append(priority_result)
        
        # Optimize thread pools
        thread_results = self.optimize_thread_pools()
        recommendations.extend(thread_results)
        
        # Wait a moment for changes to take effect
        time.sleep(0.5)
        
        # Get after measurements
        after_usage = self.get_current_usage()
        after_info = self.get_cpu_info()
        
        improvement = before_usage - after_usage
        improvement_percent = (improvement / max(before_usage, 0.01)) * 100
        
        # Add CPU-specific recommendations
        cpu_count = after_info.get('cpu_count_logical', 4)
        if after_info.get('system_cpu_percent', 0) > 80:
            recommendations.append(f"High CPU usage detected - consider using async patterns")
        
        if after_info.get('process_num_threads', 0) > cpu_count * 2:
            recommendations.append(f"High thread count ({after_info['process_num_threads']}) - consider thread pooling")
        
        duration = time.time() - start_time
        
        # Update stats
        self._optimization_count += 1
        self._total_improvement += improvement
        self._last_optimization = time.time()
        
        result = OptimizationResult(
            optimization_type="cpu",
            before_value=before_usage,
            after_value=after_usage,
            improvement=improvement,
            improvement_percent=improvement_percent,
            duration_seconds=duration,
            recommendations=recommendations
        )
        
        logger.info(
            f"CPU optimization completed: "
            f"{improvement_percent:.2f}% improvement"
        )
        
        return result


class ResourceOptimizer:
    """Comprehensive resource optimizer coordinating all optimization strategies."""
    
    def __init__(self, 
                 memory_optimizer: Optional[MemoryOptimizer] = None,
                 cpu_optimizer: Optional[CPUOptimizer] = None,
                 auto_optimize_interval: Optional[float] = None):
        self.memory_optimizer = memory_optimizer or MemoryOptimizer()
        self.cpu_optimizer = cpu_optimizer or CPUOptimizer()
        self.auto_optimize_interval = auto_optimize_interval
        
        self._optimizers = [self.memory_optimizer, self.cpu_optimizer]
        self._auto_optimize_task: Optional[threading.Timer] = None
        self._optimization_history: List[OptimizationResult] = []
        self._lock = threading.RLock()
    
    def register_cache_cleanup(self, cleanup_func: Callable) -> None:
        """Register a cache cleanup function with the memory optimizer."""
        self.memory_optimizer.register_cache_cleanup(cleanup_func)
    
    def register_thread_pool(self, pool: Any) -> None:
        """Register a thread pool with the CPU optimizer."""
        self.cpu_optimizer.register_thread_pool(pool)
    
    def optimize_memory(self) -> OptimizationResult:
        """Optimize memory usage."""
        result = self.memory_optimizer.optimize()
        with self._lock:
            self._optimization_history.append(result)
        return result
    
    def optimize_cpu(self) -> OptimizationResult:
        """Optimize CPU usage."""
        result = self.cpu_optimizer.optimize()
        with self._lock:
            self._optimization_history.append(result)
        return result
    
    def optimize_all(self, 
                    memory_threshold: float = 0.8,
                    cpu_threshold: float = 0.8) -> List[OptimizationResult]:
        """Optimize all resources that exceed thresholds."""
        results = []
        
        # Check and optimize memory if needed
        if self.memory_optimizer.is_optimization_needed(memory_threshold):
            try:
                result = self.optimize_memory()
                results.append(result)
            except Exception as e:
                logger.error(f"Memory optimization failed: {e}")
        
        # Check and optimize CPU if needed
        if self.cpu_optimizer.is_optimization_needed(cpu_threshold):
            try:
                result = self.optimize_cpu()
                results.append(result)
            except Exception as e:
                logger.error(f"CPU optimization failed: {e}")
        
        return results
    
    def start_auto_optimization(self, 
                               interval: Optional[float] = None,
                               memory_threshold: float = 0.8,
                               cpu_threshold: float = 0.8) -> None:
        """Start automatic optimization at regular intervals."""
        if self._auto_optimize_task:
            self.stop_auto_optimization()
        
        interval = interval or self.auto_optimize_interval or 300.0  # 5 minutes default
        
        def auto_optimize():
            try:
                results = self.optimize_all(memory_threshold, cpu_threshold)
                if results:
                    logger.info(f"Auto-optimization completed: {len(results)} optimizations performed")
            except Exception as e:
                logger.error(f"Auto-optimization failed: {e}")
            finally:
                # Schedule next optimization
                if self.auto_optimize_interval:
                    self._auto_optimize_task = threading.Timer(interval, auto_optimize)
                    self._auto_optimize_task.start()
        
        self._auto_optimize_task = threading.Timer(interval, auto_optimize)
        self._auto_optimize_task.start()
        logger.info(f"Started auto-optimization with {interval}s interval")
    
    def stop_auto_optimization(self) -> None:
        """Stop automatic optimization."""
        if self._auto_optimize_task:
            self._auto_optimize_task.cancel()
            self._auto_optimize_task = None
            logger.info("Stopped auto-optimization")
    
    def get_optimization_history(self, limit: Optional[int] = None) -> List[OptimizationResult]:
        """Get optimization history."""
        with self._lock:
            history = self._optimization_history.copy()
            if limit:
                return history[-limit:]
            return history
    
    def get_resource_status(self) -> Dict[str, Any]:
        """Get comprehensive resource status."""
        memory_info = self.memory_optimizer.get_memory_info()
        cpu_info = self.cpu_optimizer.get_cpu_info()
        
        return {
            'timestamp': time.time(),
            'memory': {
                'usage_percent': self.memory_optimizer.get_current_usage() * 100,
                'details': memory_info,
                'optimizer_stats': self.memory_optimizer.get_stats()
            },
            'cpu': {
                'usage_percent': self.cpu_optimizer.get_current_usage() * 100,
                'details': cpu_info,
                'optimizer_stats': self.cpu_optimizer.get_stats()
            },
            'optimization_history_count': len(self._optimization_history),
            'auto_optimization_active': self._auto_optimize_task is not None
        }
    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """Generate a comprehensive optimization report."""
        history = self.get_optimization_history()
        status = self.get_resource_status()
        
        # Calculate aggregate statistics
        if history:
            memory_optimizations = [r for r in history if r.optimization_type == "memory"]
            cpu_optimizations = [r for r in history if r.optimization_type == "cpu"]
            
            total_memory_improvement = sum(r.improvement for r in memory_optimizations)
            total_cpu_improvement = sum(r.improvement for r in cpu_optimizations)
            
            avg_memory_improvement = (
                sum(r.improvement_percent for r in memory_optimizations) / len(memory_optimizations)
                if memory_optimizations else 0
            )
            avg_cpu_improvement = (
                sum(r.improvement_percent for r in cpu_optimizations) / len(cpu_optimizations)
                if cpu_optimizations else 0
            )
        else:
            total_memory_improvement = 0
            total_cpu_improvement = 0
            avg_memory_improvement = 0
            avg_cpu_improvement = 0
        
        return {
            'report_timestamp': time.time(),
            'current_status': status,
            'optimization_summary': {
                'total_optimizations': len(history),
                'memory_optimizations': len([r for r in history if r.optimization_type == "memory"]),
                'cpu_optimizations': len([r for r in history if r.optimization_type == "cpu"]),
                'total_memory_improvement': total_memory_improvement,
                'total_cpu_improvement': total_cpu_improvement,
                'avg_memory_improvement_percent': avg_memory_improvement,
                'avg_cpu_improvement_percent': avg_cpu_improvement,
            },
            'recent_optimizations': history[-10:] if history else [],
            'recommendations': self._generate_recommendations(status, history)
        }
    
    def _generate_recommendations(self, 
                                 status: Dict[str, Any],
                                 history: List[OptimizationResult]) -> List[str]:
        """Generate optimization recommendations based on current status and history."""
        recommendations = []
        
        # Memory recommendations
        memory_usage = status['memory']['usage_percent']
        if memory_usage > 80:
            recommendations.append("High memory usage - consider enabling auto-optimization")
        elif memory_usage > 60:
            recommendations.append("Moderate memory usage - monitor for trends")
        
        # CPU recommendations
        cpu_usage = status['cpu']['usage_percent']
        if cpu_usage > 80:
            recommendations.append("High CPU usage - consider process optimization")
        
        # Historical analysis
        if history:
            recent_history = history[-5:]
            avg_improvement = sum(r.improvement_percent for r in recent_history) / len(recent_history)
            
            if avg_improvement < 5:
                recommendations.append("Low optimization impact - review optimization strategies")
            elif avg_improvement > 20:
                recommendations.append("High optimization impact - consider more frequent optimization")
        
        # Auto-optimization recommendations
        if not status['auto_optimization_active']:
            recommendations.append("Auto-optimization not active - consider enabling for maintenance")
        
        return recommendations


# Global resource optimizer instance
_default_optimizer = None

def get_resource_optimizer() -> ResourceOptimizer:
    """Get the default resource optimizer instance."""
    global _default_optimizer
    if _default_optimizer is None:
        _default_optimizer = ResourceOptimizer()
    return _default_optimizer


def optimize_memory() -> OptimizationResult:
    """Optimize memory using the default optimizer."""
    return get_resource_optimizer().optimize_memory()


def optimize_cpu() -> OptimizationResult:
    """Optimize CPU using the default optimizer."""
    return get_resource_optimizer().optimize_cpu()


def auto_optimize(memory_threshold: float = 0.8, cpu_threshold: float = 0.8):
    """Decorator to automatically optimize resources when thresholds are exceeded."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if optimization is needed before function execution
            optimizer = get_resource_optimizer()
            optimizer.optimize_all(memory_threshold, cpu_threshold)
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Check if optimization is needed after function execution
                optimizer.optimize_all(memory_threshold, cpu_threshold)
        
        return wrapper
    return decorator