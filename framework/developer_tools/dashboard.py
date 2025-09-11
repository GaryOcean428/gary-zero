"""
Developer Dashboard Module

Provides web-based dashboards for development, debugging, and monitoring
with real-time visualizations and interactive controls.
"""

import asyncio
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import logging

from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI, WebSocket, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

try:
    import plotly
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.utils import PlotlyJSONEncoder
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from .inspector import RuntimeInspector, inspect_framework
from .profiler import PerformanceProfiler, SystemStats
from .debugger import AdvancedDebugger


@dataclass
class DashboardMetric:
    """Dashboard metric data point"""
    name: str
    value: Union[float, int, str]
    unit: str
    timestamp: datetime
    category: str
    severity: str = "info"  # info, warning, error, success


@dataclass
class DashboardAlert:
    """Dashboard alert"""
    id: str
    title: str
    message: str
    severity: str  # info, warning, error
    timestamp: datetime
    resolved: bool = False


class MetricsCollector:
    """Collects and manages dashboard metrics"""
    
    def __init__(self, max_history: int = 1000):
        self._metrics: Dict[str, List[DashboardMetric]] = {}
        self._max_history = max_history
        self._lock = threading.Lock()
        self._collecting = False
        self._collection_thread = None
    
    def start_collection(self, interval: float = 1.0):
        """Start metrics collection"""
        if self._collecting:
            return
        
        self._collecting = True
        self._collection_thread = threading.Thread(
            target=self._collect_loop,
            args=(interval,),
            daemon=True
        )
        self._collection_thread.start()
        logger.info("Started metrics collection")
    
    def stop_collection(self):
        """Stop metrics collection"""
        self._collecting = False
        if self._collection_thread:
            self._collection_thread.join(timeout=5)
        logger.info("Stopped metrics collection")
    
    def add_metric(self, metric: DashboardMetric):
        """Add a metric data point"""
        with self._lock:
            if metric.name not in self._metrics:
                self._metrics[metric.name] = []
            
            self._metrics[metric.name].append(metric)
            
            # Trim history
            if len(self._metrics[metric.name]) > self._max_history:
                self._metrics[metric.name] = self._metrics[metric.name][-self._max_history:]
    
    def get_metrics(self, name: Optional[str] = None, limit: Optional[int] = None) -> Dict[str, List[DashboardMetric]]:
        """Get metrics data"""
        with self._lock:
            if name:
                metrics = {name: self._metrics.get(name, [])}
            else:
                metrics = dict(self._metrics)
            
            if limit:
                for key in metrics:
                    metrics[key] = metrics[key][-limit:]
            
            return metrics
    
    def get_latest_metrics(self) -> Dict[str, DashboardMetric]:
        """Get latest value for each metric"""
        with self._lock:
            latest = {}
            for name, values in self._metrics.items():
                if values:
                    latest[name] = values[-1]
            return latest
    
    def _collect_loop(self, interval: float):
        """Main collection loop"""
        try:
            import psutil
            
            while self._collecting:
                try:
                    # System metrics
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    
                    now = datetime.now()
                    
                    # Add system metrics
                    self.add_metric(DashboardMetric(
                        name="cpu_percent",
                        value=cpu_percent,
                        unit="%",
                        timestamp=now,
                        category="system",
                        severity="info" if cpu_percent < 80 else "warning" if cpu_percent < 95 else "error"
                    ))
                    
                    self.add_metric(DashboardMetric(
                        name="memory_percent",
                        value=memory.percent,
                        unit="%",
                        timestamp=now,
                        category="system",
                        severity="info" if memory.percent < 80 else "warning" if memory.percent < 95 else "error"
                    ))
                    
                    self.add_metric(DashboardMetric(
                        name="disk_percent",
                        value=disk.percent,
                        unit="%",
                        timestamp=now,
                        category="system",
                        severity="info" if disk.percent < 80 else "warning" if disk.percent < 95 else "error"
                    ))
                    
                    # Framework metrics
                    try:
                        framework_info = inspect_framework()
                        if framework_info:
                            self.add_metric(DashboardMetric(
                                name="framework_modules",
                                value=framework_info.get('total_modules', 0),
                                unit="count",
                                timestamp=now,
                                category="framework"
                            ))
                    except:
                        pass
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"Error in metrics collection: {e}")
                    time.sleep(interval)
                    
        except ImportError:
            logger.warning("psutil not available, limited metrics collection")
        except Exception as e:
            logger.error(f"Metrics collection error: {e}")


