"""
Code Inspector Module

Provides comprehensive code inspection, analysis, and introspection capabilities
for understanding code structure, dependencies, and runtime behavior.
"""

import ast
import dis
import gc
import importlib
import inspect
import sys
import types
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import logging

logger = logging.getLogger(__name__)


@dataclass
class CodeMetrics:
    """Code complexity and quality metrics"""
    lines_of_code: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    halstead_metrics: Dict[str, float]
    maintainability_index: float
    technical_debt_ratio: float


@dataclass
class FunctionInfo:
    """Function information and metadata"""
    name: str
    module: str
    file_path: str
    line_number: int
    arguments: List[str]
    return_annotation: Optional[str]
    docstring: Optional[str]
    source_code: Optional[str]
    bytecode: Optional[str]
    is_async: bool
    is_generator: bool
    is_coroutine: bool
    decorators: List[str]
    calls: List[str]
    complexity: int


@dataclass
class ClassInfo:
    """Class information and metadata"""
    name: str
    module: str
    file_path: str
    line_number: int
    base_classes: List[str]
    methods: List[FunctionInfo]
    attributes: List[str]
    docstring: Optional[str]
    source_code: Optional[str]
    is_abstract: bool
    is_dataclass: bool
    metaclass: Optional[str]


@dataclass
class ModuleInfo:
    """Module information and metadata"""
    name: str
    file_path: str
    imports: List[str]
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    variables: List[str]
    docstring: Optional[str]
    size_bytes: int
    dependencies: List[str]
    reverse_dependencies: List[str]


@dataclass
class DependencyGraph:
    """Code dependency graph"""
    nodes: Set[str]
    edges: List[Tuple[str, str]]
    circular_dependencies: List[List[str]]
    depth_levels: Dict[str, int]


class CodeComplexityAnalyzer:
    """Analyzes code complexity metrics"""
    
    def __init__(self):
        self._complexity_cache: Dict[str, CodeMetrics] = {}
    
    def analyze_function(self, func: types.FunctionType) -> CodeMetrics:
        """Analyze complexity metrics for a function"""
        try:
            source = inspect.getsource(func)
            tree = ast.parse(source)
            
            lines_of_code = len([line for line in source.split('\n') if line.strip()])
            cyclomatic_complexity = self._calculate_cyclomatic_complexity(tree)
            cognitive_complexity = self._calculate_cognitive_complexity(tree)
            halstead_metrics = self._calculate_halstead_metrics(tree)
            
            maintainability_index = self._calculate_maintainability_index(
                lines_of_code, cyclomatic_complexity, halstead_metrics
            )
            
            technical_debt_ratio = self._calculate_technical_debt_ratio(
                cyclomatic_complexity, cognitive_complexity, lines_of_code
            )
            
            return CodeMetrics(
                lines_of_code=lines_of_code,
                cyclomatic_complexity=cyclomatic_complexity,
                cognitive_complexity=cognitive_complexity,
                halstead_metrics=halstead_metrics,
                maintainability_index=maintainability_index,
                technical_debt_ratio=technical_debt_ratio
            )
        except Exception as e:
            logger.error(f"Error analyzing function complexity: {e}")
            return CodeMetrics(0, 0, 0, {}, 0.0, 0.0)
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            # Decision points that increase complexity
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(node, ast.ListComp):
                complexity += 1
        
        return complexity
    
    def _calculate_cognitive_complexity(self, tree: ast.AST) -> int:
        """Calculate cognitive complexity (more human-oriented)"""
        complexity = 0
        nesting_level = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1 + nesting_level
                nesting_level += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1 + nesting_level
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(node, ast.FunctionDef):
                nesting_level += 1
        
        return complexity
    
    def _calculate_halstead_metrics(self, tree: ast.AST) -> Dict[str, float]:
        """Calculate Halstead complexity metrics"""
        operators = set()
        operands = set()
        operator_count = 0
        operand_count = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp):
                operators.add(type(node.op).__name__)
                operator_count += 1
            elif isinstance(node, ast.UnaryOp):
                operators.add(type(node.op).__name__)
                operator_count += 1
            elif isinstance(node, ast.Compare):
                operator_count += len(node.ops)
                for op in node.ops:
                    operators.add(type(op).__name__)
            elif isinstance(node, ast.Name):
                operands.add(node.id)
                operand_count += 1
            elif isinstance(node, ast.Constant):
                operands.add(str(node.value))
                operand_count += 1
        
        n1 = len(operators)  # Unique operators
        n2 = len(operands)   # Unique operands
        N1 = operator_count  # Total operators
        N2 = operand_count   # Total operands
        
        if n1 == 0 or n2 == 0:
            return {}
        
        vocabulary = n1 + n2
        length = N1 + N2
        volume = length * (vocabulary.bit_length() if vocabulary > 0 else 0)
        difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
        effort = difficulty * volume
        
        return {
            'vocabulary': vocabulary,
            'length': length,
            'volume': volume,
            'difficulty': difficulty,
            'effort': effort
        }
    
    def _calculate_maintainability_index(
        self, 
        loc: int, 
        complexity: int, 
        halstead: Dict[str, float]
    ) -> float:
        """Calculate maintainability index"""
        try:
            volume = halstead.get('volume', 1)
            mi = (171 - 5.2 * (volume ** 0.23) - 0.23 * complexity - 16.2 * (loc ** 0.5))
            return max(0, mi)  # Normalize to positive values
        except:
            return 0.0
    
    def _calculate_technical_debt_ratio(
        self, 
        cyclomatic: int, 
        cognitive: int, 
        loc: int
    ) -> float:
        """Calculate technical debt ratio"""
        if loc == 0:
            return 0.0
        
        # Simple heuristic: debt increases with complexity
        debt_score = (cyclomatic * 2 + cognitive * 3) / loc
        return min(1.0, debt_score)  # Normalize to 0-1


