"""
Comprehensive Tests for Phase 7: Advanced Developer Tooling and Debugging Utilities

Tests all components of the developer tools framework including debugging,
profiling, code inspection, REPL, dashboard, generation, analysis, and more.
"""

import asyncio
import pytest
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import all developer tools modules
from ..debugger import AdvancedDebugger, BreakpointManager, DebugSession
from ..profiler import PerformanceProfiler, CodeProfiler, MemoryProfiler
from ..inspector import CodeInspector, FrameworkInspector, RuntimeInspector
from ..repl import DeveloperREPL, CommandProcessor, InteractiveShell
from ..dashboard import DeveloperDashboard, MetricsCollector, AlertManager
from ..generator import CodeGenerator, ScaffoldGenerator, TemplateEngine
from ..analyzer import LogAnalyzer, ErrorTracker, PerformanceAnalyzer
from ..hotreload import HotReloadManager, FileWatcher, ModuleReloader
from ..testing import TestingUtilities, MockGenerator, TestDataFactory
from ..diagnostics import SystemDiagnostics, HealthAnalyzer, TroubleshootingGuide


class TestAdvancedDebugger:
    """Test suite for advanced debugger"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.debugger = AdvancedDebugger()
    
    def test_session_management(self):
        """Test debugging session management"""
        # Start session
        session_id = self.debugger.start_session("test_session")
        assert session_id is not None
        
        # Get session
        session = self.debugger.get_session(session_id)
        assert session is not None
        assert session.session_id == session_id
        assert session.active is True
        
        # Stop session
        result = self.debugger.stop_session(session_id)
        assert result is True
        
        # Check session is inactive
        session = self.debugger.get_session(session_id)
        assert session.active is False
    
    def test_breakpoint_management(self):
        """Test breakpoint management"""
        # Add breakpoint
        bp_id = self.debugger.add_breakpoint(__file__, 100, condition="x > 5")
        assert bp_id is not None
        
        # Get breakpoints
        breakpoints = self.debugger.get_breakpoints()
        assert len(breakpoints) == 1
        assert breakpoints[0].id == bp_id
        assert breakpoints[0].condition == "x > 5"
        
        # Remove breakpoint
        result = self.debugger.remove_breakpoint(bp_id)
        assert result is True
        
        # Check breakpoint removed
        breakpoints = self.debugger.get_breakpoints()
        assert len(breakpoints) == 0
    
    def test_debug_context(self):
        """Test debug context manager"""
        with self.debugger.debug_context("context_test") as session_id:
            assert session_id is not None
            
            # Add breakpoint in context
            bp_id = self.debugger.add_breakpoint(__file__, 200, temporary=True)
            assert bp_id is not None
        
        # Session should be stopped after context
        session = self.debugger.get_session(session_id)
        assert session.active is False


class TestPerformanceProfiler:
    """Test suite for performance profiler"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.profiler = PerformanceProfiler()
    
    def test_profiling_session(self):
        """Test profiling session lifecycle"""
        # Start session
        session_id = self.profiler.start_session("test_profile")
        assert session_id is not None
        
        # Simulate some work
        result = sum(range(1000))
        
        # Stop session
        session = self.profiler.stop_session(session_id)
        assert session is not None
        assert session.duration > 0
        assert len(session.profile_stats) > 0
    
    def test_profile_context(self):
        """Test profiling context manager"""
        with self.profiler.profile_context("context_test") as session_id:
            # Simulate computational work
            data = [i**2 for i in range(1000)]
            result = sum(data)
        
        # Check session results
        session = self.profiler.get_session(session_id)
        assert session is not None
        assert session.duration > 0
    
    def test_performance_analysis(self):
        """Test performance analysis"""
        # Create a session with some work
        with self.profiler.profile_context("analysis_test") as session_id:
            # Multiple function calls
            for i in range(100):
                str(i).upper()
        
        # Analyze performance
        analysis = self.profiler.analyze_performance(session_id)
        assert analysis is not None
        assert 'duration' in analysis
        assert 'total_functions' in analysis
        assert 'top_functions' in analysis