class AlertManager:
    """Manages dashboard alerts"""
    
    def __init__(self, max_alerts: int = 100):
        self._alerts: List[DashboardAlert] = []
        self._max_alerts = max_alerts
        self._lock = threading.Lock()
        self._next_id = 1
    
    def add_alert(self, title: str, message: str, severity: str = "info") -> str:
        """Add a new alert"""
        with self._lock:
            alert_id = f"alert_{self._next_id}"
            self._next_id += 1
            
            alert = DashboardAlert(
                id=alert_id,
                title=title,
                message=message,
                severity=severity,
                timestamp=datetime.now()
            )
            
            self._alerts.append(alert)
            
            # Trim alerts
            if len(self._alerts) > self._max_alerts:
                self._alerts = self._alerts[-self._max_alerts:]
            
            logger.info(f"Added alert: {title} ({severity})")
            return alert_id
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        with self._lock:
            for alert in self._alerts:
                if alert.id == alert_id:
                    alert.resolved = True
                    return True
            return False
    
    def get_alerts(self, resolved: Optional[bool] = None) -> List[DashboardAlert]:
        """Get alerts"""
        with self._lock:
            if resolved is None:
                return list(self._alerts)
            else:
                return [alert for alert in self._alerts if alert.resolved == resolved]
    
    def clear_resolved_alerts(self):
        """Clear resolved alerts"""
        with self._lock:
            self._alerts = [alert for alert in self._alerts if not alert.resolved]


class DashboardWebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self._connections: List[Any] = []  # Use Any instead of WebSocket when not available
        self._lock = None
        if HAS_FASTAPI:
            import asyncio
            self._lock = asyncio.Lock()
    
    async def connect(self, websocket):
        """Add a WebSocket connection"""
        if not HAS_FASTAPI:
            return
            
        await websocket.accept()
        if self._lock:
            async with self._lock:
                self._connections.append(websocket)
                logger.info(f"WebSocket connected. Total connections: {len(self._connections)}")
    
    async def disconnect(self, websocket):
        """Remove a WebSocket connection"""
        if not HAS_FASTAPI or not self._lock:
            return
            
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)
                logger.info(f"WebSocket disconnected. Total connections: {len(self._connections)}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connections"""
        if not HAS_FASTAPI or not self._connections or not self._lock:
            return
        
        async with self._lock:
            disconnected = []
            for connection in self._connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send WebSocket message: {e}")
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self._connections.remove(connection)


class DeveloperDashboard:
    """Main developer dashboard with comprehensive development tools"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        if not HAS_FASTAPI:
            raise ImportError("FastAPI required for dashboard. Install with: pip install fastapi uvicorn")
        
        self.host = host
        self.port = port
        self.app = FastAPI(title="Gary-Zero Developer Dashboard")
        self._metrics_collector = MetricsCollector()
        self._alert_manager = AlertManager()
        self._websocket_manager = DashboardWebSocketManager()
        self._runtime_inspector = RuntimeInspector()
        self._profiler = PerformanceProfiler()
        self._debugger = AdvancedDebugger()
        self._running = False
        
        self._setup_routes()
        self._setup_static_files()
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        if not HAS_FASTAPI:
            logger.warning("FastAPI not available, dashboard routes disabled")
            return
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home(request):
            """Main dashboard page"""
            return self._render_dashboard_template("dashboard.html", request)
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            """Get metrics data"""
            metrics = self._metrics_collector.get_metrics()
            
            # Convert to JSON-serializable format
            serializable_metrics = {}
            for name, metric_list in metrics.items():
                serializable_metrics[name] = [
                    {
                        'name': m.name,
                        'value': m.value,
                        'unit': m.unit,
                        'timestamp': m.timestamp.isoformat(),
                        'category': m.category,
                        'severity': m.severity
                    }
                    for m in metric_list
                ]
            
            return JSONResponse(serializable_metrics)
        
        @self.app.get("/api/metrics/latest")
        async def get_latest_metrics():
            """Get latest metrics"""
            latest = self._metrics_collector.get_latest_metrics()
            
            serializable_latest = {}
            for name, metric in latest.items():
                serializable_latest[name] = {
                    'name': metric.name,
                    'value': metric.value,
                    'unit': metric.unit,
                    'timestamp': metric.timestamp.isoformat(),
                    'category': metric.category,
                    'severity': metric.severity
                }
            
            return JSONResponse(serializable_latest)
        
        @self.app.get("/api/alerts")
        async def get_alerts():
            """Get alerts"""
            alerts = self._alert_manager.get_alerts()
            
            serializable_alerts = [
                {
                    'id': alert.id,
                    'title': alert.title,
                    'message': alert.message,
                    'severity': alert.severity,
                    'timestamp': alert.timestamp.isoformat(),
                    'resolved': alert.resolved
                }
                for alert in alerts
            ]
            
            return JSONResponse(serializable_alerts)
        
        @self.app.post("/api/alerts/{alert_id}/resolve")
        async def resolve_alert(alert_id: str):
            """Resolve an alert"""
            success = self._alert_manager.resolve_alert(alert_id)
            return JSONResponse({"success": success})
        
        @self.app.get("/api/framework/info")
        async def get_framework_info():
            """Get framework information"""
            try:
                info = inspect_framework()
                return JSONResponse(info)
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)
        
        @self.app.get("/api/runtime/snapshot")
        async def get_runtime_snapshot():
            """Get runtime snapshot"""
            try:
                snapshot = self._runtime_inspector.take_runtime_snapshot()
                
                # Make serializable
                serializable_snapshot = {}
                for key, value in snapshot.items():
                    if key == 'timestamp':
                        serializable_snapshot[key] = value
                    elif isinstance(value, dict):
                        serializable_snapshot[key] = value
                    else:
                        serializable_snapshot[key] = str(value)
                
                return JSONResponse(serializable_snapshot)
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket):
            """WebSocket endpoint for real-time updates"""
            await self._websocket_manager.connect(websocket)
            try:
                while True:
                    # Send periodic updates
                    await asyncio.sleep(2)
                    
                    # Send latest metrics
                    latest_metrics = self._metrics_collector.get_latest_metrics()
                    await self._websocket_manager.broadcast({
                        'type': 'metrics_update',
                        'data': {
                            name: {
                                'value': metric.value,
                                'unit': metric.unit,
                                'severity': metric.severity,
                                'timestamp': metric.timestamp.isoformat()
                            }
                            for name, metric in latest_metrics.items()
                        }
                    })
                    
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                await self._websocket_manager.disconnect(websocket)
    
    def _setup_static_files(self):
        """Setup static files and templates"""
        # In a real implementation, you would have actual static files
        # For now, we'll create a simple template in memory
        pass
    
    def _render_dashboard_template(self, template_name: str, request) -> str:
        """Render dashboard template"""
        # Simple HTML template for the dashboard
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Gary-Zero Developer Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 20px; margin: -20px -20px 20px -20px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; color: #3498db; }
        .metric-label { color: #7f8c8d; margin-top: 5px; }
        .alert { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .alert-info { background: #d1ecf1; border-left: 4px solid #bee5eb; }
        .alert-warning { background: #fff3cd; border-left: 4px solid #ffeaa7; }
        .alert-error { background: #f8d7da; border-left: 4px solid #f5c6cb; }
        .charts-container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .chart-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        #status { margin-left: 20px; color: #27ae60; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Gary-Zero Developer Dashboard</h1>
        <span id="status">● Connected</span>
    </div>
    
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-value" id="cpu-value">--</div>
            <div class="metric-label">CPU Usage (%)</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" id="memory-value">--</div>
            <div class="metric-label">Memory Usage (%)</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" id="disk-value">--</div>
            <div class="metric-label">Disk Usage (%)</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" id="modules-value">--</div>
            <div class="metric-label">Framework Modules</div>
        </div>
    </div>
    
    <div id="alerts-container">
        <h3>Alerts</h3>
        <div id="alerts"></div>
    </div>
    
    <div class="charts-container">
        <div class="chart-card">
            <h3>System Metrics</h3>
            <div id="system-chart"></div>
        </div>
        <div class="chart-card">
            <h3>Framework Info</h3>
            <div id="framework-chart"></div>
        </div>
    </div>
    
    <script>
        // WebSocket connection
        const ws = new WebSocket('ws://localhost:8080/ws');
        const status = document.getElementById('status');
        
        ws.onopen = function() {
            status.textContent = '● Connected';
            status.style.color = '#27ae60';
        };
        
        ws.onclose = function() {
            status.textContent = '● Disconnected';
            status.style.color = '#e74c3c';
        };
        
        ws.onmessage = function(event) {
            const message = JSON.parse(event.data);
            if (message.type === 'metrics_update') {
                updateMetrics(message.data);
            }
        };
        
        function updateMetrics(metrics) {
            if (metrics.cpu_percent) {
                document.getElementById('cpu-value').textContent = metrics.cpu_percent.value.toFixed(1);
            }
            if (metrics.memory_percent) {
                document.getElementById('memory-value').textContent = metrics.memory_percent.value.toFixed(1);
            }
            if (metrics.disk_percent) {
                document.getElementById('disk-value').textContent = metrics.disk_percent.value.toFixed(1);
            }
            if (metrics.framework_modules) {
                document.getElementById('modules-value').textContent = metrics.framework_modules.value;
            }
        }
        
        // Load initial data
        fetch('/api/metrics/latest')
            .then(response => response.json())
            .then(data => updateMetrics(data));
        
        // Load alerts
        fetch('/api/alerts')
            .then(response => response.json())
            .then(data => {
                const alertsContainer = document.getElementById('alerts');
                alertsContainer.innerHTML = '';
                
                data.forEach(alert => {
                    const alertDiv = document.createElement('div');
                    alertDiv.className = `alert alert-${alert.severity}`;
                    alertDiv.innerHTML = `
                        <strong>${alert.title}</strong>: ${alert.message}
                        <small style="float: right;">${new Date(alert.timestamp).toLocaleString()}</small>
                    `;
                    alertsContainer.appendChild(alertDiv);
                });
            });
        
        // Initialize charts
        const systemTrace = {
            x: [],
            y: [],
            type: 'scatter',
            mode: 'lines',
            name: 'CPU %'
        };
        
        Plotly.newPlot('system-chart', [systemTrace], {
            title: 'CPU Usage Over Time',
            xaxis: { title: 'Time' },
            yaxis: { title: 'Percentage' }
        });
        
        // Update charts periodically
        setInterval(() => {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    if (data.cpu_percent) {
                        const times = data.cpu_percent.map(m => new Date(m.timestamp));
                        const values = data.cpu_percent.map(m => m.value);
                        
                        Plotly.restyle('system-chart', {
                            x: [times],
                            y: [values]
                        });
                    }
                });
        }, 5000);
    </script>
</body>
</html>
"""
        return html_template
    
    def start(self, background: bool = False):
        """Start the dashboard server"""
        if self._running:
            logger.warning("Dashboard already running")
            return
        
        self._running = True
        self._metrics_collector.start_collection()
        
        # Add initial alerts
        self._alert_manager.add_alert(
            "Dashboard Started",
            "Gary-Zero Developer Dashboard is now running",
            "info"
        )
        
        logger.info(f"Starting dashboard at http://{self.host}:{self.port}")
        
        if background:
            # Run in background thread
            def run_server():
                uvicorn.run(self.app, host=self.host, port=self.port, log_level="warning")
            
            thread = threading.Thread(target=run_server, daemon=True)
            thread.start()
            time.sleep(2)  # Give server time to start
        else:
            # Run in foreground
            uvicorn.run(self.app, host=self.host, port=self.port)
    
    def stop(self):
        """Stop the dashboard server"""
        self._running = False
        self._metrics_collector.stop_collection()
        logger.info("Dashboard stopped")
    
    def add_custom_metric(self, name: str, value: Union[float, int], unit: str = "", category: str = "custom"):
        """Add a custom metric"""
        metric = DashboardMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            category=category
        )
        self._metrics_collector.add_metric(metric)
    
    def add_alert(self, title: str, message: str, severity: str = "info") -> str:
        """Add an alert"""
        return self._alert_manager.add_alert(title, message, severity)


