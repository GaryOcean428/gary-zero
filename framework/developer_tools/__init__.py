"""
Gary-Zero Framework - Developer Tools Module

Advanced developer tooling and debugging utilities for enhanced development experience.
Provides comprehensive debugging, profiling, and development workflow automation.
"""

from .debugger import AdvancedDebugger, DebugSession, BreakpointManager
from .profiler import PerformanceProfiler, CodeProfiler, MemoryProfiler
from .inspector import CodeInspector, FrameworkInspector, RuntimeInspector
from .repl import DeveloperREPL, InteractiveShell, CommandProcessor
from .dashboard import DeveloperDashboard, DebugDashboard, MetricsDashboard
from .generator import CodeGenerator, ScaffoldGenerator, TemplateEngine
from .analyzer import LogAnalyzer, ErrorTracker, PerformanceAnalyzer
from .hotreload import HotReloadManager, FileWatcher, AutoReloader
from .testing import TestingUtilities, MockGenerator, TestDataFactory
from .diagnostics import SystemDiagnostics, HealthAnalyzer, TroubleshootingGuide

__all__ = [
    # Core Debugging
    "AdvancedDebugger",
    "DebugSession", 
    "BreakpointManager",
    
    # Performance Analysis
    "PerformanceProfiler",
    "CodeProfiler",
    "MemoryProfiler",
    
    # Code Inspection
    "CodeInspector",
    "FrameworkInspector", 
    "RuntimeInspector",
    
    # Interactive Development
    "DeveloperREPL",
    "InteractiveShell",
    "CommandProcessor",
    
    # Developer Dashboards
    "DeveloperDashboard",
    "DebugDashboard",
    "MetricsDashboard",
    
    # Code Generation
    "CodeGenerator",
    "ScaffoldGenerator",
    "TemplateEngine",
    
    # Analysis Tools
    "LogAnalyzer", 
    "ErrorTracker",
    "PerformanceAnalyzer",
    
    # Hot Reload
    "HotReloadManager",
    "FileWatcher",
    "AutoReloader",
    
    # Testing Utilities
    "TestingUtilities",
    "MockGenerator", 
    "TestDataFactory",
    
    # System Diagnostics
    "SystemDiagnostics",
    "HealthAnalyzer",
    "TroubleshootingGuide"
]

__version__ = "1.0.0"