class TestCodeInspector:
    """Test suite for code inspector"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.inspector = CodeInspector()
    
    def test_function_inspection(self):
        """Test function inspection"""
        def sample_function(x: int, y: str = "default") -> str:
            """Sample function for testing"""
            return f"{x}: {y}"
        
        func_info = self.inspector.inspect_function(sample_function)
        
        assert func_info.name == "sample_function"
        assert "x" in func_info.arguments
        assert "y" in func_info.arguments
        assert func_info.docstring == "Sample function for testing"
        assert func_info.is_async is False
        assert func_info.complexity >= 1
    
    def test_class_inspection(self):
        """Test class inspection"""
        class SampleClass:
            """Sample class for testing"""
            
            def __init__(self):
                self.value = 42
            
            def method1(self):
                return self.value
            
            def method2(self, x):
                return x * 2
        
        class_info = self.inspector.inspect_class(SampleClass)
        
        assert class_info.name == "SampleClass"
        assert class_info.docstring == "Sample class for testing"
        assert len(class_info.methods) >= 2  # At least method1 and method2
        assert "value" in class_info.attributes or len(class_info.methods) > 0
    
    def test_code_quality_analysis(self):
        """Test code quality analysis"""
        def complex_function(x):
            """Complex function for testing"""
            if x > 10:
                if x > 20:
                    if x > 30:
                        return x * 3
                    else:
                        return x * 2
                else:
                    return x + 10
            else:
                return x
        
        quality = self.inspector.analyze_code_quality(complex_function)
        
        assert 'complexity_score' in quality
        assert 'documentation_score' in quality
        assert quality['complexity_score'] > 0
        assert quality['documentation_score'] > 0  # Has docstring


class TestDeveloperREPL:
    """Test suite for developer REPL"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.repl = DeveloperREPL()
    
    def test_code_execution(self):
        """Test code execution in REPL"""
        # Execute simple assignment
        result = self.repl.execute_code("x = 42", capture_output=True)
        assert result.success is True
        
        # Execute expression
        result = self.repl.execute_code("x * 2", capture_output=True)
        assert result.success is True
        assert result.result == 84
    
    def test_special_commands(self):
        """Test special REPL commands"""
        # Setup some variables
        self.repl.execute_code("test_var = 'hello'", capture_output=True)
        
        # Test %vars command
        result = self.repl.execute_code("%vars", capture_output=True)
        assert result.success is True
        assert "test_var" in result.output
    
    def test_session_info(self):
        """Test session information"""
        # Execute some commands
        self.repl.execute_code("a = 1", capture_output=True)
        self.repl.execute_code("b = 2", capture_output=True)
        
        session_info = self.repl.get_session_info()
        assert session_info is not None
        assert session_info.commands_executed >= 2
        assert 'a' in session_info.variables
        assert 'b' in session_info.variables


class TestCodeGenerator:
    """Test suite for code generator"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = CodeGenerator()
    
    def test_template_generation(self):
        """Test code generation from templates"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            output_path = f.name
        
        try:
            # Generate Python module
            generated_file = self.generator.generate_from_template(
                'python_module',
                output_path,
                {
                    'class_name': 'TestClass',
                    'class_description': 'Test class',
                    'function_name': 'test_function',
                    'function_description': 'Test function',
                    'parameters': 'data: str',
                    'return_type': 'str',
                    'description': 'Test module'
                }
            )
            
            assert generated_file.path == output_path
            assert 'TestClass' in generated_file.content
            assert 'test_function' in generated_file.content
            assert Path(output_path).exists()
            
        finally:
            # Cleanup
            Path(output_path).unlink(missing_ok=True)
    
    def test_crud_generation(self):
        """Test CRUD API generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate CRUD API
            files = self.generator.generate_crud_api(
                'User',
                {'name': 'str', 'email': 'str', 'age': 'int'},
                temp_dir
            )
            
            assert len(files) >= 2  # Should generate at least models and API files
            
            # Check files exist
            for file in files:
                assert Path(file.path).exists()
                assert 'User' in file.content


class TestLogAnalyzer:
    """Test suite for log analyzer"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.analyzer = LogAnalyzer()
    
    def test_log_parsing(self):
        """Test log line parsing"""
        log_line = "2024-01-15 10:30:15,123 - myapp - ERROR - Test error message"
        entry = self.analyzer.parse_log_line(log_line)
        
        assert entry is not None
        assert entry.level == "ERROR"
        assert entry.message == "Test error message"
        assert entry.logger_name == "myapp"
    
    def test_pattern_detection(self):
        """Test log pattern detection"""
        # Add multiple similar log entries
        sample_logs = [
            "2024-01-15 10:30:15,123 - myapp - ERROR - Database connection failed",
            "2024-01-15 10:30:16,456 - myapp - ERROR - Database connection failed",
            "2024-01-15 10:30:17,789 - myapp - ERROR - Database connection failed",
        ]
        
        for log_line in sample_logs:
            entry = self.analyzer.parse_log_line(log_line)
            if entry:
                self.analyzer.add_log_entry(entry)
        
        patterns = self.analyzer.detect_patterns(min_occurrences=2)
        assert len(patterns) >= 1
        assert any("Database connection" in p.description for p in patterns)
    
    def test_error_analysis(self):
        """Test error analysis"""
        # Add error entries
        error_logs = [
            "2024-01-15 10:30:15,123 - myapp - ERROR - Connection timeout",
            "2024-01-15 10:30:16,456 - myapp - ERROR - Connection timeout",
            "2024-01-15 10:30:17,789 - myapp - CRITICAL - System failure",
        ]
        
        for log_line in error_logs:
            entry = self.analyzer.parse_log_line(log_line)
            if entry:
                self.analyzer.add_log_entry(entry)
        
        error_analyses = self.analyzer.analyze_errors()
        assert len(error_analyses) >= 1
        
        # Check if connection timeout was analyzed
        timeout_analysis = next((a for a in error_analyses if "timeout" in a.error_type.lower()), None)
        assert timeout_analysis is not None
        assert timeout_analysis.count >= 2