class DebugDashboard:
    """Specialized dashboard for debugging"""
    
    def __init__(self, host: str = "localhost", port: int = 8081):
        self.host = host
        self.port = port
        self._debugger = AdvancedDebugger()
        self._sessions: Dict[str, Any] = {}
    
    def start_debug_session(self, name: str) -> str:
        """Start a debugging session"""
        session_id = self._debugger.start_session(name)
        self._sessions[session_id] = {
            'name': name,
            'start_time': datetime.now(),
            'breakpoints': [],
            'status': 'active'
        }
        return session_id
    
    def get_debug_sessions(self) -> Dict[str, Any]:
        """Get all debug sessions"""
        return self._sessions


class MetricsDashboard:
    """Specialized dashboard for metrics and monitoring"""
    
    def __init__(self, host: str = "localhost", port: int = 8082):
        self.host = host
        self.port = port
        self._profiler = PerformanceProfiler()
        self._metrics_history: List[SystemStats] = []
    
    def start_metrics_collection(self):
        """Start collecting metrics"""
        self._profiler.start_session(profile_system=True)
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        sessions = self._profiler.get_sessions()
        
        report = {
            'total_sessions': len(sessions),
            'performance_summary': {},
            'recommendations': []
        }
        
        for session in sessions:
            if session.profile_stats:
                analysis = self._profiler.analyze_performance(session.session_id)
                report['performance_summary'][session.session_id] = analysis
        
        return report


# Global dashboard instances
_developer_dashboard = None
_debug_dashboard = None
_metrics_dashboard = None

# Convenience functions
def start_developer_dashboard(host: str = "localhost", port: int = 8080, background: bool = True):
    """Start the developer dashboard"""
    global _developer_dashboard
    if not _developer_dashboard:
        _developer_dashboard = DeveloperDashboard(host, port)
    _developer_dashboard.start(background)
    return _developer_dashboard

def stop_developer_dashboard():
    """Stop the developer dashboard"""
    global _developer_dashboard
    if _developer_dashboard:
        _developer_dashboard.stop()

def add_dashboard_metric(name: str, value: Union[float, int], unit: str = "", category: str = "custom"):
    """Add metric to dashboard"""
    global _developer_dashboard
    if _developer_dashboard:
        _developer_dashboard.add_custom_metric(name, value, unit, category)

def add_dashboard_alert(title: str, message: str, severity: str = "info") -> Optional[str]:
    """Add alert to dashboard"""
    global _developer_dashboard
    if _developer_dashboard:
        return _developer_dashboard.add_alert(title, message, severity)
    return None