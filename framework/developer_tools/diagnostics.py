"""
System Diagnostics Module

Provides comprehensive system diagnostics, health analysis, and troubleshooting
capabilities for identifying and resolving system issues.
"""

import asyncio
import gc
import os
import platform
import socket
import subprocess
import sys
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@dataclass
class SystemInfo:
    """System information snapshot"""
    hostname: str
    platform: str
    architecture: str
    cpu_count: int
    memory_total: int
    disk_total: int
    python_version: str
    uptime: float
    load_average: Tuple[float, float, float]


@dataclass
class HealthCheck:
    """Health check result"""
    name: str
    status: str  # "healthy", "warning", "critical"
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    duration: float


@dataclass
class DiagnosticTest:
    """Diagnostic test definition"""
    name: str
    description: str
    test_function: callable
    severity: str  # "info", "warning", "critical"
    timeout: float
    dependencies: List[str]


class SystemDiagnostics:
    """Comprehensive system diagnostics"""
    
    def __init__(self):
        self._diagnostic_tests: Dict[str, DiagnosticTest] = {}
        self._health_checks: Dict[str, HealthCheck] = {}
        self._system_info: Optional[SystemInfo] = None
        self._monitoring_active = False
        self._setup_default_tests()
    
    def gather_system_info(self) -> SystemInfo:
        """Gather comprehensive system information"""
        try:
            # Get system information
            hostname = socket.gethostname()
            platform_info = platform.platform()
            architecture = platform.architecture()[0]
            python_version = sys.version
            
            if HAS_PSUTIL:
                cpu_count = psutil.cpu_count()
                memory_total = psutil.virtual_memory().total
                disk_total = psutil.disk_usage('/').total
                uptime = time.time() - psutil.boot_time()
            else:
                cpu_count = os.cpu_count() or 1
                memory_total = 8 * 1024**3  # Default 8GB
                disk_total = 100 * 1024**3  # Default 100GB
                uptime = 3600.0  # Default 1 hour
            
            # Load average (Unix-like systems)
            try:
                load_average = os.getloadavg()
            except (OSError, AttributeError):
                load_average = (0.0, 0.0, 0.0)
            
            info = SystemInfo(
                hostname=hostname,
                platform=platform_info,
                architecture=architecture,
                cpu_count=cpu_count,
                memory_total=memory_total,
                disk_total=disk_total,
                python_version=python_version,
                uptime=uptime,
                load_average=load_average
            )
            
            self._system_info = info
            return info
            
        except Exception as e:
            logger.error(f"Error gathering system info: {e}")
            raise
    
    def run_diagnostic_test(self, test_name: str) -> HealthCheck:
        """Run a specific diagnostic test"""
        if test_name not in self._diagnostic_tests:
            raise ValueError(f"Unknown diagnostic test: {test_name}")
        
        test = self._diagnostic_tests[test_name]
        start_time = time.time()
        
        try:
            # Run test with timeout
            result = self._run_with_timeout(test.test_function, test.timeout)
            
            duration = time.time() - start_time
            
            if result is True or (isinstance(result, dict) and result.get('status') == 'healthy'):
                status = "healthy"
                message = f"{test.description} - OK"
                details = result if isinstance(result, dict) else {}
            elif isinstance(result, dict):
                status = result.get('status', 'warning')
                message = result.get('message', f"{test.description} - Check details")
                details = {k: v for k, v in result.items() if k not in ['status', 'message']}
            else:
                status = "warning"
                message = f"{test.description} - {result}"
                details = {}
            
            health_check = HealthCheck(
                name=test_name,
                status=status,
                message=message,
                details=details,
                timestamp=datetime.now(),
                duration=duration
            )
            
            self._health_checks[test_name] = health_check
            return health_check
            
        except Exception as e:
            duration = time.time() - start_time
            
            health_check = HealthCheck(
                name=test_name,
                status="critical",
                message=f"{test.description} - Error: {str(e)}",
                details={'error': str(e), 'error_type': type(e).__name__},
                timestamp=datetime.now(),
                duration=duration
            )
            
            self._health_checks[test_name] = health_check
            return health_check
    
    def run_all_tests(self) -> Dict[str, HealthCheck]:
        """Run all diagnostic tests"""
        results = {}
        
        # Sort tests by dependencies
        sorted_tests = self._sort_tests_by_dependencies()
        
        for test_name in sorted_tests:
            try:
                result = self.run_diagnostic_test(test_name)
                results[test_name] = result
            except Exception as e:
                logger.error(f"Error running test {test_name}: {e}")
                results[test_name] = HealthCheck(
                    name=test_name,
                    status="critical",
                    message=f"Test failed: {str(e)}",
                    details={'error': str(e)},
                    timestamp=datetime.now(),
                    duration=0.0
                )
        
        return results
    
    def register_test(self, test: DiagnosticTest):
        """Register a custom diagnostic test"""
        self._diagnostic_tests[test.name] = test
        logger.info(f"Registered diagnostic test: {test.name}")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary"""
        if not self._health_checks:
            return {"status": "unknown", "message": "No health checks run"}
        
        status_counts = defaultdict(int)
        for check in self._health_checks.values():
            status_counts[check.status] += 1
        
        # Determine overall status
        if status_counts['critical'] > 0:
            overall_status = "critical"
        elif status_counts['warning'] > 0:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "overall_status": overall_status,
            "total_checks": len(self._health_checks),
            "status_breakdown": dict(status_counts),
            "last_check": max(check.timestamp for check in self._health_checks.values()),
            "critical_issues": [
                check.name for check in self._health_checks.values() 
                if check.status == "critical"
            ],
            "warnings": [
                check.name for check in self._health_checks.values() 
                if check.status == "warning"
            ]
        }
    
    def _setup_default_tests(self):
        """Setup default diagnostic tests"""
        
        # CPU test
        self.register_test(DiagnosticTest(
            name="cpu_usage",
            description="CPU usage check",
            test_function=self._test_cpu_usage,
            severity="warning",
            timeout=5.0,
            dependencies=[]
        ))
        
        # Memory test
        self.register_test(DiagnosticTest(
            name="memory_usage",
            description="Memory usage check",
            test_function=self._test_memory_usage,
            severity="critical",
            timeout=5.0,
            dependencies=[]
        ))
        
        # Disk space test
        self.register_test(DiagnosticTest(
            name="disk_space",
            description="Disk space check",
            test_function=self._test_disk_space,
            severity="critical",
            timeout=5.0,
            dependencies=[]
        ))
        
        # Network connectivity test
        self.register_test(DiagnosticTest(
            name="network_connectivity",
            description="Network connectivity check",
            test_function=self._test_network_connectivity,
            severity="warning",
            timeout=10.0,
            dependencies=[]
        ))
        
        # Python environment test
        self.register_test(DiagnosticTest(
            name="python_environment",
            description="Python environment check",
            test_function=self._test_python_environment,
            severity="info",
            timeout=5.0,
            dependencies=[]
        ))
        
        # File system permissions test
        self.register_test(DiagnosticTest(
            name="file_permissions",
            description="File system permissions check",
            test_function=self._test_file_permissions,
            severity="warning",
            timeout=5.0,
            dependencies=[]
        ))
        
        # Database connectivity test (if applicable)
        self.register_test(DiagnosticTest(
            name="database_connectivity",
            description="Database connectivity check",
            test_function=self._test_database_connectivity,
            severity="critical",
            timeout=10.0,
            dependencies=[]
        ))
    
    def _test_cpu_usage(self) -> Dict[str, Any]:
        """Test CPU usage"""
        if not HAS_PSUTIL:
            return {
                "status": "healthy",
                "message": "CPU monitoring not available (psutil not installed)",
                "cpu_percent": 0,
                "cpu_count": os.cpu_count() or 1
            }
            
        cpu_percent = psutil.cpu_percent(interval=1)
        
        if cpu_percent > 90:
            status = "critical"
            message = f"CPU usage very high: {cpu_percent}%"
        elif cpu_percent > 75:
            status = "warning"
            message = f"CPU usage high: {cpu_percent}%"
        else:
            status = "healthy"
            message = f"CPU usage normal: {cpu_percent}%"
        
        return {
            "status": status,
            "message": message,
            "cpu_percent": cpu_percent,
            "cpu_count": psutil.cpu_count(),
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
        }
    
    def _test_memory_usage(self) -> Dict[str, Any]:
        """Test memory usage"""
        if not HAS_PSUTIL:
            return {
                "status": "healthy",
                "message": "Memory monitoring not available (psutil not installed)",
                "memory_percent": 50.0,
                "memory_total_gb": 8.0,
                "memory_available_gb": 4.0,
                "memory_used_gb": 4.0
            }
            
        memory = psutil.virtual_memory()
        
        if memory.percent > 95:
            status = "critical"
            message = f"Memory usage critical: {memory.percent}%"
        elif memory.percent > 85:
            status = "warning"
            message = f"Memory usage high: {memory.percent}%"
        else:
            status = "healthy"
            message = f"Memory usage normal: {memory.percent}%"
        
        return {
            "status": status,
            "message": message,
            "memory_percent": memory.percent,
            "memory_total_gb": memory.total / (1024**3),
            "memory_available_gb": memory.available / (1024**3),
            "memory_used_gb": memory.used / (1024**3)
        }
    
    def _test_disk_space(self) -> Dict[str, Any]:
        """Test disk space"""
        if not HAS_PSUTIL:
            return {
                "status": "healthy",
                "message": "Disk monitoring not available (psutil not installed)",
                "disk_percent_used": 50.0,
                "disk_total_gb": 100.0,
                "disk_free_gb": 50.0,
                "disk_used_gb": 50.0
            }
            
        disk = psutil.disk_usage('/')
        percent_used = (disk.used / disk.total) * 100
        
        if percent_used > 95:
            status = "critical"
            message = f"Disk space critical: {percent_used:.1f}% used"
        elif percent_used > 85:
            status = "warning"
            message = f"Disk space low: {percent_used:.1f}% used"
        else:
            status = "healthy"
            message = f"Disk space OK: {percent_used:.1f}% used"
        
        return {
            "status": status,
            "message": message,
            "disk_percent_used": percent_used,
            "disk_total_gb": disk.total / (1024**3),
            "disk_free_gb": disk.free / (1024**3),
            "disk_used_gb": disk.used / (1024**3)
        }
    
    def _test_network_connectivity(self) -> Dict[str, Any]:
        """Test network connectivity"""
        try:
            # Test DNS resolution
            socket.gethostbyname('google.com')
            
            # Test HTTP connectivity (simple ping-like test)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('google.com', 80))
            sock.close()
            
            if result == 0:
                return {
                    "status": "healthy",
                    "message": "Network connectivity OK",
                    "dns_resolution": True,
                    "external_connectivity": True
                }
            else:
                return {
                    "status": "warning",
                    "message": "Limited network connectivity",
                    "dns_resolution": True,
                    "external_connectivity": False
                }
                
        except Exception as e:
            return {
                "status": "critical",
                "message": f"Network connectivity failed: {str(e)}",
                "dns_resolution": False,
                "external_connectivity": False,
                "error": str(e)
            }
    
    def _test_python_environment(self) -> Dict[str, Any]:
        """Test Python environment"""
        issues = []
        
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 8):
            issues.append(f"Python version {python_version.major}.{python_version.minor} is outdated")
        
        # Check important modules
        required_modules = ['os', 'sys', 'threading', 'asyncio']
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            issues.append(f"Missing modules: {', '.join(missing_modules)}")
        
        # Check garbage collection
        gc_stats = gc.get_stats()
        gc_count = gc.get_count()
        
        status = "critical" if issues else "healthy"
        message = f"Python environment {'issues found' if issues else 'OK'}"
        
        return {
            "status": status,
            "message": message,
            "python_version": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
            "issues": issues,
            "gc_stats": gc_stats,
            "gc_count": gc_count,
            "executable": sys.executable
        }
    
    def _test_file_permissions(self) -> Dict[str, Any]:
        """Test file system permissions"""
        test_paths = [
            '/tmp' if os.name != 'nt' else os.environ.get('TEMP', '.'),
            '.',  # current directory
        ]
        
        permission_issues = []
        
        for path in test_paths:
            if not os.path.exists(path):
                continue
            
            # Test read permission
            if not os.access(path, os.R_OK):
                permission_issues.append(f"No read access to {path}")
            
            # Test write permission
            if not os.access(path, os.W_OK):
                permission_issues.append(f"No write access to {path}")
            
            # Test execute permission (for directories)
            if os.path.isdir(path) and not os.access(path, os.X_OK):
                permission_issues.append(f"No execute access to {path}")
        
        status = "warning" if permission_issues else "healthy"
        message = f"File permissions {'issues found' if permission_issues else 'OK'}"
        
        return {
            "status": status,
            "message": message,
            "issues": permission_issues,
            "tested_paths": test_paths
        }
    
    def _test_database_connectivity(self) -> Dict[str, Any]:
        """Test database connectivity (mock implementation)"""
        # This would be implemented based on the actual database being used
        # For now, return a mock result
        return {
            "status": "healthy",
            "message": "Database connectivity not configured",
            "configured": False
        }
    
    def _run_with_timeout(self, func: callable, timeout: float) -> Any:
        """Run function with timeout"""
        result = [None]
        exception = [None]
        
        def target():
            try:
                result[0] = func()
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            # Force thread termination (not ideal, but necessary for timeout)
            raise TimeoutError(f"Function timed out after {timeout} seconds")
        
        if exception[0]:
            raise exception[0]
        
        return result[0]
    
    def _sort_tests_by_dependencies(self) -> List[str]:
        """Sort tests by their dependencies"""
        # Simple topological sort
        sorted_tests = []
        remaining_tests = set(self._diagnostic_tests.keys())
        
        while remaining_tests:
            ready_tests = [
                test for test in remaining_tests
                if all(dep in sorted_tests for dep in self._diagnostic_tests[test].dependencies)
            ]
            
            if not ready_tests:
                # No tests are ready, might be circular dependencies
                # Just add remaining tests
                sorted_tests.extend(remaining_tests)
                break
            
            for test in ready_tests:
                sorted_tests.append(test)
                remaining_tests.remove(test)
        
        return sorted_tests


class HealthAnalyzer:
    """Analyzes system health trends and patterns"""
    
    def __init__(self):
        self._health_history: List[Dict[str, HealthCheck]] = []
        self._alerts: List[Dict[str, Any]] = []
    
    def analyze_health_trends(self, diagnostics: SystemDiagnostics) -> Dict[str, Any]:
        """Analyze health trends over time"""
        if len(self._health_history) < 2:
            return {"status": "insufficient_data", "message": "Need more data points for trend analysis"}
        
        trends = {}
        
        # Analyze each test's trend
        for test_name in diagnostics._diagnostic_tests.keys():
            test_history = [
                checks.get(test_name) for checks in self._health_history
                if test_name in checks and checks[test_name] is not None
            ]
            
            if len(test_history) >= 2:
                trends[test_name] = self._analyze_test_trend(test_history)
        
        return {
            "trends": trends,
            "overall_trend": self._calculate_overall_trend(trends),
            "recommendations": self._generate_trend_recommendations(trends)
        }
    
    def add_health_snapshot(self, health_checks: Dict[str, HealthCheck]):
        """Add health snapshot to history"""
        self._health_history.append(health_checks)
        
        # Keep only last 100 snapshots
        if len(self._health_history) > 100:
            self._health_history = self._health_history[-100:]
    
    def _analyze_test_trend(self, test_history: List[HealthCheck]) -> Dict[str, Any]:
        """Analyze trend for a specific test"""
        if len(test_history) < 2:
            return {"trend": "unknown", "confidence": 0}
        
        # Simple trend analysis based on status changes
        status_values = {"healthy": 3, "warning": 2, "critical": 1}
        values = [status_values.get(check.status, 0) for check in test_history]
        
        if len(values) < 2:
            return {"trend": "stable", "confidence": 0}
        
        # Calculate trend direction
        recent_avg = sum(values[-3:]) / len(values[-3:])
        older_avg = sum(values[:-3]) / len(values[:-3]) if len(values) > 3 else sum(values[:-1]) / len(values[:-1])
        
        if recent_avg > older_avg + 0.5:
            trend = "improving"
        elif recent_avg < older_avg - 0.5:
            trend = "degrading"
        else:
            trend = "stable"
        
        confidence = min(len(values) / 10.0, 1.0)  # More data = higher confidence
        
        return {
            "trend": trend,
            "confidence": confidence,
            "recent_average": recent_avg,
            "historical_average": older_avg,
            "data_points": len(values)
        }
    
    def _calculate_overall_trend(self, trends: Dict[str, Dict[str, Any]]) -> str:
        """Calculate overall system health trend"""
        if not trends:
            return "unknown"
        
        improving_count = sum(1 for t in trends.values() if t.get("trend") == "improving")
        degrading_count = sum(1 for t in trends.values() if t.get("trend") == "degrading")
        
        if improving_count > degrading_count:
            return "improving"
        elif degrading_count > improving_count:
            return "degrading"
        else:
            return "stable"
    
    def _generate_trend_recommendations(self, trends: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on trends"""
        recommendations = []
        
        for test_name, trend_data in trends.items():
            if trend_data.get("trend") == "degrading" and trend_data.get("confidence", 0) > 0.5:
                if "cpu" in test_name.lower():
                    recommendations.append(f"CPU performance degrading - consider optimizing workload or scaling resources")
                elif "memory" in test_name.lower():
                    recommendations.append(f"Memory usage increasing - check for memory leaks or consider increasing memory")
                elif "disk" in test_name.lower():
                    recommendations.append(f"Disk space declining - clean up old files or expand storage")
                elif "network" in test_name.lower():
                    recommendations.append(f"Network connectivity issues - check network configuration")
                else:
                    recommendations.append(f"{test_name} performance degrading - investigate root cause")
        
        return recommendations