class CodeInspector:
    """Main code inspection and analysis engine"""
    
    def __init__(self):
        self._complexity_analyzer = CodeComplexityAnalyzer()
        self._cache: Dict[str, Any] = {}
    
    def inspect_function(self, func: types.FunctionType) -> FunctionInfo:
        """Comprehensive function inspection"""
        try:
            signature = inspect.signature(func)
            source = inspect.getsource(func)
            filename = inspect.getfile(func)
            line_number = inspect.getsourcelines(func)[1]
            
            # Get function details
            arguments = list(signature.parameters.keys())
            return_annotation = str(signature.return_annotation) if signature.return_annotation != inspect.Signature.empty else None
            docstring = inspect.getdoc(func)
            
            # Analyze decorators
            decorators = []
            if hasattr(func, '__wrapped__'):
                decorators.append('wrapped')
            
            # Get bytecode
            bytecode = None
            try:
                import io
                output = io.StringIO()
                dis.dis(func, file=output)
                bytecode = output.getvalue()
            except:
                pass
            
            # Analyze function calls
            calls = self._extract_function_calls(source)
            
            # Calculate complexity
            complexity_metrics = self._complexity_analyzer.analyze_function(func)
            
            return FunctionInfo(
                name=func.__name__,
                module=func.__module__,
                file_path=filename,
                line_number=line_number,
                arguments=arguments,
                return_annotation=return_annotation,
                docstring=docstring,
                source_code=source,
                bytecode=bytecode,
                is_async=inspect.iscoroutinefunction(func),
                is_generator=inspect.isgeneratorfunction(func),
                is_coroutine=inspect.iscoroutine(func),
                decorators=decorators,
                calls=calls,
                complexity=complexity_metrics.cyclomatic_complexity
            )
        except Exception as e:
            logger.error(f"Error inspecting function {func.__name__}: {e}")
            return FunctionInfo(
                name=func.__name__,
                module=getattr(func, '__module__', 'unknown'),
                file_path='unknown',
                line_number=0,
                arguments=[],
                return_annotation=None,
                docstring=None,
                source_code=None,
                bytecode=None,
                is_async=False,
                is_generator=False,
                is_coroutine=False,
                decorators=[],
                calls=[],
                complexity=0
            )
    
    def inspect_class(self, cls: type) -> ClassInfo:
        """Comprehensive class inspection"""
        try:
            source = inspect.getsource(cls)
            filename = inspect.getfile(cls)
            line_number = inspect.getsourcelines(cls)[1]
            
            # Get class details
            base_classes = [base.__name__ for base in cls.__bases__]
            docstring = inspect.getdoc(cls)
            
            # Inspect methods
            methods = []
            for name, method in inspect.getmembers(cls, inspect.isfunction):
                try:
                    method_info = self.inspect_function(method)
                    methods.append(method_info)
                except:
                    pass
            
            # Get attributes
            attributes = []
            for name, value in inspect.getmembers(cls):
                if not name.startswith('_') and not inspect.ismethod(value) and not inspect.isfunction(value):
                    attributes.append(name)
            
            # Check special properties
            is_abstract = inspect.isabstract(cls)
            is_dataclass = hasattr(cls, '__dataclass_fields__')
            metaclass = type(cls).__name__ if type(cls) != type else None
            
            return ClassInfo(
                name=cls.__name__,
                module=cls.__module__,
                file_path=filename,
                line_number=line_number,
                base_classes=base_classes,
                methods=methods,
                attributes=attributes,
                docstring=docstring,
                source_code=source,
                is_abstract=is_abstract,
                is_dataclass=is_dataclass,
                metaclass=metaclass
            )
        except Exception as e:
            logger.error(f"Error inspecting class {cls.__name__}: {e}")
            return ClassInfo(
                name=cls.__name__,
                module=getattr(cls, '__module__', 'unknown'),
                file_path='unknown',
                line_number=0,
                base_classes=[],
                methods=[],
                attributes=[],
                docstring=None,
                source_code=None,
                is_abstract=False,
                is_dataclass=False,
                metaclass=None
            )
    
    def inspect_module(self, module: types.ModuleType) -> ModuleInfo:
        """Comprehensive module inspection"""
        try:
            filename = inspect.getfile(module)
            docstring = inspect.getdoc(module)
            
            # Get file size
            size_bytes = Path(filename).stat().st_size if Path(filename).exists() else 0
            
            # Get imports, functions, classes, variables
            imports = []
            functions = []
            classes = []
            variables = []
            
            for name, obj in inspect.getmembers(module):
                if inspect.ismodule(obj) and obj.__name__ != module.__name__:
                    imports.append(obj.__name__)
                elif inspect.isfunction(obj) and obj.__module__ == module.__name__:
                    try:
                        function_info = self.inspect_function(obj)
                        functions.append(function_info)
                    except:
                        pass
                elif inspect.isclass(obj) and obj.__module__ == module.__name__:
                    try:
                        class_info = self.inspect_class(obj)
                        classes.append(class_info)
                    except:
                        pass
                elif not name.startswith('_') and not inspect.ismodule(obj) and not inspect.isfunction(obj) and not inspect.isclass(obj):
                    variables.append(name)
            
            # Analyze dependencies
            dependencies = self._analyze_module_dependencies(module)
            
            return ModuleInfo(
                name=module.__name__,
                file_path=filename,
                imports=imports,
                functions=functions,
                classes=classes,
                variables=variables,
                docstring=docstring,
                size_bytes=size_bytes,
                dependencies=dependencies,
                reverse_dependencies=[]  # Would need global analysis
            )
        except Exception as e:
            logger.error(f"Error inspecting module {module.__name__}: {e}")
            return ModuleInfo(
                name=module.__name__,
                file_path='unknown',
                imports=[],
                functions=[],
                classes=[],
                variables=[],
                docstring=None,
                size_bytes=0,
                dependencies=[],
                reverse_dependencies=[]
            )
    
    def build_dependency_graph(self, modules: List[types.ModuleType]) -> DependencyGraph:
        """Build dependency graph for modules"""
        nodes = set()
        edges = []
        
        # Build graph
        for module in modules:
            module_info = self.inspect_module(module)
            nodes.add(module_info.name)
            
            for dependency in module_info.dependencies:
                edges.append((module_info.name, dependency))
                nodes.add(dependency)
        
        # Find circular dependencies
        circular_deps = self._find_circular_dependencies(nodes, edges)
        
        # Calculate depth levels
        depth_levels = self._calculate_depth_levels(nodes, edges)
        
        return DependencyGraph(
            nodes=nodes,
            edges=edges,
            circular_dependencies=circular_deps,
            depth_levels=depth_levels
        )
    
    def analyze_code_quality(self, obj: Any) -> Dict[str, Any]:
        """Analyze code quality metrics"""
        analysis = {
            'complexity_score': 0,
            'maintainability_score': 0,
            'test_coverage': 0,
            'documentation_score': 0,
            'issues': [],
            'recommendations': []
        }
        
        try:
            if inspect.isfunction(obj):
                func_info = self.inspect_function(obj)
                metrics = self._complexity_analyzer.analyze_function(obj)
                
                analysis['complexity_score'] = metrics.cyclomatic_complexity
                analysis['maintainability_score'] = metrics.maintainability_index
                analysis['documentation_score'] = 100 if func_info.docstring else 0
                
                # Add issues and recommendations
                if metrics.cyclomatic_complexity > 10:
                    analysis['issues'].append("High cyclomatic complexity")
                    analysis['recommendations'].append("Consider breaking function into smaller parts")
                
                if metrics.technical_debt_ratio > 0.5:
                    analysis['issues'].append("High technical debt")
                    analysis['recommendations'].append("Refactor to reduce complexity")
                
                if not func_info.docstring:
                    analysis['issues'].append("Missing documentation")
                    analysis['recommendations'].append("Add docstring with description and parameters")
            
            elif inspect.isclass(obj):
                class_info = self.inspect_class(obj)
                
                # Calculate average method complexity
                total_complexity = sum(method.complexity for method in class_info.methods)
                avg_complexity = total_complexity / len(class_info.methods) if class_info.methods else 0
                
                analysis['complexity_score'] = avg_complexity
                analysis['documentation_score'] = 100 if class_info.docstring else 0
                
                # Class-specific issues
                if len(class_info.methods) > 20:
                    analysis['issues'].append("Large class with many methods")
                    analysis['recommendations'].append("Consider splitting class responsibilities")
                
                if not class_info.docstring:
                    analysis['issues'].append("Missing class documentation")
                    analysis['recommendations'].append("Add class docstring")
        
        except Exception as e:
            logger.error(f"Error analyzing code quality: {e}")
        
        return analysis
    
    def _extract_function_calls(self, source_code: str) -> List[str]:
        """Extract function calls from source code"""
        calls = []
        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        calls.append(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        calls.append(node.func.attr)
        except:
            pass
        return calls
    
    def _analyze_module_dependencies(self, module: types.ModuleType) -> List[str]:
        """Analyze module dependencies"""
        dependencies = []
        try:
            if hasattr(module, '__file__') and module.__file__:
                with open(module.__file__, 'r') as f:
                    source = f.read()
                    tree = ast.parse(source)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                dependencies.append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                dependencies.append(node.module)
        except:
            pass
        return dependencies
    
    def _find_circular_dependencies(self, nodes: Set[str], edges: List[Tuple[str, str]]) -> List[List[str]]:
        """Find circular dependencies using DFS"""
        graph = defaultdict(list)
        for src, dst in edges:
            graph[src].append(dst)
        
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:])
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph[node]:
                dfs(neighbor, path.copy())
            
            rec_stack.remove(node)
        
        for node in nodes:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def _calculate_depth_levels(self, nodes: Set[str], edges: List[Tuple[str, str]]) -> Dict[str, int]:
        """Calculate dependency depth levels"""
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        for src, dst in edges:
            graph[src].append(dst)
            in_degree[dst] += 1
        
        # Initialize all nodes
        for node in nodes:
            if node not in in_degree:
                in_degree[node] = 0
        
        # Topological sort to find levels
        queue = deque([node for node in nodes if in_degree[node] == 0])
        levels = {}
        current_level = 0
        
        while queue:
            level_size = len(queue)
            for _ in range(level_size):
                node = queue.popleft()
                levels[node] = current_level
                
                for neighbor in graph[node]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
            
            current_level += 1
        
        return levels


