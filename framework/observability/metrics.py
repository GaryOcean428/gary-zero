"""
Comprehensive Metrics Collection and Aggregation System

Provides enterprise-grade metrics collection with:
- Counter, Gauge, Histogram, and Timer metrics
- Automatic system and application metrics
- Custom metric definitions with labels
- Aggregation and export capabilities
- Integration with monitoring systems
"""

import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Optional dependency handling
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("⚠️ psutil not available - system metrics collection disabled")


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricValue:
    """Represents a single metric measurement"""
    name: str
    value: Union[int, float]
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class CustomMetric:
    """Configuration for custom metrics"""
    name: str
    metric_type: MetricType
    description: str
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None  # For histograms
    
    def create_value(self, value: Union[int, float], labels: Dict[str, str] = None) -> MetricValue:
        """Create a metric value with validation"""
        if labels is None:
            labels = {}
            
        # Validate labels
        for label in self.labels:
            if label not in labels:
                raise ValueError(f"Required label '{label}' not provided for metric '{self.name}'")
                
        return MetricValue(
            name=self.name,
            value=value,
            labels=labels,
            metric_type=self.metric_type
        )


class MetricsRegistry:
    """Central registry for all metrics and their configurations"""
    
    def __init__(self):
        self._metrics: Dict[str, CustomMetric] = {}
        self._lock = threading.RLock()
        
    def register(self, metric: CustomMetric) -> None:
        """Register a new metric definition"""
        with self._lock:
            if metric.name in self._metrics:
                raise ValueError(f"Metric '{metric.name}' already registered")
            self._metrics[metric.name] = metric
            
    def get_metric(self, name: str) -> Optional[CustomMetric]:
        """Get metric definition by name"""
        with self._lock:
            return self._metrics.get(name)
            
    def list_metrics(self) -> List[CustomMetric]:
        """List all registered metrics"""
        with self._lock:
            return list(self._metrics.values())
            
    def unregister(self, name: str) -> bool:
        """Unregister a metric"""
        with self._lock:
            return self._metrics.pop(name, None) is not None


