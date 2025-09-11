"""
Enterprise Monitoring and Alerting Framework.

Provides advanced monitoring capabilities with custom dashboards,
real-time alerting, and comprehensive metrics collection.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, asdict, field
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert lifecycle status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SILENCED = "silenced"


class MetricType(Enum):
    """Metric data types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class DashboardType(Enum):
    """Dashboard types."""
    OPERATIONAL = "operational"
    BUSINESS = "business"
    CUSTOM = "custom"
    SYSTEM = "system"


@dataclass
class MetricDefinition:
    """Metric definition with metadata."""
    name: str
    type: MetricType
    description: str
    labels: List[str] = field(default_factory=list)
    unit: str = ""
    help_text: str = ""
    
    def __post_init__(self):
        if not self.help_text:
            self.help_text = self.description


@dataclass
class MetricSample:
    """Individual metric sample."""
    metric_name: str
    value: Union[int, float]
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    description: str
    metric_name: str
    condition: str  # e.g., "> 0.95", "< 100", "== 0"
    threshold_value: Union[int, float]
    severity: AlertSeverity
    duration: int = 60  # seconds
    labels: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Alert:
    """Active alert instance."""
    id: str
    rule_name: str
    metric_name: str
    current_value: Union[int, float]
    threshold_value: Union[int, float]
    severity: AlertSeverity
    status: AlertStatus
    message: str
    labels: Dict[str, str] = field(default_factory=dict)
    fired_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None


@dataclass
class DashboardWidget:
    """Dashboard widget configuration."""
    id: str
    title: str
    type: str  # chart, gauge, table, text
    metric_queries: List[str]
    config: Dict[str, Any] = field(default_factory=dict)
    position: Dict[str, int] = field(default_factory=dict)  # x, y, width, height


@dataclass
class Dashboard:
    """Dashboard configuration."""
    id: str
    name: str
    description: str
    type: DashboardType
    widgets: List[DashboardWidget] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "system"


