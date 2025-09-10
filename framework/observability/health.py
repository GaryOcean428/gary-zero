"""
Advanced Health Monitoring and Alerting System

Provides comprehensive health monitoring with:
- Multi-level health checks (system, application, dependencies)
- Automatic health status aggregation
- Alerting and notification capabilities
- Health history and trend analysis
- Integration with monitoring systems
"""

import time
import threading
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Union, Awaitable
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

# Optional dependency handling
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

try:
    from sqlalchemy import create_engine, text
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckType(Enum):
    """Types of health checks"""
    SYSTEM = "system"
    DATABASE = "database"
    CACHE = "cache"
    EXTERNAL_API = "external_api"
    CUSTOM = "custom"


@dataclass
class HealthCheckResult:
    """Result of a health check execution"""
    name: str
    status: HealthStatus
    timestamp: float = field(default_factory=time.time)
    duration: float = 0.0
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    check_type: HealthCheckType = HealthCheckType.CUSTOM
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "status": self.status.value,
            "timestamp": self.timestamp,
            "duration": self.duration,
            "message": self.message,
            "details": self.details,
            "check_type": self.check_type.value
        }


@dataclass
class HealthCheck:
    """Configuration for a health check"""
    name: str
    check_function: Callable[[], Union[HealthCheckResult, Awaitable[HealthCheckResult]]]
    interval: float = 30.0  # seconds
    timeout: float = 10.0  # seconds
    check_type: HealthCheckType = HealthCheckType.CUSTOM
    enabled: bool = True
    critical: bool = False  # If true, failure affects overall health
    retry_count: int = 3
    retry_delay: float = 1.0
    
    def __post_init__(self):
        if self.timeout >= self.interval:
            raise ValueError("Timeout must be less than interval")