class MetricsCollector:
    """Advanced metrics collection system with automatic aggregation"""
    
    def __init__(self, 
                 registry: Optional[MetricsRegistry] = None,
                 buffer_size: int = 10000,
                 flush_interval: float = 60.0,
                 enable_system_metrics: bool = True):
        self.registry = registry or MetricsRegistry()
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.enable_system_metrics = enable_system_metrics
        
        # Storage
        self._metrics_buffer: deque = deque(maxlen=buffer_size)
        self._aggregated_metrics: Dict[str, Dict] = defaultdict(dict)
        self._lock = threading.RLock()
        
        # Background processing
        self._running = False
        self._flush_thread: Optional[threading.Thread] = None
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="metrics")
        
        # Callbacks
        self._export_callbacks: List[Callable[[List[MetricValue]], None]] = []
        
        # Initialize built-in metrics
        self._initialize_builtin_metrics()
        
    def _initialize_builtin_metrics(self):
        """Register built-in system and application metrics"""
        builtin_metrics = [
            CustomMetric("system_cpu_percent", MetricType.GAUGE, "CPU usage percentage"),
            CustomMetric("system_memory_percent", MetricType.GAUGE, "Memory usage percentage"),
            CustomMetric("system_disk_percent", MetricType.GAUGE, "Disk usage percentage", ["mount_point"]),
            CustomMetric("system_network_bytes", MetricType.COUNTER, "Network bytes", ["direction", "interface"]),
            CustomMetric("request_count", MetricType.COUNTER, "HTTP request count", ["method", "endpoint", "status"]),
            CustomMetric("request_duration", MetricType.TIMER, "HTTP request duration", ["method", "endpoint"]),
            CustomMetric("agent_active_sessions", MetricType.GAUGE, "Number of active agent sessions"),
            CustomMetric("agent_task_duration", MetricType.HISTOGRAM, "Agent task duration", ["task_type"], 
                        buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]),
            CustomMetric("model_inference_count", MetricType.COUNTER, "Model inference count", ["model", "provider"]),
            CustomMetric("model_inference_duration", MetricType.TIMER, "Model inference duration", ["model", "provider"]),
            CustomMetric("cache_hits", MetricType.COUNTER, "Cache hits", ["cache_type"]),
            CustomMetric("cache_misses", MetricType.COUNTER, "Cache misses", ["cache_type"]),
            CustomMetric("error_count", MetricType.COUNTER, "Error count", ["error_type", "component"]),
        ]
        
        for metric in builtin_metrics:
            try:
                self.registry.register(metric)
            except ValueError:
                pass  # Already registered
                
    def start(self) -> None:
        """Start the metrics collection system"""
        if self._running:
            return
            
        self._running = True
        
        # Start flush thread
        self._flush_thread = threading.Thread(
            target=self._flush_worker,
            name="metrics-flush",
            daemon=True
        )
        self._flush_thread.start()
        
        # Start system metrics collection if enabled
        if self.enable_system_metrics:
            self._executor.submit(self._collect_system_metrics)
            
    def stop(self) -> None:
        """Stop the metrics collection system"""
        self._running = False
        
        if self._flush_thread:
            self._flush_thread.join(timeout=5.0)
            
        self._executor.shutdown(wait=True)
        
        # Final flush
        self._flush_metrics()
        
    def record(self, name: str, value: Union[int, float], labels: Dict[str, str] = None) -> None:
        """Record a metric value"""
        metric_def = self.registry.get_metric(name)
        if not metric_def:
            # Auto-register as gauge metric
            metric_def = CustomMetric(name, MetricType.GAUGE, f"Auto-registered metric: {name}")
            self.registry.register(metric_def)
            
        metric_value = metric_def.create_value(value, labels or {})
        
        with self._lock:
            self._metrics_buffer.append(metric_value)
            self._update_aggregation(metric_value)
            
    def increment(self, name: str, value: Union[int, float] = 1, labels: Dict[str, str] = None) -> None:
        """Increment a counter metric"""
        current = self.get_current_value(name, labels)
        self.record(name, current + value, labels)
        
    def timer(self, name: str, labels: Dict[str, str] = None):
        """Context manager for timing operations"""
        return TimerContext(self, name, labels or {})
        
    def get_current_value(self, name: str, labels: Dict[str, str] = None) -> float:
        """Get current aggregated value for a metric"""
        labels = labels or {}
        label_key = self._make_label_key(labels)
        
        with self._lock:
            metric_data = self._aggregated_metrics.get(name, {})
            return metric_data.get(label_key, {}).get("value", 0.0)
            
    def get_all_metrics(self) -> List[MetricValue]:
        """Get all current metric values"""
        with self._lock:
            metrics = []
            for name, label_data in self._aggregated_metrics.items():
                for label_key, data in label_data.items():
                    metrics.append(MetricValue(
                        name=name,
                        value=data["value"],
                        labels=data["labels"],
                        timestamp=data["timestamp"]
                    ))
            return metrics
            
    def add_export_callback(self, callback: Callable[[List[MetricValue]], None]) -> None:
        """Add a callback for metric export"""
        self._export_callbacks.append(callback)
        
    def _update_aggregation(self, metric: MetricValue) -> None:
        """Update aggregated metrics storage"""
        label_key = self._make_label_key(metric.labels)
        
        if metric.name not in self._aggregated_metrics:
            self._aggregated_metrics[metric.name] = {}
            
        if label_key not in self._aggregated_metrics[metric.name]:
            self._aggregated_metrics[metric.name][label_key] = {
                "value": metric.value,
                "labels": metric.labels,
                "timestamp": metric.timestamp,
                "count": 1,
                "sum": metric.value,
                "min": metric.value,
                "max": metric.value
            }
        else:
            data = self._aggregated_metrics[metric.name][label_key]
            
            # Update based on metric type
            metric_def = self.registry.get_metric(metric.name)
            if metric_def:
                if metric_def.metric_type == MetricType.COUNTER:
                    data["value"] = metric.value  # Counters are absolute
                elif metric_def.metric_type == MetricType.GAUGE:
                    data["value"] = metric.value  # Gauges are absolute
                elif metric_def.metric_type in [MetricType.HISTOGRAM, MetricType.TIMER]:
                    # Update statistical aggregations
                    data["count"] += 1
                    data["sum"] += metric.value
                    data["min"] = min(data["min"], metric.value)
                    data["max"] = max(data["max"], metric.value)
                    data["value"] = data["sum"] / data["count"]  # Average
                    
            data["timestamp"] = metric.timestamp
            
    def _make_label_key(self, labels: Dict[str, str]) -> str:
        """Create a string key from labels for aggregation"""
        if not labels:
            return "__default__"
        return "|".join(f"{k}={v}" for k, v in sorted(labels.items()))
        
    def _flush_worker(self) -> None:
        """Background worker for periodic metric flushing"""
        while self._running:
            time.sleep(self.flush_interval)
            if self._running:
                self._flush_metrics()
                
    def _flush_metrics(self) -> None:
        """Flush metrics to export callbacks"""
        if not self._export_callbacks:
            return
            
        metrics = self.get_all_metrics()
        if not metrics:
            return
            
        for callback in self._export_callbacks:
            try:
                callback(metrics)
            except Exception as e:
                # Log error but continue with other callbacks
                print(f"Error in metrics export callback: {e}")
                
    def _collect_system_metrics(self) -> None:
        """Collect system-level metrics"""
        if not HAS_PSUTIL:
            print("⚠️ System metrics collection skipped - psutil not available")
            return
            
        while self._running:
            try:
                # CPU metrics
                if HAS_PSUTIL:
                    cpu_percent = psutil.cpu_percent(interval=1)
                    self.record("system_cpu_percent", cpu_percent)
                
                    # Memory metrics
                    memory = psutil.virtual_memory()
                    self.record("system_memory_percent", memory.percent)
                
                    # Disk metrics
                    for partition in psutil.disk_partitions():
                        try:
                            usage = psutil.disk_usage(partition.mountpoint)
                            self.record("system_disk_percent", 
                                      (usage.used / usage.total) * 100,
                                      {"mount_point": partition.mountpoint})
                        except (PermissionError, FileNotFoundError):
                            continue
                        
                    # Network metrics
                    net_io = psutil.net_io_counters(pernic=True)
                    for interface, stats in net_io.items():
                        self.record("system_network_bytes", stats.bytes_sent, 
                                  {"direction": "sent", "interface": interface})
                        self.record("system_network_bytes", stats.bytes_recv,
                                  {"direction": "received", "interface": interface})
                              
            except Exception as e:
                print(f"Error collecting system metrics: {e}")
                
            time.sleep(30)  # Collect every 30 seconds


class TimerContext:
    """Context manager for timing operations"""
    
    def __init__(self, collector: MetricsCollector, name: str, labels: Dict[str, str]):
        self.collector = collector
        self.name = name
        self.labels = labels
        self.start_time: Optional[float] = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time
            self.collector.record(self.name, duration, self.labels)