class TestTestingUtilities:
    """Test suite for testing utilities"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.testing_utils = TestingUtilities()
    
    def test_mock_generation(self):
        """Test mock object generation"""
        # Create simple mock
        mock_obj = self.testing_utils.mock_generator.create_mock(name="test_mock")
        assert mock_obj is not None
        
        # Configure mock behavior
        mock_obj.get_data.return_value = {"test": "data"}
        result = mock_obj.get_data()
        assert result == {"test": "data"}
    
    def test_test_data_factory(self):
        """Test test data generation"""
        factory = self.testing_utils.data_factory
        
        # Test string generation
        test_string = factory.generate_string(length=10)
        assert len(test_string) == 10
        
        # Test email generation
        email = factory.generate_email()
        assert "@" in email
        assert "." in email
        
        # Test dictionary generation
        schema = {
            'id': 'uuid',
            'name': 'string',
            'email': 'email',
            'count': 'number'
        }
        test_dict = factory.generate_dict(schema)
        
        assert 'id' in test_dict
        assert 'name' in test_dict
        assert 'email' in test_dict
        assert 'count' in test_dict
        assert "@" in test_dict['email']
    
    def test_performance_testing(self):
        """Test performance testing utilities"""
        def sample_function():
            return sum(range(100))
        
        # Run performance test
        perf_result = self.testing_utils.create_performance_test(
            sample_function,
            max_execution_time=1.0,
            iterations=10
        )
        
        assert 'average_time' in perf_result
        assert 'max_time' in perf_result
        assert 'iterations' in perf_result
        assert perf_result['iterations'] == 10
        assert perf_result['passed'] is True  # Should pass for simple function


class TestSystemDiagnostics:
    """Test suite for system diagnostics"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.diagnostics = SystemDiagnostics()
    
    def test_system_info_gathering(self):
        """Test system information gathering"""
        system_info = self.diagnostics.gather_system_info()
        
        assert system_info.hostname is not None
        assert system_info.platform is not None
        assert system_info.cpu_count > 0
        assert system_info.memory_total > 0
        assert system_info.python_version is not None
    
    def test_diagnostic_tests(self):
        """Test diagnostic test execution"""
        # Run CPU test
        cpu_result = self.diagnostics.run_diagnostic_test("cpu_usage")
        assert cpu_result.name == "cpu_usage"
        assert cpu_result.status in ["healthy", "warning", "critical"]
        assert cpu_result.duration >= 0
        
        # Run memory test
        memory_result = self.diagnostics.run_diagnostic_test("memory_usage")
        assert memory_result.name == "memory_usage"
        assert memory_result.status in ["healthy", "warning", "critical"]
    
    def test_health_summary(self):
        """Test health summary generation"""
        # Run some tests first
        self.diagnostics.run_diagnostic_test("cpu_usage")
        self.diagnostics.run_diagnostic_test("memory_usage")
        
        # Get health summary
        summary = self.diagnostics.get_health_summary()
        
        assert 'overall_status' in summary
        assert 'total_checks' in summary
        assert summary['total_checks'] >= 2
        assert 'status_breakdown' in summary


