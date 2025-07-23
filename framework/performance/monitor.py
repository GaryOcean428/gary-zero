"""
Performance monitoring and metrics collection.

Provides comprehensive performance monitoring including:
- Real-time performance metrics collection
- Resource usage tracking (CPU, memory, I/O)
- Performance alerting and optimization suggestions
- Detailed performance analytics
"""

import asyncio
import json
import logging
import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from typing import Any

import psutil

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric."""
    name: str
    value: float
    timestamp: float
    tags: dict[str, str] = field(default_factory=dict)
    unit: str = ""


@dataclass
class ResourceSnapshot:
    """System resource usage snapshot."""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    process_count: int
    load_average: list[float] | None = None


class MetricsCollector:
    """Collects and aggregates performance metrics."""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._metrics: dict[str, deque[PerformanceMetric]] = defaultdict(
            lambda: deque(maxlen=max_history)
        )
        self._lock = threading.RLock()

    def record(self,
               name: str,
               value: float,
               tags: dict[str, str] | None = None,
               unit: str = "") -> None:
        """Record a performance metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags or {},
            unit=unit
        )

        with self._lock:
            self._metrics[name].append(metric)

    def get_latest(self, name: str) -> PerformanceMetric | None:
        """Get the latest metric value."""
        with self._lock:
            if name in self._metrics and self._metrics[name]:
                return self._metrics[name][-1]
        return None

    def get_history(self,
                   name: str,
                   limit: int | None = None) -> list[PerformanceMetric]:
        """Get metric history."""
        with self._lock:
            if name not in self._metrics:
                return []

            metrics = list(self._metrics[name])
            if limit:
                return metrics[-limit:]
            return metrics

    def get_average(self,
                   name: str,
                   duration_seconds: float | None = None) -> float | None:
        """Get average metric value over a time period."""
        with self._lock:
            if name not in self._metrics or not self._metrics[name]:
                return None

            current_time = time.time()
            values = []

            for metric in reversed(self._metrics[name]):
                if duration_seconds and (current_time - metric.timestamp) > duration_seconds:
                    break
                values.append(metric.value)

            return sum(values) / len(values) if values else None

    def get_percentile(self,
                      name: str,
                      percentile: float,
                      duration_seconds: float | None = None) -> float | None:
        """Get percentile metric value over a time period."""
        with self._lock:
            if name not in self._metrics or not self._metrics[name]:
                return None

            current_time = time.time()
            values = []

            for metric in reversed(self._metrics[name]):
                if duration_seconds and (current_time - metric.timestamp) > duration_seconds:
                    break
                values.append(metric.value)

            if not values:
                return None

            values.sort()
            index = int((percentile / 100.0) * len(values))
            index = min(index, len(values) - 1)
            return values[index]

    def get_all_metrics(self) -> dict[str, list[PerformanceMetric]]:
        """Get all metrics."""
        with self._lock:
            return {name: list(metrics) for name, metrics in self._metrics.items()}

    def clear(self, name: str | None = None) -> None:
        """Clear metrics history."""
        with self._lock:
            if name:
                if name in self._metrics:
                    self._metrics[name].clear()
            else:
                self._metrics.clear()