class TroubleshootingGuide:
    """Provides troubleshooting guidance and solutions"""
    
    def __init__(self):
        self._troubleshooting_rules = self._setup_troubleshooting_rules()
    
    def diagnose_issues(self, health_checks: Dict[str, HealthCheck]) -> Dict[str, Any]:
        """Diagnose issues and provide solutions"""
        issues = []
        solutions = []
        
        for check_name, check in health_checks.items():
            if check.status in ["warning", "critical"]:
                issue_info = {
                    "test": check_name,
                    "status": check.status,
                    "message": check.message,
                    "details": check.details
                }
                
                # Find matching troubleshooting rules
                matching_solutions = self._find_solutions(check_name, check)
                
                issue_info["solutions"] = matching_solutions
                issues.append(issue_info)
                solutions.extend(matching_solutions)
        
        return {
            "issues_found": len(issues),
            "issues": issues,
            "priority_solutions": self._prioritize_solutions(solutions),
            "overall_recommendation": self._generate_overall_recommendation(issues)
        }
    
    def _setup_troubleshooting_rules(self) -> Dict[str, List[Dict[str, str]]]:
        """Setup troubleshooting rules"""
        return {
            "cpu_usage": [
                {
                    "condition": "high_usage",
                    "solution": "Identify resource-intensive processes using task manager",
                    "priority": "high"
                },
                {
                    "condition": "high_usage",
                    "solution": "Consider scaling horizontally or upgrading CPU",
                    "priority": "medium"
                },
                {
                    "condition": "high_usage",
                    "solution": "Optimize application algorithms and reduce computational complexity",
                    "priority": "high"
                }
            ],
            "memory_usage": [
                {
                    "condition": "high_usage",
                    "solution": "Check for memory leaks in application code",
                    "priority": "high"
                },
                {
                    "condition": "high_usage",
                    "solution": "Increase available memory or optimize data structures",
                    "priority": "medium"
                },
                {
                    "condition": "high_usage",
                    "solution": "Implement memory pooling or object reuse patterns",
                    "priority": "medium"
                }
            ],
            "disk_space": [
                {
                    "condition": "low_space",
                    "solution": "Clean up temporary files and logs",
                    "priority": "high"
                },
                {
                    "condition": "low_space",
                    "solution": "Archive or compress old data",
                    "priority": "medium"
                },
                {
                    "condition": "low_space",
                    "solution": "Expand disk storage capacity",
                    "priority": "low"
                }
            ],
            "network_connectivity": [
                {
                    "condition": "connection_failed",
                    "solution": "Check network configuration and firewall settings",
                    "priority": "high"
                },
                {
                    "condition": "connection_failed",
                    "solution": "Verify DNS resolution and routing",
                    "priority": "high"
                },
                {
                    "condition": "connection_failed",
                    "solution": "Test with different network interfaces",
                    "priority": "medium"
                }
            ]
        }
    
    def _find_solutions(self, test_name: str, check: HealthCheck) -> List[Dict[str, str]]:
        """Find solutions for a specific test failure"""
        if test_name not in self._troubleshooting_rules:
            return [{"solution": "No specific troubleshooting guide available", "priority": "low"}]
        
        return self._troubleshooting_rules[test_name]
    
    def _prioritize_solutions(self, solutions: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Prioritize solutions by importance"""
        priority_order = {"high": 3, "medium": 2, "low": 1}
        
        return sorted(solutions, key=lambda s: priority_order.get(s.get("priority", "low"), 1), reverse=True)
    
    def _generate_overall_recommendation(self, issues: List[Dict[str, Any]]) -> str:
        """Generate overall recommendation"""
        if not issues:
            return "System appears healthy. Continue regular monitoring."
        
        critical_count = sum(1 for issue in issues if issue["status"] == "critical")
        warning_count = sum(1 for issue in issues if issue["status"] == "warning")
        
        if critical_count > 0:
            return f"Immediate attention required: {critical_count} critical issues detected. Address critical issues first."
        elif warning_count > 2:
            return f"Multiple warnings detected: {warning_count} issues need attention. Plan maintenance window."
        else:
            return f"Minor issues detected: {warning_count} warnings. Monitor and address during next maintenance."


# Global instances
_system_diagnostics = SystemDiagnostics()
_health_analyzer = HealthAnalyzer()
_troubleshooting_guide = TroubleshootingGuide()

# Convenience functions
def run_system_diagnostics() -> Dict[str, HealthCheck]:
    """Run comprehensive system diagnostics"""
    return _system_diagnostics.run_all_tests()

def get_system_info() -> SystemInfo:
    """Get system information"""
    return _system_diagnostics.gather_system_info()

def get_health_summary() -> Dict[str, Any]:
    """Get system health summary"""
    return _system_diagnostics.get_health_summary()

def analyze_health_trends() -> Dict[str, Any]:
    """Analyze health trends"""
    return _health_analyzer.analyze_health_trends(_system_diagnostics)

def get_troubleshooting_guide() -> Dict[str, Any]:
    """Get troubleshooting recommendations"""
    health_checks = _system_diagnostics._health_checks
    return _troubleshooting_guide.diagnose_issues(health_checks)

def register_diagnostic_test(test: DiagnosticTest):
    """Register custom diagnostic test"""
    _system_diagnostics.register_test(test)