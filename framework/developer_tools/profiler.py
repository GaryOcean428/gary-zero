"""
Performance Profiler Module

Provides comprehensive performance profiling and analysis capabilities
for code optimization and bottleneck identification.
"""

import asyncio
import cProfile
import gc
import io
import pstats
import sys
import threading
import time
import tracemalloc
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import logging

logger = logging.getLogger(__name__)

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import memory_profiler
    HAS_MEMORY_PROFILER = True
except ImportError:
    HAS_MEMORY_PROFILER = False

try:
    import line_profiler
    HAS_LINE_PROFILER = True
except ImportError:
    HAS_LINE_PROFILER = False


@dataclass
class ProfileStats:
    """Performance profiling statistics"""
    function_name: str
    filename: str
    line_number: int
    call_count: int
    total_time: float
    cumulative_time: float
    per_call_time: float
    percentage: float


@dataclass
class MemoryStats:
    """Memory usage statistics"""
    current_memory: float
    peak_memory: float
    memory_increase: float
    allocations: int
    deallocations: int
    active_blocks: int


@dataclass
class SystemStats:
    """System resource statistics"""
    cpu_percent: float
    memory_percent: float
    memory_available: int
    memory_used: int
    disk_io_read: int
    disk_io_write: int
    network_io_sent: int
    network_io_recv: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ProfilingSession:
    """Profiling session data"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    profile_stats: List[ProfileStats] = field(default_factory=list)
    memory_stats: Optional[MemoryStats] = None
    system_stats: List[SystemStats] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceProfiler:
    """Advanced performance profiler"""
    
    def __init__(self):
        self._sessions: Dict[str, ProfilingSession] = {}
        self._active_session: Optional[str] = None
        self._profiler: Optional[cProfile.Profile] = None
        self._memory_tracker = None
        self._system_monitor = None
        self._monitoring = False
        self._lock = threading.Lock()
    
    def start_session(
        self, 
        session_id: Optional[str] = None,
        profile_memory: bool = True,
        profile_system: bool = True,
        sample_rate: float = 1.0
    ) -> str:
        """Start a new profiling session"""
        if session_id is None:
            session_id = f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with self._lock:
            session = ProfilingSession(
                session_id=session_id,
                start_time=datetime.now(),
                metadata={
                    'profile_memory': profile_memory,
                    'profile_system': profile_system,
                    'sample_rate': sample_rate
                }
            )
            
            self._sessions[session_id] = session
            self._active_session = session_id
            
            # Start profiling
            self._profiler = cProfile.Profile()
            self._profiler.enable()
            
            # Start memory tracking
            if profile_memory and HAS_MEMORY_PROFILER:
                tracemalloc.start()
                self._memory_tracker = tracemalloc
            
            # Start system monitoring
            if profile_system:
                self._start_system_monitoring()
            
            logger.info(f"Started profiling session {session_id}")
            return session_id
    
    def stop_session(self, session_id: Optional[str] = None) -> Optional[ProfilingSession]:
        """Stop profiling session"""
        if session_id is None:
            session_id = self._active_session
        
        if not session_id or session_id not in self._sessions:
            return None
        
        with self._lock:
            session = self._sessions[session_id]
            session.end_time = datetime.now()
            session.duration = (session.end_time - session.start_time).total_seconds()
            
            # Stop profiling
            if self._profiler:
                self._profiler.disable()
                session.profile_stats = self._extract_profile_stats()
                self._profiler = None
            
            # Stop memory tracking
            if self._memory_tracker:
                session.memory_stats = self._extract_memory_stats()
                tracemalloc.stop()
                self._memory_tracker = None
            
            # Stop system monitoring
            if self._monitoring:
                self._stop_system_monitoring()
            
            if self._active_session == session_id:
                self._active_session = None
            
            logger.info(f"Stopped profiling session {session_id}")
            return session
    
    @contextmanager
    def profile_context(
        self,
        session_id: Optional[str] = None,
        profile_memory: bool = True,
        profile_system: bool = True
    ):
        """Context manager for profiling a code block"""
        session_id = self.start_session(session_id, profile_memory, profile_system)
        try:
            yield session_id
        finally:
            self.stop_session(session_id)
    
    def get_session(self, session_id: str) -> Optional[ProfilingSession]:
        """Get profiling session by ID"""
        return self._sessions.get(session_id)
    
    def get_sessions(self) -> List[ProfilingSession]:
        """Get all profiling sessions"""
        return list(self._sessions.values())
    
    def analyze_performance(self, session_id: str) -> Dict[str, Any]:
        """Analyze performance data from session"""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        analysis = {
            'session_id': session_id,
            'duration': session.duration,
            'total_functions': len(session.profile_stats),
            'top_functions': [],
            'bottlenecks': [],
            'memory_usage': {},
            'system_performance': {},
            'recommendations': []
        }
        
        # Analyze function performance
        if session.profile_stats:
            # Sort by cumulative time
            sorted_stats = sorted(
                session.profile_stats,
                key=lambda x: x.cumulative_time,
                reverse=True
            )
            
            analysis['top_functions'] = [
                {
                    'function': stat.function_name,
                    'file': stat.filename,
                    'cumulative_time': stat.cumulative_time,
                    'percentage': stat.percentage,
                    'calls': stat.call_count
                }
                for stat in sorted_stats[:10]
            ]
            
            # Identify bottlenecks (functions taking > 10% of total time)
            total_time = sum(stat.cumulative_time for stat in session.profile_stats)
            bottlenecks = [
                stat for stat in sorted_stats
                if stat.cumulative_time / total_time > 0.1
            ]
            
            analysis['bottlenecks'] = [
                {
                    'function': stat.function_name,
                    'file': stat.filename,
                    'impact': stat.cumulative_time / total_time,
                    'optimization_potential': 'HIGH' if stat.cumulative_time / total_time > 0.2 else 'MEDIUM'
                }
                for stat in bottlenecks
            ]
        
        # Analyze memory usage
        if session.memory_stats:
            analysis['memory_usage'] = {
                'current_mb': session.memory_stats.current_memory / 1024 / 1024,
                'peak_mb': session.memory_stats.peak_memory / 1024 / 1024,
                'increase_mb': session.memory_stats.memory_increase / 1024 / 1024,
                'allocations': session.memory_stats.allocations,
                'active_blocks': session.memory_stats.active_blocks
            }
        
        # Analyze system performance
        if session.system_stats:
            avg_cpu = sum(stat.cpu_percent for stat in session.system_stats) / len(session.system_stats)
            avg_memory = sum(stat.memory_percent for stat in session.system_stats) / len(session.system_stats)
            
            analysis['system_performance'] = {
                'average_cpu_percent': avg_cpu,
                'average_memory_percent': avg_memory,
                'peak_cpu_percent': max(stat.cpu_percent for stat in session.system_stats),
                'peak_memory_percent': max(stat.memory_percent for stat in session.system_stats)
            }
        
        # Generate recommendations
        recommendations = []
        
        if analysis['bottlenecks']:
            recommendations.append({
                'type': 'performance',
                'severity': 'high',
                'message': f"Found {len(analysis['bottlenecks'])} performance bottlenecks",
                'suggestion': "Focus optimization efforts on the identified bottleneck functions"
            })
        
        if analysis.get('memory_usage', {}).get('increase_mb', 0) > 100:
            recommendations.append({
                'type': 'memory',
                'severity': 'medium',
                'message': "High memory usage detected",
                'suggestion': "Consider implementing memory pooling or object reuse"
            })
        
        if analysis.get('system_performance', {}).get('average_cpu_percent', 0) > 80:
            recommendations.append({
                'type': 'cpu',
                'severity': 'high',
                'message': "High CPU usage detected",
                'suggestion': "Consider parallelization or algorithm optimization"
            })
        
        analysis['recommendations'] = recommendations
        return analysis
    
    def _extract_profile_stats(self) -> List[ProfileStats]:
        """Extract statistics from cProfile"""
        if not self._profiler:
            return []
        
        # Get statistics
        s = io.StringIO()
        ps = pstats.Stats(self._profiler, stream=s)
        ps.sort_stats('cumulative')
        
        stats = []
        total_time = ps.total_tt
        
        for (filename, line_number, function_name), (call_count, _, cumulative_time, _, _) in ps.stats.items():
            per_call_time = cumulative_time / call_count if call_count > 0 else 0
            percentage = (cumulative_time / total_time * 100) if total_time > 0 else 0
            
            stats.append(ProfileStats(
                function_name=function_name,
                filename=filename,
                line_number=line_number,
                call_count=call_count,
                total_time=cumulative_time,
                cumulative_time=cumulative_time,
                per_call_time=per_call_time,
                percentage=percentage
            ))
        
        return stats
    
    def _extract_memory_stats(self) -> Optional[MemoryStats]:
        """Extract memory statistics"""
        if not self._memory_tracker:
            return None
        
        try:
            current, peak = tracemalloc.get_traced_memory()
            snapshot = tracemalloc.take_snapshot()
            
            # Calculate allocations
            allocations = 0
            deallocations = 0
            active_blocks = 0
            
            for stat in snapshot.statistics('filename'):
                allocations += stat.count
                active_blocks += stat.count
            
            return MemoryStats(
                current_memory=current,
                peak_memory=peak,
                memory_increase=peak - current,
                allocations=allocations,
                deallocations=deallocations,
                active_blocks=active_blocks
            )
        except Exception as e:
            logger.error(f"Error extracting memory stats: {e}")
            return None
    
    def _start_system_monitoring(self):
        """Start system resource monitoring"""
        if not HAS_PSUTIL:
            logger.warning("psutil not available, system monitoring disabled")
            return
            
        self._monitoring = True
        
        def monitor():
            session = self._sessions.get(self._active_session)
            if not session:
                return
            
            while self._monitoring:
                try:
                    # Get system stats
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    disk_io = psutil.disk_io_counters()
                    network_io = psutil.net_io_counters()
                    
                    stat = SystemStats(
                        cpu_percent=cpu_percent,
                        memory_percent=memory.percent,
                        memory_available=memory.available,
                        memory_used=memory.used,
                        disk_io_read=disk_io.read_bytes if disk_io else 0,
                        disk_io_write=disk_io.write_bytes if disk_io else 0,
                        network_io_sent=network_io.bytes_sent if network_io else 0,
                        network_io_recv=network_io.bytes_recv if network_io else 0
                    )
                    
                    session.system_stats.append(stat)
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error monitoring system stats: {e}")
                    break
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def _stop_system_monitoring(self):
        """Stop system resource monitoring"""
        self._monitoring = False


class CodeProfiler:
    """Line-by-line code profiler"""
    
    def __init__(self):
        self._profiler = None
        self._enabled = HAS_LINE_PROFILER
    
    def profile_function(self, func: Callable) -> Callable:
        """Decorator to profile a function line by line"""
        if not self._enabled:
            logger.warning("Line profiler not available")
            return func
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use line_profiler if available
            if HAS_LINE_PROFILER:
                profiler = line_profiler.LineProfiler()
                profiler.add_function(func)
                profiler.enable_by_count()
                
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    profiler.disable_by_count()
                    profiler.print_stats()
            else:
                return func(*args, **kwargs)
        
        return wrapper
    
    def profile_code_block(self, code: str, globals_dict: Optional[Dict] = None):
        """Profile a code block"""
        if not self._enabled:
            logger.warning("Line profiler not available")
            return
        
        if globals_dict is None:
            globals_dict = globals()
        
        if HAS_LINE_PROFILER:
            profiler = line_profiler.LineProfiler()
            profiler.enable_by_count()
            
            try:
                exec(code, globals_dict)
            finally:
                profiler.disable_by_count()
                profiler.print_stats()


class MemoryProfiler:
    """Memory usage profiler"""
    
    def __init__(self):
        self._enabled = HAS_MEMORY_PROFILER
        self._baseline_memory = None
    
    def profile_function(self, func: Callable) -> Callable:
        """Decorator to profile memory usage of a function"""
        if not self._enabled:
            return func
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            if HAS_MEMORY_PROFILER:
                # Get memory before
                mem_before = memory_profiler.memory_usage()[0]
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Get memory after
                mem_after = memory_profiler.memory_usage()[0]
                mem_diff = mem_after - mem_before
                
                logger.info(f"Memory usage for {func.__name__}: {mem_diff:.2f} MB")
                return result
            else:
                return func(*args, **kwargs)
        
        return wrapper
    
    def track_memory_usage(self, interval: float = 0.1) -> List[float]:
        """Track memory usage over time"""
        if not self._enabled:
            return []
        
        if HAS_MEMORY_PROFILER:
            return memory_profiler.memory_usage(interval=interval)
        return []
    
    def set_memory_baseline(self):
        """Set current memory usage as baseline"""
        if HAS_MEMORY_PROFILER:
            self._baseline_memory = memory_profiler.memory_usage()[0]
    
    def get_memory_increase(self) -> float:
        """Get memory increase since baseline"""
        if not self._enabled or self._baseline_memory is None:
            return 0.0
        
        if HAS_MEMORY_PROFILER:
            current_memory = memory_profiler.memory_usage()[0]
            return current_memory - self._baseline_memory
        return 0.0


# Profiling decorators
def profile_performance(
    session_id: Optional[str] = None,
    profile_memory: bool = True,
    profile_system: bool = True
):
    """Decorator to profile function performance"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            profiler = PerformanceProfiler()
            with profiler.profile_context(session_id, profile_memory, profile_system) as sid:
                result = func(*args, **kwargs)
                
                # Log performance summary
                session = profiler.get_session(sid)
                if session:
                    analysis = profiler.analyze_performance(sid)
                    logger.info(f"Performance analysis for {func.__name__}: {analysis}")
                
                return result
        return wrapper
    return decorator