class HealthMonitor:
    """Advanced health monitoring system"""
    
    def __init__(self, 
                 check_interval: float = 30.0,
                 history_size: int = 1000,
                 alert_threshold: int = 3):  # Consecutive failures before alert
        self.check_interval = check_interval
        self.history_size = history_size
        self.alert_threshold = alert_threshold
        
        # Health checks registry
        self._checks: Dict[str, HealthCheck] = {}
        self._check_results: Dict[str, HealthCheckResult] = {}
        self._check_history: Dict[str, List[HealthCheckResult]] = {}
        self._consecutive_failures: Dict[str, int] = {}
        
        # Overall health
        self._overall_status = HealthStatus.UNKNOWN
        self._overall_message = "Monitoring not started"
        
        # Threading
        self._lock = threading.RLock()
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="health")
        
        # Alerting
        self._alert_callbacks: List[Callable[[str, HealthCheckResult], None]] = []
        
        # Initialize built-in health checks
        self._register_builtin_checks()
        
    def _register_builtin_checks(self):
        """Register built-in system health checks"""
        self.register_check(HealthCheck(
            name="system_cpu",
            check_function=self._check_system_cpu,
            check_type=HealthCheckType.SYSTEM,
            critical=True
        ))
        
        self.register_check(HealthCheck(
            name="system_memory",
            check_function=self._check_system_memory,
            check_type=HealthCheckType.SYSTEM,
            critical=True
        ))
        
        self.register_check(HealthCheck(
            name="system_disk",
            check_function=self._check_system_disk,
            check_type=HealthCheckType.SYSTEM,
            critical=True
        ))
        
    def register_check(self, health_check: HealthCheck) -> None:
        """Register a health check"""
        with self._lock:
            if health_check.name in self._checks:
                raise ValueError(f"Health check '{health_check.name}' already registered")
            self._checks[health_check.name] = health_check
            self._consecutive_failures[health_check.name] = 0
            
    def unregister_check(self, name: str) -> bool:
        """Unregister a health check"""
        with self._lock:
            removed = self._checks.pop(name, None) is not None
            if removed:
                self._check_results.pop(name, None)
                self._check_history.pop(name, None)
                self._consecutive_failures.pop(name, None)
            return removed
            
    def start(self) -> None:
        """Start the health monitoring system"""
        if self._running:
            return
            
        self._running = True
        self._overall_status = HealthStatus.HEALTHY
        self._overall_message = "Monitoring started"
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(
            target=self._monitor_worker,
            name="health-monitor",
            daemon=True
        )
        self._monitor_thread.start()
        
    def stop(self) -> None:
        """Stop the health monitoring system"""
        self._running = False
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
            
        self._executor.shutdown(wait=True)
        
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        with self._lock:
            healthy_count = sum(1 for result in self._check_results.values() 
                              if result.status == HealthStatus.HEALTHY)
            total_count = len(self._check_results)
            
            return {
                "status": self._overall_status.value,
                "message": self._overall_message,
                "timestamp": time.time(),
                "checks": {
                    "total": total_count,
                    "healthy": healthy_count,
                    "unhealthy": total_count - healthy_count
                },
                "details": {name: result.to_dict() for name, result in self._check_results.items()}
            }
            
    def get_check_status(self, name: str) -> Optional[HealthCheckResult]:
        """Get status of a specific health check"""
        with self._lock:
            return self._check_results.get(name)
            
    def get_check_history(self, name: str, limit: int = None) -> List[HealthCheckResult]:
        """Get history of a specific health check"""
        with self._lock:
            history = self._check_history.get(name, [])
            if limit:
                return history[-limit:]
            return list(history)
            
    def force_check(self, name: str) -> Optional[HealthCheckResult]:
        """Force execution of a specific health check"""
        check = self._checks.get(name)
        if not check or not check.enabled:
            return None
            
        return self._execute_check(check)
        
    def add_alert_callback(self, callback: Callable[[str, HealthCheckResult], None]) -> None:
        """Add an alert callback"""
        self._alert_callbacks.append(callback)
        
    def _monitor_worker(self) -> None:
        """Background worker for health monitoring"""
        while self._running:
            try:
                self._run_all_checks()
                self._update_overall_health()
            except Exception as e:
                print(f"Error in health monitor: {e}")
                
            time.sleep(self.check_interval)
            
    def _run_all_checks(self) -> None:
        """Execute all enabled health checks"""
        futures = []
        
        for check in self._checks.values():
            if check.enabled:
                future = self._executor.submit(self._execute_check, check)
                futures.append((check.name, future))
                
        # Collect results
        for name, future in futures:
            try:
                result = future.result(timeout=self._checks[name].timeout)
                self._process_check_result(name, result)
            except Exception as e:
                error_result = HealthCheckResult(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check execution failed: {str(e)}",
                    check_type=self._checks[name].check_type
                )
                self._process_check_result(name, error_result)
                
    def _execute_check(self, check: HealthCheck) -> HealthCheckResult:
        """Execute a single health check with retry logic"""
        last_exception = None
        
        for attempt in range(check.retry_count):
            try:
                start_time = time.time()
                
                # Execute check function
                if asyncio.iscoroutinefunction(check.check_function):
                    # Handle async function
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(check.check_function())
                    finally:
                        loop.close()
                else:
                    result = check.check_function()
                    
                result.duration = time.time() - start_time
                return result
                
            except Exception as e:
                last_exception = e
                if attempt < check.retry_count - 1:
                    time.sleep(check.retry_delay)
                    
        # All retries failed
        return HealthCheckResult(
            name=check.name,
            status=HealthStatus.UNHEALTHY,
            message=f"Check failed after {check.retry_count} attempts: {str(last_exception)}",
            check_type=check.check_type
        )
        
    def _process_check_result(self, name: str, result: HealthCheckResult) -> None:
        """Process and store check result"""
        with self._lock:
            # Store current result
            self._check_results[name] = result
            
            # Update history
            if name not in self._check_history:
                self._check_history[name] = []
            self._check_history[name].append(result)
            
            # Limit history size
            if len(self._check_history[name]) > self.history_size:
                self._check_history[name] = self._check_history[name][-self.history_size:]
                
            # Track consecutive failures
            if result.status == HealthStatus.UNHEALTHY:
                self._consecutive_failures[name] += 1
            else:
                self._consecutive_failures[name] = 0
                
            # Trigger alerts if needed
            check = self._checks.get(name)
            if (check and check.critical and 
                self._consecutive_failures[name] >= self.alert_threshold):
                self._trigger_alert(name, result)
                
    def _update_overall_health(self) -> None:
        """Update overall system health based on check results"""
        with self._lock:
            if not self._check_results:
                self._overall_status = HealthStatus.UNKNOWN
                self._overall_message = "No health checks configured"
                return
                
            critical_checks = [
                name for name, check in self._checks.items() 
                if check.critical and check.enabled
            ]
            
            unhealthy_critical = [
                name for name in critical_checks
                if (name in self._check_results and 
                    self._check_results[name].status == HealthStatus.UNHEALTHY)
            ]
            
            degraded_critical = [
                name for name in critical_checks
                if (name in self._check_results and 
                    self._check_results[name].status == HealthStatus.DEGRADED)
            ]
            
            if unhealthy_critical:
                self._overall_status = HealthStatus.UNHEALTHY
                self._overall_message = f"Critical checks failing: {', '.join(unhealthy_critical)}"
            elif degraded_critical:
                self._overall_status = HealthStatus.DEGRADED
                self._overall_message = f"Critical checks degraded: {', '.join(degraded_critical)}"
            else:
                unhealthy_any = [
                    name for name, result in self._check_results.items()
                    if result.status == HealthStatus.UNHEALTHY
                ]
                if unhealthy_any:
                    self._overall_status = HealthStatus.DEGRADED
                    self._overall_message = f"Non-critical checks failing: {', '.join(unhealthy_any)}"
                else:
                    self._overall_status = HealthStatus.HEALTHY
                    self._overall_message = "All checks passing"
                    
    def _trigger_alert(self, check_name: str, result: HealthCheckResult) -> None:
        """Trigger alert callbacks for failing checks"""
        for callback in self._alert_callbacks:
            try:
                callback(check_name, result)
            except Exception as e:
                print(f"Error in alert callback: {e}")
                
    # Built-in health check implementations
    def _check_system_cpu(self) -> HealthCheckResult:
        """Check system CPU usage"""
        if not HAS_PSUTIL:
            return HealthCheckResult(
                name="system_cpu",
                status=HealthStatus.UNKNOWN,
                message="psutil not available",
                check_type=HealthCheckType.SYSTEM
            )
            
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            if cpu_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"High CPU usage: {cpu_percent:.1f}%"
            elif cpu_percent > 75:
                status = HealthStatus.DEGRADED
                message = f"Elevated CPU usage: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU usage normal: {cpu_percent:.1f}%"
                
            return HealthCheckResult(
                name="system_cpu",
                status=status,
                message=message,
                details={"cpu_percent": cpu_percent},
                check_type=HealthCheckType.SYSTEM
            )
        except Exception as e:
            return HealthCheckResult(
                name="system_cpu",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check CPU: {str(e)}",
                check_type=HealthCheckType.SYSTEM
            )
            
    def _check_system_memory(self) -> HealthCheckResult:
        """Check system memory usage"""
        if not HAS_PSUTIL:
            return HealthCheckResult(
                name="system_memory",
                status=HealthStatus.UNKNOWN,
                message="psutil not available",
                check_type=HealthCheckType.SYSTEM
            )
            
        try:
            memory = psutil.virtual_memory()
            
            if memory.percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"High memory usage: {memory.percent:.1f}%"
            elif memory.percent > 80:
                status = HealthStatus.DEGRADED
                message = f"Elevated memory usage: {memory.percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage normal: {memory.percent:.1f}%"
                
            return HealthCheckResult(
                name="system_memory",
                status=status,
                message=message,
                details={
                    "memory_percent": memory.percent,
                    "available_gb": memory.available / (1024**3),
                    "total_gb": memory.total / (1024**3)
                },
                check_type=HealthCheckType.SYSTEM
            )
        except Exception as e:
            return HealthCheckResult(
                name="system_memory",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check memory: {str(e)}",
                check_type=HealthCheckType.SYSTEM
            )
            
    def _check_system_disk(self) -> HealthCheckResult:
        """Check system disk usage"""
        if not HAS_PSUTIL:
            return HealthCheckResult(
                name="system_disk",
                status=HealthStatus.UNKNOWN,
                message="psutil not available",
                check_type=HealthCheckType.SYSTEM
            )
            
        try:
            disk_usage = psutil.disk_usage('/')
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            
            if disk_percent > 95:
                status = HealthStatus.UNHEALTHY
                message = f"High disk usage: {disk_percent:.1f}%"
            elif disk_percent > 85:
                status = HealthStatus.DEGRADED
                message = f"Elevated disk usage: {disk_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk usage normal: {disk_percent:.1f}%"
                
            return HealthCheckResult(
                name="system_disk",
                status=status,
                message=message,
                details={
                    "disk_percent": disk_percent,
                    "free_gb": disk_usage.free / (1024**3),
                    "total_gb": disk_usage.total / (1024**3)
                },
                check_type=HealthCheckType.SYSTEM
            )
        except Exception as e:
            return HealthCheckResult(
                name="system_disk",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check disk: {str(e)}",
                check_type=HealthCheckType.SYSTEM
            )