class MetricStorage(ABC):
    """Abstract metric storage backend."""
    
    @abstractmethod
    async def store_metric(self, sample: MetricSample) -> bool:
        """Store a metric sample."""
        pass
    
    @abstractmethod
    async def query_metrics(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        labels: Optional[Dict[str, str]] = None,
        aggregation: Optional[str] = None
    ) -> List[MetricSample]:
        """Query metric samples."""
        pass
    
    @abstractmethod
    async def get_latest_value(
        self,
        metric_name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[MetricSample]:
        """Get the latest value for a metric."""
        pass


class InMemoryMetricStorage(MetricStorage):
    """In-memory metric storage for development and testing."""
    
    def __init__(self, max_samples: int = 10000):
        self._metrics: Dict[str, List[MetricSample]] = {}
        self.max_samples = max_samples
        self._lock = asyncio.Lock()
    
    async def store_metric(self, sample: MetricSample) -> bool:
        async with self._lock:
            if sample.metric_name not in self._metrics:
                self._metrics[sample.metric_name] = []
            
            self._metrics[sample.metric_name].append(sample)
            
            # Limit storage size
            if len(self._metrics[sample.metric_name]) > self.max_samples:
                self._metrics[sample.metric_name] = self._metrics[sample.metric_name][-self.max_samples:]
            
            return True
    
    async def query_metrics(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        labels: Optional[Dict[str, str]] = None,
        aggregation: Optional[str] = None
    ) -> List[MetricSample]:
        async with self._lock:
            samples = self._metrics.get(metric_name, [])
            
            # Filter by time range
            filtered_samples = [
                s for s in samples
                if start_time <= s.timestamp <= end_time
            ]
            
            # Filter by labels if provided
            if labels:
                filtered_samples = [
                    s for s in filtered_samples
                    if all(s.labels.get(k) == v for k, v in labels.items())
                ]
            
            # Apply aggregation if requested
            if aggregation and filtered_samples:
                return self._apply_aggregation(filtered_samples, aggregation)
            
            return filtered_samples
    
    async def get_latest_value(
        self,
        metric_name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[MetricSample]:
        async with self._lock:
            samples = self._metrics.get(metric_name, [])
            
            if not samples:
                return None
            
            # Filter by labels if provided
            if labels:
                samples = [
                    s for s in samples
                    if all(s.labels.get(k) == v for k, v in labels.items())
                ]
            
            return samples[-1] if samples else None
    
    def _apply_aggregation(self, samples: List[MetricSample], aggregation: str) -> List[MetricSample]:
        """Apply aggregation to samples."""
        if not samples:
            return []
        
        values = [s.value for s in samples]
        
        if aggregation == "avg":
            result_value = sum(values) / len(values)
        elif aggregation == "sum":
            result_value = sum(values)
        elif aggregation == "min":
            result_value = min(values)
        elif aggregation == "max":
            result_value = max(values)
        elif aggregation == "count":
            result_value = len(values)
        else:
            return samples  # No aggregation
        
        # Return single aggregated sample
        return [MetricSample(
            metric_name=samples[0].metric_name,
            value=result_value,
            labels=samples[0].labels,
            timestamp=samples[-1].timestamp
        )]


class AlertManager:
    """
    Alert manager with rule evaluation and notification capabilities.
    """
    
    def __init__(
        self,
        metric_storage: MetricStorage,
        notification_backends: Optional[List[Callable]] = None
    ):
        self.metric_storage = metric_storage
        self.notification_backends = notification_backends or []
        
        # Alert state
        self._alert_rules: Dict[str, AlertRule] = {}
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: List[Alert] = []
        
        # Evaluation task
        self._evaluation_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        logger.info("AlertManager initialized")
    
    async def start(self):
        """Start alert evaluation loop."""
        if self._evaluation_task is None:
            self._evaluation_task = asyncio.create_task(self._evaluation_loop())
            logger.info("Started alert evaluation")
    
    async def stop(self):
        """Stop alert evaluation loop."""
        if self._evaluation_task:
            self._shutdown_event.set()
            await self._evaluation_task
            self._evaluation_task = None
            logger.info("Stopped alert evaluation")
    
    async def add_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self._alert_rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    async def remove_rule(self, rule_name: str) -> bool:
        """Remove an alert rule."""
        if rule_name in self._alert_rules:
            del self._alert_rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")
            return True
        return False
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an active alert."""
        if alert_id in self._active_alerts:
            alert = self._active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.now(timezone.utc)
            alert.acknowledged_by = acknowledged_by
            
            logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
            return True
        
        return False
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Manually resolve an alert."""
        if alert_id in self._active_alerts:
            alert = self._active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now(timezone.utc)
            
            # Move to history
            self._alert_history.append(alert)
            del self._active_alerts[alert_id]
            
            logger.info(f"Alert resolved: {alert_id}")
            return True
        
        return False
    
    async def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        status: Optional[AlertStatus] = None
    ) -> List[Alert]:
        """Get active alerts with optional filtering."""
        alerts = list(self._active_alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if status:
            alerts = [a for a in alerts if a.status == status]
        
        return sorted(alerts, key=lambda a: a.fired_at, reverse=True)
    
    async def get_alert_history(
        self,
        limit: int = 100,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """Get alert history."""
        history = self._alert_history
        
        if severity:
            history = [a for a in history if a.severity == severity]
        
        return sorted(history, key=lambda a: a.fired_at, reverse=True)[:limit]
    
    async def _evaluation_loop(self):
        """Background loop for evaluating alert rules."""
        while not self._shutdown_event.is_set():
            try:
                await self._evaluate_rules()
                await asyncio.sleep(30)  # Evaluate every 30 seconds
            except Exception as e:
                logger.error(f"Error in alert evaluation loop: {e}")
                await asyncio.sleep(60)  # Back off on error
    
    async def _evaluate_rules(self):
        """Evaluate all alert rules."""
        for rule_name, rule in self._alert_rules.items():
            if not rule.enabled:
                continue
            
            try:
                await self._evaluate_rule(rule)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule_name}: {e}")
    
    async def _evaluate_rule(self, rule: AlertRule):
        """Evaluate a single alert rule."""
        # Get latest metric value
        latest_sample = await self.metric_storage.get_latest_value(rule.metric_name)
        
        if not latest_sample:
            return
        
        # Check if condition is met
        if self._evaluate_condition(latest_sample.value, rule.condition, rule.threshold_value):
            # Condition met - fire alert if not already active
            alert_id = f"{rule.name}:{rule.metric_name}"
            
            if alert_id not in self._active_alerts:
                alert = Alert(
                    id=alert_id,
                    rule_name=rule.name,
                    metric_name=rule.metric_name,
                    current_value=latest_sample.value,
                    threshold_value=rule.threshold_value,
                    severity=rule.severity,
                    status=AlertStatus.ACTIVE,
                    message=f"{rule.description} - Current: {latest_sample.value}, Threshold: {rule.threshold_value}",
                    labels=rule.labels
                )
                
                self._active_alerts[alert_id] = alert
                await self._send_notifications(alert)
                logger.warning(f"Alert fired: {alert.message}")
        
        else:
            # Condition not met - resolve alert if active
            alert_id = f"{rule.name}:{rule.metric_name}"
            
            if alert_id in self._active_alerts:
                alert = self._active_alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.now(timezone.utc)
                
                # Move to history
                self._alert_history.append(alert)
                del self._active_alerts[alert_id]
                
                logger.info(f"Alert auto-resolved: {alert_id}")
    
    def _evaluate_condition(
        self,
        current_value: Union[int, float],
        condition: str,
        threshold_value: Union[int, float]
    ) -> bool:
        """Evaluate alert condition."""
        if condition == ">":
            return current_value > threshold_value
        elif condition == ">=":
            return current_value >= threshold_value
        elif condition == "<":
            return current_value < threshold_value
        elif condition == "<=":
            return current_value <= threshold_value
        elif condition == "==":
            return current_value == threshold_value
        elif condition == "!=":
            return current_value != threshold_value
        
        return False
    
    async def _send_notifications(self, alert: Alert):
        """Send alert notifications to configured backends."""
        for backend in self.notification_backends:
            try:
                if asyncio.iscoroutinefunction(backend):
                    await backend(alert)
                else:
                    backend(alert)
            except Exception as e:
                logger.error(f"Error sending alert notification: {e}")


class EnterpriseMonitor:
    """
    Enterprise monitoring system with metrics collection, alerting, and dashboards.
    
    Features:
    - Real-time metric collection and storage
    - Custom dashboard creation and management
    - Alert rule management with multiple severity levels
    - Integration with existing observability stack
    - Performance monitoring and trending
    """
    
    def __init__(
        self,
        metric_storage: Optional[MetricStorage] = None,
        alert_manager: Optional[AlertManager] = None
    ):
        self.metric_storage = metric_storage or InMemoryMetricStorage()
        self.alert_manager = alert_manager or AlertManager(self.metric_storage)
        
        # Metric definitions
        self._metric_definitions: Dict[str, MetricDefinition] = {}
        
        # Dashboard management
        self._dashboards: Dict[str, Dashboard] = {}
        
        # Built-in metrics
        self._setup_builtin_metrics()
        
        logger.info("EnterpriseMonitor initialized")
    
    async def start(self):
        """Start monitoring services."""
        await self.alert_manager.start()
        logger.info("Enterprise monitoring started")
    
    async def stop(self):
        """Stop monitoring services."""
        await self.alert_manager.stop()
        logger.info("Enterprise monitoring stopped")
    
    def _setup_builtin_metrics(self):
        """Setup built-in metric definitions."""
        builtin_metrics = [
            MetricDefinition(
                name="http_requests_total",
                type=MetricType.COUNTER,
                description="Total HTTP requests",
                labels=["method", "status", "endpoint"],
                unit="requests"
            ),
            MetricDefinition(
                name="http_request_duration",
                type=MetricType.HISTOGRAM,
                description="HTTP request duration",
                labels=["method", "endpoint"],
                unit="seconds"
            ),
            MetricDefinition(
                name="system_cpu_usage",
                type=MetricType.GAUGE,
                description="System CPU usage percentage",
                unit="percent"
            ),
            MetricDefinition(
                name="system_memory_usage",
                type=MetricType.GAUGE,
                description="System memory usage percentage",
                unit="percent"
            ),
            MetricDefinition(
                name="ai_model_inference_time",
                type=MetricType.HISTOGRAM,
                description="AI model inference time",
                labels=["model", "version"],
                unit="seconds"
            ),
            MetricDefinition(
                name="feature_flag_evaluations",
                type=MetricType.COUNTER,
                description="Feature flag evaluations",
                labels=["flag", "variation"],
                unit="evaluations"
            ),
            MetricDefinition(
                name="deployment_status",
                type=MetricType.GAUGE,
                description="Deployment status (1=success, 0=failure)",
                labels=["environment", "version"],
                unit="status"
            )
        ]
        
        for metric in builtin_metrics:
            self._metric_definitions[metric.name] = metric
    
    async def register_metric(self, metric_def: MetricDefinition):
        """Register a custom metric definition."""
        self._metric_definitions[metric_def.name] = metric_def
        logger.info(f"Registered metric: {metric_def.name}")
    
    async def record_metric(
        self,
        metric_name: str,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Record a metric value."""
        if metric_name not in self._metric_definitions:
            logger.warning(f"Unknown metric: {metric_name}")
            return False
        
        sample = MetricSample(
            metric_name=metric_name,
            value=value,
            labels=labels or {},
            timestamp=timestamp or datetime.now(timezone.utc)
        )
        
        return await self.metric_storage.store_metric(sample)
    
    async def query_metrics(
        self,
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None,
        aggregation: Optional[str] = None,
        duration_hours: int = 1
    ) -> List[MetricSample]:
        """Query metric samples."""
        if not end_time:
            end_time = datetime.now(timezone.utc)
        
        if not start_time:
            start_time = end_time - timedelta(hours=duration_hours)
        
        return await self.metric_storage.query_metrics(
            metric_name, start_time, end_time, labels, aggregation
        )
    
    async def get_metric_summary(
        self,
        metric_name: str,
        duration_hours: int = 24
    ) -> Dict[str, Any]:
        """Get metric summary statistics."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=duration_hours)
        
        samples = await self.metric_storage.query_metrics(metric_name, start_time, end_time)
        
        if not samples:
            return {"metric_name": metric_name, "samples": 0}
        
        values = [s.value for s in samples]
        
        return {
            "metric_name": metric_name,
            "samples": len(samples),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1],
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    
    async def create_dashboard(
        self,
        name: str,
        description: str,
        dashboard_type: DashboardType = DashboardType.CUSTOM,
        tags: Optional[List[str]] = None,
        created_by: str = "system"
    ) -> Dashboard:
        """Create a new dashboard."""
        dashboard_id = f"dashboard_{int(time.time())}"
        
        dashboard = Dashboard(
            id=dashboard_id,
            name=name,
            description=description,
            type=dashboard_type,
            tags=tags or [],
            created_by=created_by
        )
        
        self._dashboards[dashboard_id] = dashboard
        logger.info(f"Created dashboard: {name}")
        
        return dashboard
    
    async def add_widget_to_dashboard(
        self,
        dashboard_id: str,
        title: str,
        widget_type: str,
        metric_queries: List[str],
        config: Optional[Dict[str, Any]] = None,
        position: Optional[Dict[str, int]] = None
    ) -> bool:
        """Add a widget to a dashboard."""
        if dashboard_id not in self._dashboards:
            return False
        
        widget_id = f"widget_{int(time.time())}"
        
        widget = DashboardWidget(
            id=widget_id,
            title=title,
            type=widget_type,
            metric_queries=metric_queries,
            config=config or {},
            position=position or {}
        )
        
        dashboard = self._dashboards[dashboard_id]
        dashboard.widgets.append(widget)
        dashboard.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Added widget '{title}' to dashboard '{dashboard.name}'")
        return True
    
    async def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get dashboard by ID."""
        return self._dashboards.get(dashboard_id)
    
    async def list_dashboards(
        self,
        dashboard_type: Optional[DashboardType] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dashboard]:
        """List dashboards with optional filtering."""
        dashboards = list(self._dashboards.values())
        
        if dashboard_type:
            dashboards = [d for d in dashboards if d.type == dashboard_type]
        
        if tags:
            dashboards = [d for d in dashboards if any(tag in d.tags for tag in tags)]
        
        return sorted(dashboards, key=lambda d: d.created_at, reverse=True)
    
    async def render_dashboard_data(self, dashboard_id: str) -> Dict[str, Any]:
        """Render dashboard with current metric data."""
        dashboard = self._dashboards.get(dashboard_id)
        if not dashboard:
            return {}
        
        dashboard_data = asdict(dashboard)
        
        # Add current data for each widget
        for widget in dashboard_data["widgets"]:
            widget["data"] = []
            
            for query in widget["metric_queries"]:
                try:
                    # Parse simple metric query (metric_name or metric_name{labels})
                    metric_name = query.split("{")[0]
                    labels = {}
                    
                    if "{" in query:
                        label_part = query.split("{")[1].split("}")[0]
                        for label_pair in label_part.split(","):
                            if "=" in label_pair:
                                key, value = label_pair.split("=", 1)
                                labels[key.strip()] = value.strip().strip('"')
                    
                    # Get recent data
                    samples = await self.query_metrics(
                        metric_name,
                        labels=labels if labels else None,
                        duration_hours=1
                    )
                    
                    widget["data"].append({
                        "query": query,
                        "samples": [asdict(s) for s in samples[-100:]]  # Last 100 samples
                    })
                    
                except Exception as e:
                    logger.error(f"Error rendering widget data for query '{query}': {e}")
                    widget["data"].append({
                        "query": query,
                        "error": str(e),
                        "samples": []
                    })
        
        return dashboard_data
    
    async def create_operational_dashboard(self) -> Dashboard:
        """Create a pre-configured operational dashboard."""
        dashboard = await self.create_dashboard(
            name="Operational Dashboard",
            description="Key operational metrics for Gary-Zero",
            dashboard_type=DashboardType.OPERATIONAL,
            tags=["operations", "system"]
        )
        
        # Add system widgets
        await self.add_widget_to_dashboard(
            dashboard.id,
            "System CPU Usage",
            "gauge",
            ["system_cpu_usage"],
            {"threshold_warning": 70, "threshold_critical": 90},
            {"x": 0, "y": 0, "width": 6, "height": 4}
        )
        
        await self.add_widget_to_dashboard(
            dashboard.id,
            "System Memory Usage",
            "gauge",
            ["system_memory_usage"],
            {"threshold_warning": 80, "threshold_critical": 95},
            {"x": 6, "y": 0, "width": 6, "height": 4}
        )
        
        await self.add_widget_to_dashboard(
            dashboard.id,
            "HTTP Request Rate",
            "line_chart",
            ["http_requests_total"],
            {"time_range": "1h"},
            {"x": 0, "y": 4, "width": 12, "height": 6}
        )
        
        await self.add_widget_to_dashboard(
            dashboard.id,
            "AI Model Performance",
            "line_chart",
            ["ai_model_inference_time"],
            {"time_range": "1h", "aggregation": "avg"},
            {"x": 0, "y": 10, "width": 12, "height": 6}
        )
        
        return dashboard
    
    async def setup_default_alerts(self):
        """Setup default alert rules."""
        default_rules = [
            AlertRule(
                name="high_cpu_usage",
                description="High CPU usage detected",
                metric_name="system_cpu_usage",
                condition=">",
                threshold_value=90.0,
                severity=AlertSeverity.HIGH,
                duration=300
            ),
            AlertRule(
                name="high_memory_usage",
                description="High memory usage detected",
                metric_name="system_memory_usage",
                condition=">",
                threshold_value=95.0,
                severity=AlertSeverity.CRITICAL,
                duration=180
            ),
            AlertRule(
                name="slow_ai_inference",
                description="Slow AI model inference detected",
                metric_name="ai_model_inference_time",
                condition=">",
                threshold_value=5.0,
                severity=AlertSeverity.MEDIUM,
                duration=120
            ),
            AlertRule(
                name="deployment_failure",
                description="Deployment failure detected",
                metric_name="deployment_status",
                condition="==",
                threshold_value=0.0,
                severity=AlertSeverity.CRITICAL,
                duration=60
            )
        ]
        
        for rule in default_rules:
            await self.alert_manager.add_rule(rule)
        
        logger.info("Setup default alert rules")
    
    async def get_monitoring_health(self) -> Dict[str, Any]:
        """Get overall monitoring system health."""
        active_alerts = await self.alert_manager.get_active_alerts()
        critical_alerts = [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]
        
        # Get some key metrics
        metrics_health = {}
        for metric_name in ["system_cpu_usage", "system_memory_usage"]:
            latest = await self.metric_storage.get_latest_value(metric_name)
            if latest:
                metrics_health[metric_name] = {
                    "value": latest.value,
                    "timestamp": latest.timestamp.isoformat()
                }
        
        return {
            "status": "critical" if critical_alerts else "healthy",
            "active_alerts": len(active_alerts),
            "critical_alerts": len(critical_alerts),
            "registered_metrics": len(self._metric_definitions),
            "dashboards": len(self._dashboards),
            "metrics_health": metrics_health,
            "last_check": datetime.now(timezone.utc).isoformat()
        }


# Convenience functions for common operations
async def record_http_request(
    monitor: EnterpriseMonitor,
    method: str,
    endpoint: str,
    status_code: int,
    duration: float
):
    """Record HTTP request metrics."""
    await monitor.record_metric(
        "http_requests_total",
        1,
        {"method": method, "status": str(status_code), "endpoint": endpoint}
    )
    
    await monitor.record_metric(
        "http_request_duration",
        duration,
        {"method": method, "endpoint": endpoint}
    )


async def record_ai_inference(
    monitor: EnterpriseMonitor,
    model_name: str,
    model_version: str,
    inference_time: float
):
    """Record AI model inference metrics."""
    await monitor.record_metric(
        "ai_model_inference_time",
        inference_time,
        {"model": model_name, "version": model_version}
    )


async def record_feature_flag_evaluation(
    monitor: EnterpriseMonitor,
    flag_key: str,
    variation: str
):
    """Record feature flag evaluation metrics."""
    await monitor.record_metric(
        "feature_flag_evaluations",
        1,
        {"flag": flag_key, "variation": variation}
    )