class ResourceTracker:
    """Tracks system resource usage."""

    def __init__(self,
                 collection_interval: float = 5.0,
                 max_history: int = 720):  # 1 hour at 5-second intervals
        self.collection_interval = collection_interval
        self.max_history = max_history
        self._snapshots: deque[ResourceSnapshot] = deque(maxlen=max_history)
        self._running = False
        self._task: asyncio.Task | None = None
        self._lock = threading.RLock()

        # Initialize baseline values
        self._initial_disk_io = psutil.disk_io_counters()
        self._initial_network = psutil.net_io_counters()

    def _get_resource_snapshot(self) -> ResourceSnapshot:
        """Get current resource usage snapshot."""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read_mb = (
                (disk_io.read_bytes - self._initial_disk_io.read_bytes) / 1024 / 1024
                if self._initial_disk_io else 0
            )
            disk_write_mb = (
                (disk_io.write_bytes - self._initial_disk_io.write_bytes) / 1024 / 1024
                if self._initial_disk_io else 0
            )

            # Network I/O
            network = psutil.net_io_counters()
            network_sent_mb = (
                (network.bytes_sent - self._initial_network.bytes_sent) / 1024 / 1024
                if self._initial_network else 0
            )
            network_recv_mb = (
                (network.bytes_recv - self._initial_network.bytes_recv) / 1024 / 1024
                if self._initial_network else 0
            )

            # Process information
            process_count = len(psutil.pids())

            # Load average (Unix only)
            load_average = None
            try:
                load_average = list(psutil.getloadavg())
            except AttributeError:
                # Not available on Windows
                pass

            return ResourceSnapshot(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                memory_available_mb=memory.available / 1024 / 1024,
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                process_count=process_count,
                load_average=load_average
            )
        except Exception as e:
            logger.error(f"Error collecting resource snapshot: {e}")
            # Return minimal snapshot
            return ResourceSnapshot(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_io_read_mb=0.0,
                disk_io_write_mb=0.0,
                network_sent_mb=0.0,
                network_recv_mb=0.0,
                process_count=0
            )

    async def _collection_loop(self) -> None:
        """Background loop for collecting resource snapshots."""
        while self._running:
            try:
                snapshot = self._get_resource_snapshot()
                with self._lock:
                    self._snapshots.append(snapshot)

                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in resource collection loop: {e}")
                await asyncio.sleep(self.collection_interval)

    async def start(self) -> None:
        """Start resource tracking."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._collection_loop())
        logger.info("Resource tracking started")

    async def stop(self) -> None:
        """Stop resource tracking."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Resource tracking stopped")

    def get_latest_snapshot(self) -> ResourceSnapshot | None:
        """Get the latest resource snapshot."""
        with self._lock:
            return self._snapshots[-1] if self._snapshots else None

    def get_snapshots(self,
                     limit: int | None = None,
                     since: float | None = None) -> list[ResourceSnapshot]:
        """Get resource snapshots."""
        with self._lock:
            snapshots = list(self._snapshots)

            # Filter by time if specified
            if since:
                snapshots = [s for s in snapshots if s.timestamp >= since]

            # Limit results
            if limit:
                snapshots = snapshots[-limit:]

            return snapshots

    def get_average_usage(self,
                         duration_seconds: float | None = None) -> dict[str, float]:
        """Get average resource usage over a time period."""
        snapshots = self.get_snapshots(
            since=time.time() - duration_seconds if duration_seconds else None
        )

        if not snapshots:
            return {}

        return {
            'cpu_percent': sum(s.cpu_percent for s in snapshots) / len(snapshots),
            'memory_percent': sum(s.memory_percent for s in snapshots) / len(snapshots),
            'memory_used_mb': sum(s.memory_used_mb for s in snapshots) / len(snapshots),
            'disk_io_read_mb': snapshots[-1].disk_io_read_mb if snapshots else 0,
            'disk_io_write_mb': snapshots[-1].disk_io_write_mb if snapshots else 0,
            'network_sent_mb': snapshots[-1].network_sent_mb if snapshots else 0,
            'network_recv_mb': snapshots[-1].network_recv_mb if snapshots else 0,
        }