class FrameworkInspector:
    """Gary-Zero framework specific inspector"""
    
    def __init__(self):
        self._code_inspector = CodeInspector()
    
    def inspect_framework_structure(self) -> Dict[str, Any]:
        """Inspect Gary-Zero framework structure"""
        try:
            framework_modules = []
            
            # Find all framework modules
            for name, module in sys.modules.items():
                if name.startswith('framework.') or name == 'framework':
                    framework_modules.append(module)
            
            # Build dependency graph
            dep_graph = self._code_inspector.build_dependency_graph(framework_modules)
            
            # Analyze modules
            module_analysis = {}
            for module in framework_modules:
                module_info = self._code_inspector.inspect_module(module)
                module_analysis[module_info.name] = {
                    'functions': len(module_info.functions),
                    'classes': len(module_info.classes),
                    'size_kb': module_info.size_bytes / 1024,
                    'dependencies': len(module_info.dependencies)
                }
            
            return {
                'total_modules': len(framework_modules),
                'dependency_graph': {
                    'nodes': len(dep_graph.nodes),
                    'edges': len(dep_graph.edges),
                    'circular_dependencies': len(dep_graph.circular_dependencies)
                },
                'module_analysis': module_analysis,
                'architecture_metrics': self._calculate_architecture_metrics(dep_graph)
            }
        except Exception as e:
            logger.error(f"Error inspecting framework structure: {e}")
            return {}
    
    def _calculate_architecture_metrics(self, dep_graph: DependencyGraph) -> Dict[str, float]:
        """Calculate architecture quality metrics"""
        if not dep_graph.nodes:
            return {}
        
        # Coupling metrics
        total_dependencies = len(dep_graph.edges)
        avg_coupling = total_dependencies / len(dep_graph.nodes)
        
        # Cohesion metric (simplified)
        max_depth = max(dep_graph.depth_levels.values()) if dep_graph.depth_levels else 0
        cohesion_score = 1.0 / (max_depth + 1)
        
        # Stability metric
        circular_deps_ratio = len(dep_graph.circular_dependencies) / len(dep_graph.nodes)
        stability_score = 1.0 - circular_deps_ratio
        
        return {
            'average_coupling': avg_coupling,
            'cohesion_score': cohesion_score,
            'stability_score': stability_score,
            'complexity_score': avg_coupling * (1.0 - cohesion_score)
        }


