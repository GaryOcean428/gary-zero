"""
GAIA-style benchmarking framework for Gary-Zero.

This module provides comprehensive benchmarking capabilities including:
- Standardized test suite execution
- Performance comparison across configurations
- Regression detection and reporting
- Integration with unified logging
"""

from .harness import BenchmarkHarness, BenchmarkResult, TestCase
from .tasks import StandardTasks, TaskRegistry
from .analysis import BenchmarkAnalysis, RegressionDetector
from .reporting import BenchmarkReporter

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