class PerformanceMonitor:
    """Comprehensive performance monitoring system."""

    def __init__(self,
                 metrics_collector: MetricsCollector | None = None,
                 resource_tracker: ResourceTracker | None = None):
        self.metrics = metrics_collector or MetricsCollector()
        self.resources = resource_tracker or ResourceTracker()
        self._operation_timers: dict[str, float] = {}
        self._lock = threading.RLock()

    async def start(self) -> None:
        """Start performance monitoring."""
        await self.resources.start()
        logger.info("Performance monitoring started")

    async def stop(self) -> None:
        """Stop performance monitoring."""
        await self.resources.stop()
        logger.info("Performance monitoring stopped")

    @contextmanager
    def timer(self, operation_name: str, tags: dict[str, str] | None = None):
        """Context manager for timing operations."""
        start_time = time.time()

        try:
            yield
        finally:
            duration = time.time() - start_time
            self.metrics.record(
                f"operation_duration_{operation_name}",
                duration,
                tags=tags,
                unit="seconds"
            )

    def timed(self, operation_name: str, tags: dict[str, str] | None = None):
        """Decorator for timing function execution."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.timer(operation_name, tags):
                    return func(*args, **kwargs)
            return wrapper
        return decorator

    def async_timed(self, operation_name: str, tags: dict[str, str] | None = None):
        """Decorator for timing async function execution."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                with self.timer(operation_name, tags):
                    return await func(*args, **kwargs)
            return wrapper
        return decorator

    def record_counter(self,
                      name: str,
                      value: float = 1.0,
                      tags: dict[str, str] | None = None) -> None:
        """Record a counter metric."""
        self.metrics.record(f"counter_{name}", value, tags=tags, unit="count")

    def record_gauge(self,
                    name: str,
                    value: float,
                    tags: dict[str, str] | None = None) -> None:
        """Record a gauge metric."""
        self.metrics.record(f"gauge_{name}", value, tags=tags)

    def record_histogram(self,
                        name: str,
                        value: float,
                        tags: dict[str, str] | None = None) -> None:
        """Record a histogram metric."""
        self.metrics.record(f"histogram_{name}", value, tags=tags)

    def get_performance_summary(self,
                               duration_seconds: float = 300) -> dict[str, Any]:
        """Get comprehensive performance summary."""
        # Resource usage
        resource_avg = self.resources.get_average_usage(duration_seconds)
        latest_snapshot = self.resources.get_latest_snapshot()

        # Key metrics
        summary = {
            'timestamp': time.time(),
            'duration_seconds': duration_seconds,
            'resource_usage': {
                'current': {
                    'cpu_percent': latest_snapshot.cpu_percent if latest_snapshot else 0,
                    'memory_percent': latest_snapshot.memory_percent if latest_snapshot else 0,
                    'memory_used_mb': latest_snapshot.memory_used_mb if latest_snapshot else 0,
                },
                'average': resource_avg
            },
            'operation_metrics': {},
            'alerts': []
        }

        # Operation timing metrics
        for metric_name, metrics_deque in self.metrics._metrics.items():
            if metric_name.startswith('operation_duration_'):
                operation_name = metric_name.replace('operation_duration_', '')
                recent_metrics = [
                    m for m in metrics_deque
                    if time.time() - m.timestamp <= duration_seconds
                ]

                if recent_metrics:
                    values = [m.value for m in recent_metrics]
                    summary['operation_metrics'][operation_name] = {
                        'count': len(values),
                        'avg_duration': sum(values) / len(values),
                        'min_duration': min(values),
                        'max_duration': max(values),
                        'p95_duration': self.metrics.get_percentile(metric_name, 95, duration_seconds),
                        'p99_duration': self.metrics.get_percentile(metric_name, 99, duration_seconds),
                    }

        # Generate alerts
        if latest_snapshot:
            if latest_snapshot.cpu_percent > 80:
                summary['alerts'].append({
                    'type': 'high_cpu',
                    'level': 'warning',
                    'message': f'High CPU usage: {latest_snapshot.cpu_percent:.1f}%'
                })

            if latest_snapshot.memory_percent > 80:
                summary['alerts'].append({
                    'type': 'high_memory',
                    'level': 'warning',
                    'message': f'High memory usage: {latest_snapshot.memory_percent:.1f}%'
                })

        return summary

    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in the specified format."""
        if format == "json":
            all_metrics = self.metrics.get_all_metrics()
            serializable_metrics = {}

            for name, metrics_list in all_metrics.items():
                serializable_metrics[name] = [
                    {
                        'value': m.value,
                        'timestamp': m.timestamp,
                        'tags': m.tags,
                        'unit': m.unit
                    }
                    for m in metrics_list
                ]

            return json.dumps(serializable_metrics, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global performance monitor instance
_default_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get the default performance monitor instance."""
    global _default_monitor
    if _default_monitor is None:
        _default_monitor = PerformanceMonitor()
    return _default_monitor


def timer(operation_name: str, tags: dict[str, str] | None = None):
    """Decorator for timing operations using the default monitor."""
    return get_performance_monitor().timed(operation_name, tags)


def async_timer(operation_name: str, tags: dict[str, str] | None = None):
    """Decorator for timing async operations using the default monitor."""
    return get_performance_monitor().async_timed(operation_name, tags)