def profile_memory(func: Callable) -> Callable:
    """Decorator to profile memory usage"""
    memory_profiler = MemoryProfiler()
    return memory_profiler.profile_function(func)


def profile_code_lines(func: Callable) -> Callable:
    """Decorator to profile code line by line"""
    code_profiler = CodeProfiler()
    return code_profiler.profile_function(func)


class AsyncProfiler:
    """Async-aware profiler"""
    
    def __init__(self):
        self._profiler = PerformanceProfiler()
        self._async_sessions: Dict[str, str] = {}
    
    async def profile_async_function(self, func: Callable, *args, **kwargs):
        """Profile an async function"""
        session_id = self._profiler.start_session()
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            return result
        finally:
            self._profiler.stop_session(session_id)
    
    @contextmanager
    async def profile_async_context(self, session_id: Optional[str] = None):
        """Async context manager for profiling"""
        session_id = self._profiler.start_session(session_id)
        try:
            yield session_id
        finally:
            self._profiler.stop_session(session_id)


# Global profiler instance
_global_profiler = PerformanceProfiler()

# Convenience functions
def start_profiling(session_id: Optional[str] = None) -> str:
    """Start global profiling session"""
    return _global_profiler.start_session(session_id)

def stop_profiling(session_id: Optional[str] = None) -> Optional[ProfilingSession]:
    """Stop global profiling session"""
    return _global_profiler.stop_session(session_id)

def analyze_session(session_id: str) -> Dict[str, Any]:
    """Analyze profiling session"""
    return _global_profiler.analyze_performance(session_id)