# Convenience functions for creating common health checks
def create_database_check(name: str, connection_string: str, timeout: float = 5.0) -> HealthCheck:
    """Create a database connectivity health check"""
    def check_database() -> HealthCheckResult:
        if not HAS_SQLALCHEMY:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNKNOWN,
                message="SQLAlchemy not available",
                check_type=HealthCheckType.DATABASE
            )
            
        try:
            start_time = time.time()
            engine = create_engine(connection_string, pool_timeout=timeout)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            duration = time.time() - start_time
            
            return HealthCheckResult(
                name=name,
                status=HealthStatus.HEALTHY,
                message="Database connection successful",
                details={"connection_time": duration},
                check_type=HealthCheckType.DATABASE
            )
        except Exception as e:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                check_type=HealthCheckType.DATABASE
            )
            
    return HealthCheck(
        name=name,
        check_function=check_database,
        timeout=timeout + 1.0,
        check_type=HealthCheckType.DATABASE,
        critical=True
    )


def create_redis_check(name: str, redis_url: str, timeout: float = 5.0) -> HealthCheck:
    """Create a Redis connectivity health check"""
    def check_redis() -> HealthCheckResult:
        if not HAS_REDIS:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNKNOWN,
                message="Redis library not available",
                check_type=HealthCheckType.CACHE
            )
            
        try:
            start_time = time.time()
            r = redis.from_url(redis_url, socket_timeout=timeout)
            r.ping()
            duration = time.time() - start_time
            
            return HealthCheckResult(
                name=name,
                status=HealthStatus.HEALTHY,
                message="Redis connection successful",
                details={"ping_time": duration},
                check_type=HealthCheckType.CACHE
            )
        except Exception as e:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Redis connection failed: {str(e)}",
                check_type=HealthCheckType.CACHE
            )
            
    return HealthCheck(
        name=name,
        check_function=check_redis,
        timeout=timeout + 1.0,
        check_type=HealthCheckType.CACHE,
        critical=True
    )


