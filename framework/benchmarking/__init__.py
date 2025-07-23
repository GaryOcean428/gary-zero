"""
GAIA-style benchmarking framework for Gary-Zero.

This module provides comprehensive benchmarking capabilities including:
- Standardized test suite execution
- Performance comparison across configurations
- Regression detection and reporting
- Integration with unified logging
"""

from .analysis import BenchmarkAnalysis, RegressionDetector
from .harness import BenchmarkHarness, BenchmarkResult, TestCase
from .reporting import BenchmarkReporter
from .tasks import StandardTasks, TaskRegistry

__all__ = [
    'BenchmarkHarness',
    'BenchmarkResult',
    'TestCase',
    'StandardTasks',
    'TaskRegistry',
    'BenchmarkAnalysis',
    'RegressionDetector',
    'BenchmarkReporter'
]
