"""
Advanced Performance Profiling and Analysis System

Provides comprehensive performance profiling with:
- CPU and memory profiling
- Custom performance metrics collection  
- Bottleneck identification and analysis
- Performance trend tracking
- Integration with observability systems
"""

import time
import threading
import cProfile
import pstats
import tracemalloc
import gc
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Union
from io import StringIO
import os
from pathlib import Path

# Optional dependency handling
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@dataclass
class ProfileResult:
    """Result of a performance profiling session"""
    session_id: str
    start_time: float
    end_time: float
    duration: float
    cpu_stats: Dict[str, Any] = field(default_factory=dict)
    memory_stats: Dict[str, Any] = field(default_factory=dict)
    function_stats: List[Dict[str, Any]] = field(default_factory=list)
    hotspots: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "cpu_stats": self.cpu_stats,
            "memory_stats": self.memory_stats,
            "function_stats": self.function_stats,
            "hotspots": self.hotspots,
            "recommendations": self.recommendations
        }


class ProfilerContext:
    """Context manager for performance profiling"""
    
    def __init__(self, profiler: 'PerformanceProfiler', session_id: str, 
                 profile_cpu: bool = True, profile_memory: bool = True):
        self.profiler = profiler
        self.session_id = session_id
        self.profile_cpu = profile_cpu
        self.profile_memory = profile_memory
        self._cpu_profiler: Optional[cProfile.Profile] = None
        self._memory_start: Optional[Any] = None
        self._start_time: float = 0
        
    def __enter__(self):
        self._start_time = time.time()
        
        # Start CPU profiling
        if self.profile_cpu:
            self._cpu_profiler = cProfile.Profile()
            self._cpu_profiler.enable()
            
        # Start memory profiling
        if self.profile_memory:
            if not tracemalloc.is_tracing():
                tracemalloc.start()
            self._memory_start = tracemalloc.take_snapshot()
            
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        duration = end_time - self._start_time
        
        # Stop CPU profiling
        cpu_stats = {}
        function_stats = []
        if self._cpu_profiler:
            self._cpu_profiler.disable()
            cpu_stats, function_stats = self._analyze_cpu_profile()
            
        # Stop memory profiling
        memory_stats = {}
        if self.profile_memory and self._memory_start:
            memory_stats = self._analyze_memory_profile()
            
        # Create result
        result = ProfileResult(
            session_id=self.session_id,
            start_time=self._start_time,
            end_time=end_time,
            duration=duration,
            cpu_stats=cpu_stats,
            memory_stats=memory_stats,
            function_stats=function_stats
        )
        
        # Analyze for hotspots and recommendations
        result.hotspots = self._identify_hotspots(result)
        result.recommendations = self._generate_recommendations(result)
        
        # Store result
        self.profiler._store_result(result)
        
    def _analyze_cpu_profile(self) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Analyze CPU profiling results"""
        if not self._cpu_profiler:
            return {}, []
            
        # Get statistics
        stats_stream = StringIO()
        stats = pstats.Stats(self._cpu_profiler, stream=stats_stream)
        stats.sort_stats('cumulative')
        
        # Extract overall stats
        total_calls = stats.total_calls
        total_time = stats.total_tt
        
        cpu_stats = {
            "total_calls": total_calls,
            "total_time": total_time,
            "calls_per_second": total_calls / total_time if total_time > 0 else 0
        }
        
        # Extract function-level stats
        function_stats = []
        for func, (cc, nc, tt, ct, callers) in stats.stats.items():
            filename, line, function_name = func
            function_stats.append({
                "filename": filename,
                "line": line,
                "function": function_name,
                "call_count": cc,
                "total_time": tt,
                "cumulative_time": ct,
                "time_per_call": tt / cc if cc > 0 else 0
            })
            
        # Sort by cumulative time and limit
        function_stats.sort(key=lambda x: x["cumulative_time"], reverse=True)
        function_stats = function_stats[:50]  # Top 50 functions
        
        return cpu_stats, function_stats
        
    def _analyze_memory_profile(self) -> Dict[str, Any]:
        """Analyze memory profiling results"""
        if not self._memory_start:
            return {}
            
        try:
            memory_end = tracemalloc.take_snapshot()
            top_stats = memory_end.compare_to(self._memory_start, 'lineno')
            
            # Current memory usage
            current, peak = tracemalloc.get_traced_memory()
            
            # Top memory allocations
            allocations = []
            for stat in top_stats[:20]:  # Top 20 allocations
                allocations.append({
                    "filename": stat.traceback.format()[0] if stat.traceback.format() else "unknown",
                    "size_diff": stat.size_diff,
                    "count_diff": stat.count_diff,
                    "size": stat.size,
                    "count": stat.count
                })
                
            return {
                "current_memory": current,
                "peak_memory": peak,
                "memory_growth": current - (self._memory_start.total_size if hasattr(self._memory_start, 'total_size') else 0),
                "top_allocations": allocations
            }
        except Exception as e:
            return {"error": f"Memory analysis failed: {str(e)}"}
            
    def _identify_hotspots(self, result: ProfileResult) -> List[Dict[str, Any]]:
        """Identify performance hotspots"""
        hotspots = []
        
        # CPU hotspots - functions taking significant time
        if result.function_stats:
            total_time = sum(f["cumulative_time"] for f in result.function_stats)
            for func in result.function_stats[:10]:  # Top 10
                percentage = (func["cumulative_time"] / total_time * 100) if total_time > 0 else 0
                if percentage > 5:  # Functions taking >5% of total time
                    hotspots.append({
                        "type": "cpu_hotspot",
                        "function": func["function"],
                        "filename": func["filename"],
                        "percentage": percentage,
                        "cumulative_time": func["cumulative_time"],
                        "call_count": func["call_count"]
                    })
                    
        # Memory hotspots - large allocations
        if "top_allocations" in result.memory_stats:
            for alloc in result.memory_stats["top_allocations"][:5]:  # Top 5
                if alloc["size_diff"] > 1024 * 1024:  # > 1MB
                    hotspots.append({
                        "type": "memory_hotspot",
                        "filename": alloc["filename"],
                        "size_diff": alloc["size_diff"],
                        "size_mb": alloc["size_diff"] / (1024 * 1024),
                        "count_diff": alloc["count_diff"]
                    })
                    
        return hotspots
        
    def _generate_recommendations(self, result: ProfileResult) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # High-level performance analysis
        if result.duration > 1.0:  # Long-running operation
            recommendations.append("Consider breaking down long-running operations into smaller chunks")
            
        # CPU recommendations
        if result.cpu_stats.get("calls_per_second", 0) < 1000:
            recommendations.append("Low call rate detected - consider optimizing hot code paths")
            
        # Memory recommendations
        memory_growth = result.memory_stats.get("memory_growth", 0)
        if memory_growth > 10 * 1024 * 1024:  # > 10MB growth
            recommendations.append("High memory growth detected - check for memory leaks")
            
        # Function-specific recommendations
        for func in result.function_stats[:5]:
            if func["call_count"] > 10000:
                recommendations.append(f"High call count in {func['function']} - consider caching or optimization")
            if func["time_per_call"] > 0.01:  # > 10ms per call
                recommendations.append(f"Slow function {func['function']} - consider optimization")
                
        return recommendations


class PerformanceProfiler:
    """Advanced performance profiling system"""
    
    def __init__(self, 
                 max_results: int = 100,
                 auto_gc: bool = True,
                 enable_system_monitoring: bool = True):
        self.max_results = max_results
        self.auto_gc = auto_gc
        self.enable_system_monitoring = enable_system_monitoring
        
        # Results storage
        self._results: List[ProfileResult] = []
        self._lock = threading.RLock()
        
        # System monitoring
        self._system_stats: Dict[str, List[Dict[str, Any]]] = {}
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        # Session counter
        self._session_counter = 0
        
    def start_system_monitoring(self) -> None:
        """Start continuous system performance monitoring"""
        if self._monitoring_active:
            return
            
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(
            target=self._system_monitor_worker,
            name="perf-monitor",
            daemon=True
        )
        self._monitor_thread.start()
        
    def stop_system_monitoring(self) -> None:
        """Stop system performance monitoring"""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
            
    def profile(self, 
                session_id: str = None,
                profile_cpu: bool = True,
                profile_memory: bool = True) -> ProfilerContext:
        """Create a profiling context manager"""
        if session_id is None:
            with self._lock:
                self._session_counter += 1
                session_id = f"profile_{self._session_counter}_{int(time.time())}"
                
        return ProfilerContext(self, session_id, profile_cpu, profile_memory)
        
    def profile_function(self, func: Callable, *args, **kwargs) -> tuple[Any, ProfileResult]:
        """Profile a single function call"""
        session_id = f"func_{func.__name__}_{int(time.time())}"
        
        with self.profile(session_id) as profiler:
            result = func(*args, **kwargs)
            
        # Get the profile result
        profile_result = self.get_result(session_id)
        return result, profile_result
        
    def get_result(self, session_id: str) -> Optional[ProfileResult]:
        """Get profiling result by session ID"""
        with self._lock:
            for result in self._results:
                if result.session_id == session_id:
                    return result
            return None
            
    def get_all_results(self, limit: int = None) -> List[ProfileResult]:
        """Get all profiling results"""
        with self._lock:
            results = list(self._results)
            if limit:
                results = results[-limit:]
            return results
            
    def get_system_stats(self, metric: str = None, limit: int = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get system performance statistics"""
        with self._lock:
            if metric:
                stats = self._system_stats.get(metric, [])
                if limit:
                    stats = stats[-limit:]
                return {metric: stats}
            else:
                result = {}
                for key, values in self._system_stats.items():
                    if limit:
                        result[key] = values[-limit:]
                    else:
                        result[key] = list(values)
                return result
                
    def analyze_trends(self, session_ids: List[str] = None) -> Dict[str, Any]:
        """Analyze performance trends across multiple sessions"""
        with self._lock:
            if session_ids:
                results = [r for r in self._results if r.session_id in session_ids]
            else:
                results = list(self._results)
                
        if not results:
            return {"error": "No results to analyze"}
            
        # Calculate trends
        durations = [r.duration for r in results]
        cpu_times = [r.cpu_stats.get("total_time", 0) for r in results]
        memory_usage = [r.memory_stats.get("peak_memory", 0) for r in results]
        
        trends = {
            "duration": {
                "min": min(durations),
                "max": max(durations),
                "avg": sum(durations) / len(durations),
                "trend": self._calculate_trend(durations)
            },
            "cpu_time": {
                "min": min(cpu_times),
                "max": max(cpu_times),
                "avg": sum(cpu_times) / len(cpu_times),
                "trend": self._calculate_trend(cpu_times)
            },
            "memory_usage": {
                "min": min(memory_usage),
                "max": max(memory_usage),
                "avg": sum(memory_usage) / len(memory_usage),
                "trend": self._calculate_trend(memory_usage)
            },
            "total_sessions": len(results),
            "time_range": {
                "start": min(r.start_time for r in results),
                "end": max(r.end_time for r in results)
            }
        }
        
        return trends
        
    def export_results(self, filepath: Union[str, Path], format: str = "json") -> None:
        """Export profiling results to file"""
        filepath = Path(filepath)
        
        with self._lock:
            data = {
                "export_time": time.time(),
                "profiler_version": "1.0.0",
                "results": [r.to_dict() for r in self._results],
                "system_stats": self._system_stats
            }
            
        if format.lower() == "json":
            import json
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
            
    def clear_results(self, older_than: float = None) -> int:
        """Clear profiling results"""
        with self._lock:
            if older_than:
                cutoff_time = time.time() - older_than
                original_count = len(self._results)
                self._results = [r for r in self._results if r.end_time > cutoff_time]
                return original_count - len(self._results)
            else:
                count = len(self._results)
                self._results.clear()
                return count
                
    def _store_result(self, result: ProfileResult) -> None:
        """Store a profiling result"""
        with self._lock:
            self._results.append(result)
            
            # Limit number of stored results
            if len(self._results) > self.max_results:
                self._results = self._results[-self.max_results:]
                
            # Trigger garbage collection if enabled
            if self.auto_gc:
                gc.collect()
                
    def _system_monitor_worker(self) -> None:
        """Background worker for system monitoring"""
        if not HAS_PSUTIL:
            print("⚠️ System monitoring disabled - psutil not available")
            return
            
        while self._monitoring_active:
            try:
                timestamp = time.time()
                
                # CPU stats
                cpu_percent = psutil.cpu_percent(interval=None)
                cpu_count = psutil.cpu_count()
                
                # Memory stats
                memory = psutil.virtual_memory()
                
                # Disk I/O
                disk_io = psutil.disk_io_counters()
                
                # Network I/O
                net_io = psutil.net_io_counters()
                
                # Process stats for current process
                process = psutil.Process()
                process_info = process.as_dict(attrs=['cpu_percent', 'memory_info', 'num_threads'])
                
                # Store stats
                with self._lock:
                    # Initialize metric lists if needed
                    metrics = ['cpu', 'memory', 'disk_io', 'network_io', 'process']
                    for metric in metrics:
                        if metric not in self._system_stats:
                            self._system_stats[metric] = []
                            
                    # Add current measurements
                    self._system_stats['cpu'].append({
                        "timestamp": timestamp,
                        "cpu_percent": cpu_percent,
                        "cpu_count": cpu_count
                    })
                    
                    self._system_stats['memory'].append({
                        "timestamp": timestamp,
                        "total": memory.total,
                        "available": memory.available,
                        "percent": memory.percent,
                        "used": memory.used
                    })
                    
                    if disk_io:
                        self._system_stats['disk_io'].append({
                            "timestamp": timestamp,
                            "read_bytes": disk_io.read_bytes,
                            "write_bytes": disk_io.write_bytes,
                            "read_count": disk_io.read_count,
                            "write_count": disk_io.write_count
                        })
                        
                    if net_io:
                        self._system_stats['network_io'].append({
                            "timestamp": timestamp,
                            "bytes_sent": net_io.bytes_sent,
                            "bytes_recv": net_io.bytes_recv,
                            "packets_sent": net_io.packets_sent,
                            "packets_recv": net_io.packets_recv
                        })
                        
                    self._system_stats['process'].append({
                        "timestamp": timestamp,
                        "cpu_percent": process_info.get('cpu_percent', 0),
                        "memory_rss": process_info.get('memory_info', {}).get('rss', 0),
                        "memory_vms": process_info.get('memory_info', {}).get('vms', 0),
                        "num_threads": process_info.get('num_threads', 0)
                    })
                    
                    # Limit history size
                    for metric in self._system_stats:
                        if len(self._system_stats[metric]) > 1000:  # Keep last 1000 entries
                            self._system_stats[metric] = self._system_stats[metric][-1000:]
                            
            except Exception as e:
                print(f"Error in system monitor: {e}")
                
            time.sleep(5)  # Monitor every 5 seconds
            
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for a series of values"""
        if len(values) < 2:
            return "insufficient_data"
            
        # Simple linear trend calculation
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        
        if abs(slope) < 0.001:  # Threshold for considering flat
            return "stable"
        elif slope > 0:
            return "increasing"
        else:
            return "decreasing"


# Convenience decorators for profiling
def profile_performance(session_id: str = None, 
                        profile_cpu: bool = True, 
                        profile_memory: bool = True):
    """Decorator for automatic function profiling"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get the global profiler (would be injected via DI in real usage)
            profiler = get_global_profiler()
            if not profiler:
                return func(*args, **kwargs)
                
            func_session_id = session_id or f"{func.__module__}.{func.__qualname__}"
            with profiler.profile(func_session_id, profile_cpu, profile_memory):
                return func(*args, **kwargs)
                
        return wrapper
    return decorator


# Global profiler instance (would be managed by DI container in production)
_global_profiler: Optional[PerformanceProfiler] = None


def get_global_profiler() -> Optional[PerformanceProfiler]:
    """Get the global profiler instance"""
    return _global_profiler


def set_global_profiler(profiler: PerformanceProfiler) -> None:
    """Set the global profiler instance"""
    global _global_profiler
    _global_profiler = profiler