def create_http_check(name: str, url: str, timeout: float = 10.0, expected_status: int = 200) -> HealthCheck:
    """Create an HTTP endpoint health check"""
    async def check_http() -> HealthCheckResult:
        if not HAS_AIOHTTP:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNKNOWN,
                message="aiohttp not available",
                check_type=HealthCheckType.EXTERNAL_API
            )
            
        try:
            start_time = time.time()
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url) as response:
                    duration = time.time() - start_time
                    
                    if response.status == expected_status:
                        return HealthCheckResult(
                            name=name,
                            status=HealthStatus.HEALTHY,
                            message=f"HTTP check successful: {response.status}",
                            details={
                                "status_code": response.status,
                                "response_time": duration,
                                "url": url
                            },
                            check_type=HealthCheckType.EXTERNAL_API
                        )
                    else:
                        return HealthCheckResult(
                            name=name,
                            status=HealthStatus.UNHEALTHY,
                            message=f"Unexpected status code: {response.status}",
                            details={
                                "status_code": response.status,
                                "expected_status": expected_status,
                                "response_time": duration,
                                "url": url
                            },
                            check_type=HealthCheckType.EXTERNAL_API
                        )
        except Exception as e:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"HTTP check failed: {str(e)}",
                details={"url": url},
                check_type=HealthCheckType.EXTERNAL_API
            )
            
    return HealthCheck(
        name=name,
        check_function=check_http,
        timeout=timeout + 1.0,
        check_type=HealthCheckType.EXTERNAL_API
    )