class RuntimeInspector:
    """Runtime state and behavior inspector"""
    
    def __init__(self):
        self._snapshots: List[Dict[str, Any]] = []
    
    def take_runtime_snapshot(self) -> Dict[str, Any]:
        """Take snapshot of runtime state"""
        snapshot = {
            'timestamp': str(datetime.now()),
            'memory_objects': self._count_objects_by_type(),
            'garbage_collection': self._get_gc_stats(),
            'thread_info': self._get_thread_info(),
            'module_info': self._get_loaded_modules(),
            'stack_frames': self._get_stack_info()
        }
        
        self._snapshots.append(snapshot)
        return snapshot
    
    def compare_snapshots(self, snapshot1: Dict, snapshot2: Dict) -> Dict[str, Any]:
        """Compare two runtime snapshots"""
        comparison = {
            'memory_changes': {},
            'new_objects': {},
            'removed_objects': {},
            'module_changes': []
        }
        
        # Compare memory objects
        objects1 = snapshot1.get('memory_objects', {})
        objects2 = snapshot2.get('memory_objects', {})
        
        for obj_type in set(objects1.keys()) | set(objects2.keys()):
            count1 = objects1.get(obj_type, 0)
            count2 = objects2.get(obj_type, 0)
            if count1 != count2:
                comparison['memory_changes'][obj_type] = count2 - count1
        
        return comparison
    
    def _count_objects_by_type(self) -> Dict[str, int]:
        """Count objects by type"""
        counts = defaultdict(int)
        for obj in gc.get_objects():
            counts[type(obj).__name__] += 1
        return dict(counts)
    
    def _get_gc_stats(self) -> Dict[str, Any]:
        """Get garbage collection statistics"""
        return {
            'collections': gc.get_stats(),
            'counts': gc.get_count(),
            'threshold': gc.get_threshold()
        }
    
    def _get_thread_info(self) -> Dict[str, Any]:
        """Get thread information"""
        import threading
        return {
            'active_threads': threading.active_count(),
            'current_thread': threading.current_thread().name,
            'threads': [t.name for t in threading.enumerate()]
        }
    
    def _get_loaded_modules(self) -> Dict[str, Any]:
        """Get loaded module information"""
        return {
            'total_modules': len(sys.modules),
            'framework_modules': [name for name in sys.modules.keys() if 'framework' in name],
            'builtin_modules': [name for name in sys.modules.keys() if name in sys.builtin_module_names]
        }
    
    def _get_stack_info(self) -> List[Dict[str, Any]]:
        """Get current stack information"""
        stack_info = []
        frame = sys._getframe()
        
        while frame:
            stack_info.append({
                'filename': frame.f_code.co_filename,
                'function': frame.f_code.co_name,
                'line_number': frame.f_lineno,
                'locals_count': len(frame.f_locals)
            })
            frame = frame.f_back
            
            # Limit stack depth for performance
            if len(stack_info) > 20:
                break
        
        return stack_info


# Global inspector instances
_code_inspector = CodeInspector()
_framework_inspector = FrameworkInspector()
_runtime_inspector = RuntimeInspector()

# Convenience functions
def inspect_function(func: types.FunctionType) -> FunctionInfo:
    """Inspect a function"""
    return _code_inspector.inspect_function(func)

def inspect_class(cls: type) -> ClassInfo:
    """Inspect a class"""
    return _code_inspector.inspect_class(cls)

def inspect_module(module: types.ModuleType) -> ModuleInfo:
    """Inspect a module"""
    return _code_inspector.inspect_module(module)

def analyze_code_quality(obj: Any) -> Dict[str, Any]:
    """Analyze code quality"""
    return _code_inspector.analyze_code_quality(obj)

def inspect_framework() -> Dict[str, Any]:
    """Inspect framework structure"""
    return _framework_inspector.inspect_framework_structure()

def take_runtime_snapshot() -> Dict[str, Any]:
    """Take runtime snapshot"""
    return _runtime_inspector.take_runtime_snapshot()