class TestIntegration:
    """Integration tests for developer tools"""
    
    def test_full_workflow_integration(self):
        """Test complete development workflow integration"""
        # Initialize components
        debugger = AdvancedDebugger()
        profiler = PerformanceProfiler()
        inspector = CodeInspector()
        testing_utils = TestingUtilities()
        
        # Step 1: Create and inspect a function
        def workflow_function(data):
            """Workflow test function"""
            result = []
            for item in data:
                if item > 0:
                    result.append(item * 2)
            return result
        
        func_info = inspector.inspect_function(workflow_function)
        assert func_info.name == "workflow_function"
        
        # Step 2: Profile the function
        with profiler.profile_context("workflow_test") as session_id:
            test_data = list(range(-5, 10))
            result = workflow_function(test_data)
        
        session = profiler.get_session(session_id)
        assert session is not None
        assert len(result) > 0
        
        # Step 3: Test the function
        mock_data = testing_utils.data_factory.generate_list(
            lambda: testing_utils.data_factory.generate_number(1, 100, is_float=False),
            length=5
        )
        
        test_result = workflow_function(mock_data)
        assert len(test_result) <= len(mock_data)  # Some items might be filtered out
        
        # Step 4: Debug session
        with debugger.debug_context("workflow_debug") as debug_session:
            # Add breakpoint (would trigger in real debugging)
            bp_id = debugger.add_breakpoint(__file__, 500, temporary=True)
            assert bp_id is not None
        
        debug_session_obj = debugger.get_session(debug_session)
        assert debug_session_obj.active is False  # Should be stopped after context
    
    def test_error_tracking_integration(self):
        """Test error tracking integration"""
        from ..analyzer import track_error
        
        # Create an error scenario
        try:
            raise ValueError("Test integration error")
        except Exception as e:
            track_error(e, {'context': 'integration_test', 'component': 'testing'})
        
        # The error should be tracked (tested via the global error tracker)
        # This is more of a smoke test to ensure the integration works
        assert True  # If we get here without exception, integration works
    
    @pytest.mark.asyncio
    async def test_async_integration(self):
        """Test async components integration"""
        # Test async profiling
        profiler = PerformanceProfiler()
        
        async def async_function():
            await asyncio.sleep(0.01)
            return "async_result"
        
        # Profile async function
        with profiler.profile_context("async_test") as session_id:
            result = await async_function()
        
        assert result == "async_result"
        
        session = profiler.get_session(session_id)
        assert session is not None
        assert session.duration > 0.01  # Should take at least the sleep time


# Pytest fixtures for all tests
@pytest.fixture
def temp_directory():
    """Temporary directory fixture"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_code_file(temp_directory):
    """Sample code file fixture"""
    code_content = '''
def sample_function(x, y=10):
    """Sample function for testing"""
    if x > y:
        return x * y
    else:
        return x + y

class SampleClass:
    """Sample class for testing"""
    
    def __init__(self, value):
        self.value = value
    
    def process(self, data):
        return [item * self.value for item in data]
'''
    
    file_path = Path(temp_directory) / "sample.py"
    file_path.write_text(code_content)
    return file_path


@pytest.fixture
def mock_log_file(temp_directory):
    """Mock log file fixture"""
    log_content = '''2024-01-15 10:30:15,123 - myapp - INFO - Application started
2024-01-15 10:30:16,456 - myapp - DEBUG - Processing request
2024-01-15 10:30:17,789 - myapp - ERROR - Database connection failed
2024-01-15 10:30:18,012 - myapp - WARNING - High memory usage: 85%
2024-01-15 10:30:19,345 - myapp - ERROR - Database connection failed
2024-01-15 10:30:20,678 - myapp - INFO - Request completed
'''
    
    file_path = Path(temp_directory) / "test.log"
    file_path.write_text(log_content)
    return file_path


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmarks for developer tools"""
    
    def test_profiler_overhead(self):
        """Test profiler performance overhead"""
        profiler = PerformanceProfiler()
        
        # Measure without profiling
        start_time = time.time()
        for i in range(1000):
            str(i).upper()
        baseline_time = time.time() - start_time
        
        # Measure with profiling
        with profiler.profile_context("overhead_test"):
            start_time = time.time()
            for i in range(1000):
                str(i).upper()
            profiled_time = time.time() - start_time
        
        # Overhead should be reasonable (less than 10x slower)
        overhead_ratio = profiled_time / baseline_time
        assert overhead_ratio < 10, f"Profiler overhead too high: {overhead_ratio}x"
    
    def test_inspector_performance(self):
        """Test code inspector performance"""
        inspector = CodeInspector()
        
        def complex_function():
            for i in range(100):
                for j in range(100):
                    if i > j:
                        yield i * j
        
        # Time the inspection
        start_time = time.time()
        func_info = inspector.inspect_function(complex_function)
        inspection_time = time.time() - start_time
        
        # Should complete quickly (less than 1 second)
        assert inspection_time < 1.0, f"Inspection too slow: {inspection_time}s"
        assert func_info.name == "complex_function"
    
    def test_mock_generation_performance(self):
        """Test mock generation performance"""
        mock_gen = MockGenerator()
        
        # Generate many mocks quickly
        start_time = time.time()
        mocks = [mock_gen.create_mock(name=f"mock_{i}") for i in range(1000)]
        generation_time = time.time() - start_time
        
        # Should be fast (less than 1 second for 1000 mocks)
        assert generation_time < 1.0, f"Mock generation too slow: {generation_time}s"
        assert len(mocks) == 1000


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])