"""
Interactive REPL Module

Provides an advanced interactive shell and REPL environment for Gary-Zero framework
with enhanced development capabilities, code completion, and introspection.
"""

import asyncio
import code
import inspect
import readline
import sys
import traceback
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union
import logging

from .inspector import inspect_function, inspect_class, inspect_module, analyze_code_quality
from .profiler import PerformanceProfiler
from .debugger import AdvancedDebugger

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Result of a REPL command execution"""
    success: bool
    result: Any
    output: str
    error: Optional[str]
    execution_time: float
    timestamp: datetime


@dataclass
class REPLSession:
    """REPL session information"""
    session_id: str
    start_time: datetime
    commands_executed: int
    variables: Dict[str, Any]
    history: List[str]
    last_result: Any


class CommandProcessor:
    """Processes special REPL commands"""
    
    def __init__(self, repl_instance):
        self.repl = repl_instance
        self._commands = {
            'help': self._help,
            'exit': self._exit,
            'quit': self._exit,
            'clear': self._clear,
            'history': self._history,
            'vars': self._vars,
            'inspect': self._inspect,
            'profile': self._profile,
            'debug': self._debug,
            'load': self._load,
            'save': self._save,
            'reset': self._reset,
            'time': self._time,
            'source': self._source,
            'doc': self._doc,
            'type': self._type,
            'methods': self._methods,
            'attrs': self._attrs,
            'framework': self._framework,
            'benchmark': self._benchmark,
            'memory': self._memory,
            'gc': self._gc
        }
    
    def is_command(self, line: str) -> bool:
        """Check if line is a special command"""
        return line.strip().startswith('%')
    
    def execute_command(self, line: str) -> CommandResult:
        """Execute a special command"""
        start_time = time.time()
        
        try:
            # Parse command
            parts = line.strip()[1:].split()
            if not parts:
                return CommandResult(
                    success=False,
                    result=None,
                    output="",
                    error="Empty command",
                    execution_time=0,
                    timestamp=datetime.now()
                )
            
            cmd_name = parts[0]
            args = parts[1:] if len(parts) > 1 else []
            
            if cmd_name not in self._commands:
                return CommandResult(
                    success=False,
                    result=None,
                    output="",
                    error=f"Unknown command: {cmd_name}",
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            # Execute command
            result = self._commands[cmd_name](args)
            
            return CommandResult(
                success=True,
                result=result,
                output=str(result) if result is not None else "",
                error=None,
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                result=None,
                output="",
                error=str(e),
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    def _help(self, args: List[str]) -> str:
        """Show help information"""
        if args:
            # Show specific command help
            cmd = args[0]
            if cmd in self._commands:
                return f"Help for %{cmd}: {self._commands[cmd].__doc__}"
            else:
                return f"Unknown command: {cmd}"
        
        # Show all commands
        help_text = """
Gary-Zero Interactive REPL Commands:

%help [command]     - Show help (this message)
%exit, %quit        - Exit the REPL
%clear              - Clear screen
%history            - Show command history
%vars               - Show current variables
%inspect <obj>      - Inspect object details
%profile <code>     - Profile code execution
%debug <code>       - Debug code execution
%load <file>        - Load and execute Python file
%save <file>        - Save current session to file
%reset              - Reset session variables
%time <code>        - Time code execution
%source <obj>       - Show source code
%doc <obj>          - Show documentation
%type <obj>         - Show object type information
%methods <obj>      - Show object methods
%attrs <obj>        - Show object attributes
%framework          - Show framework information
%benchmark <code>   - Run performance benchmark
%memory             - Show memory usage
%gc                 - Run garbage collection

Examples:
  %inspect myfunction
  %profile "sum(range(1000))"
  %time "x = [i**2 for i in range(1000)]"
        """
        return help_text.strip()
    
    def _exit(self, args: List[str]) -> None:
        """Exit the REPL"""
        self.repl._running = False
        return "Goodbye!"
    
    def _clear(self, args: List[str]) -> str:
        """Clear the screen"""
        import os
        os.system('clear' if os.name == 'posix' else 'cls')
        return "Screen cleared"
    
    def _history(self, args: List[str]) -> str:
        """Show command history"""
        if not self.repl.session.history:
            return "No command history"
        
        limit = 20
        if args and args[0].isdigit():
            limit = int(args[0])
        
        history = self.repl.session.history[-limit:]
        result = "Command History:\n"
        for i, cmd in enumerate(history, 1):
            result += f"{i:3d}: {cmd}\n"
        return result.rstrip()
    
    def _vars(self, args: List[str]) -> str:
        """Show current variables"""
        variables = self.repl.session.variables
        if not variables:
            return "No user variables defined"
        
        result = "Current Variables:\n"
        for name, value in variables.items():
            if not name.startswith('_'):
                value_str = repr(value)
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."
                result += f"  {name:15} = {value_str}\n"
        return result.rstrip()
    
    def _inspect(self, args: List[str]) -> str:
        """Inspect object details"""
        if not args:
            return "Usage: %inspect <object_name>"
        
        obj_name = args[0]
        if obj_name not in self.repl.session.variables:
            return f"Object '{obj_name}' not found"
        
        obj = self.repl.session.variables[obj_name]
        
        try:
            if inspect.isfunction(obj):
                info = inspect_function(obj)
                result = f"Function: {info.name}\n"
                result += f"Module: {info.module}\n"
                result += f"File: {info.file_path}:{info.line_number}\n"
                result += f"Arguments: {', '.join(info.arguments)}\n"
                result += f"Async: {info.is_async}\n"
                result += f"Complexity: {info.complexity}\n"
                if info.docstring:
                    result += f"Docstring: {info.docstring[:100]}...\n"
                return result
            
            elif inspect.isclass(obj):
                info = inspect_class(obj)
                result = f"Class: {info.name}\n"
                result += f"Module: {info.module}\n"
                result += f"Base classes: {', '.join(info.base_classes)}\n"
                result += f"Methods: {len(info.methods)}\n"
                result += f"Attributes: {len(info.attributes)}\n"
                if info.docstring:
                    result += f"Docstring: {info.docstring[:100]}...\n"
                return result
            
            else:
                result = f"Object: {obj_name}\n"
                result += f"Type: {type(obj).__name__}\n"
                result += f"Value: {repr(obj)}\n"
                if hasattr(obj, '__doc__') and obj.__doc__:
                    result += f"Docstring: {obj.__doc__[:100]}...\n"
                return result
                
        except Exception as e:
            return f"Error inspecting object: {e}"
    
    def _profile(self, args: List[str]) -> str:
        """Profile code execution"""
        if not args:
            return "Usage: %profile <code>"
        
        code_str = ' '.join(args)
        
        try:
            profiler = PerformanceProfiler()
            with profiler.profile_context() as session_id:
                exec(code_str, self.repl.session.variables)
            
            session = profiler.get_session(session_id)
            if session and session.profile_stats:
                result = f"Profiling Results (Duration: {session.duration:.4f}s):\n"
                result += f"Total functions: {len(session.profile_stats)}\n"
                result += "Top functions by time:\n"
                
                sorted_stats = sorted(session.profile_stats, key=lambda x: x.cumulative_time, reverse=True)
                for stat in sorted_stats[:5]:
                    result += f"  {stat.function_name}: {stat.cumulative_time:.4f}s ({stat.percentage:.1f}%)\n"
                
                return result
            else:
                return "No profiling data collected"
                
        except Exception as e:
            return f"Error profiling code: {e}"
    
    def _debug(self, args: List[str]) -> str:
        """Debug code execution"""
        if not args:
            return "Usage: %debug <code>"
        
        code_str = ' '.join(args)
        
        try:
            debugger = AdvancedDebugger()
            with debugger.debug_context() as session_id:
                exec(code_str, self.repl.session.variables)
            
            return f"Debug session {session_id} completed"
            
        except Exception as e:
            return f"Error debugging code: {e}"
    
    def _load(self, args: List[str]) -> str:
        """Load and execute Python file"""
        if not args:
            return "Usage: %load <filename>"
        
        filename = args[0]
        
        try:
            with open(filename, 'r') as f:
                code_str = f.read()
            
            exec(code_str, self.repl.session.variables)
            return f"Successfully loaded and executed {filename}"
            
        except FileNotFoundError:
            return f"File not found: {filename}"
        except Exception as e:
            return f"Error loading file: {e}"
    
    def _save(self, args: List[str]) -> str:
        """Save current session to file"""
        if not args:
            return "Usage: %save <filename>"
        
        filename = args[0]
        
        try:
            with open(filename, 'w') as f:
                f.write("# Gary-Zero REPL Session\n")
                f.write(f"# Saved at {datetime.now()}\n\n")
                
                # Save variables
                for name, value in self.repl.session.variables.items():
                    if not name.startswith('_'):
                        try:
                            f.write(f"{name} = {repr(value)}\n")
                        except:
                            f.write(f"# Could not serialize {name}\n")
                
                # Save history as comments
                f.write("\n# Command History:\n")
                for cmd in self.repl.session.history:
                    f.write(f"# {cmd}\n")
            
            return f"Session saved to {filename}"
            
        except Exception as e:
            return f"Error saving session: {e}"
    
    def _reset(self, args: List[str]) -> str:
        """Reset session variables"""
        # Keep builtin variables
        builtins = ['__builtins__', '__name__', '__doc__']
        to_keep = {k: v for k, v in self.repl.session.variables.items() if k in builtins}
        
        self.repl.session.variables.clear()
        self.repl.session.variables.update(to_keep)
        
        return "Session variables reset"
    
    def _time(self, args: List[str]) -> str:
        """Time code execution"""
        if not args:
            return "Usage: %time <code>"
        
        code_str = ' '.join(args)
        
        try:
            import time
            start_time = time.time()
            result = eval(code_str, self.repl.session.variables)
            end_time = time.time()
            
            execution_time = end_time - start_time
            return f"Result: {result}\nExecution time: {execution_time:.6f} seconds"
            
        except Exception as e:
            return f"Error timing code: {e}"
    
    def _source(self, args: List[str]) -> str:
        """Show source code"""
        if not args:
            return "Usage: %source <object_name>"
        
        obj_name = args[0]
        if obj_name not in self.repl.session.variables:
            return f"Object '{obj_name}' not found"
        
        obj = self.repl.session.variables[obj_name]
        
        try:
            source = inspect.getsource(obj)
            return f"Source code for {obj_name}:\n{source}"
        except Exception as e:
            return f"Could not get source code: {e}"
    
    def _doc(self, args: List[str]) -> str:
        """Show documentation"""
        if not args:
            return "Usage: %doc <object_name>"
        
        obj_name = args[0]
        if obj_name not in self.repl.session.variables:
            return f"Object '{obj_name}' not found"
        
        obj = self.repl.session.variables[obj_name]
        doc = inspect.getdoc(obj)
        
        if doc:
            return f"Documentation for {obj_name}:\n{doc}"
        else:
            return f"No documentation available for {obj_name}"
    
    def _type(self, args: List[str]) -> str:
        """Show object type information"""
        if not args:
            return "Usage: %type <object_name>"
        
        obj_name = args[0]
        if obj_name not in self.repl.session.variables:
            return f"Object '{obj_name}' not found"
        
        obj = self.repl.session.variables[obj_name]
        
        result = f"Type information for {obj_name}:\n"
        result += f"Type: {type(obj)}\n"
        result += f"MRO: {[cls.__name__ for cls in type(obj).__mro__]}\n"
        result += f"Module: {getattr(type(obj), '__module__', 'unknown')}\n"
        
        return result
    
    def _methods(self, args: List[str]) -> str:
        """Show object methods"""
        if not args:
            return "Usage: %methods <object_name>"
        
        obj_name = args[0]
        if obj_name not in self.repl.session.variables:
            return f"Object '{obj_name}' not found"
        
        obj = self.repl.session.variables[obj_name]
        methods = [name for name, value in inspect.getmembers(obj, inspect.ismethod)]
        
        if methods:
            return f"Methods for {obj_name}:\n" + '\n'.join(f"  {method}" for method in methods)
        else:
            return f"No methods found for {obj_name}"
    
    def _attrs(self, args: List[str]) -> str:
        """Show object attributes"""
        if not args:
            return "Usage: %attrs <object_name>"
        
        obj_name = args[0]
        if obj_name not in self.repl.session.variables:
            return f"Object '{obj_name}' not found"
        
        obj = self.repl.session.variables[obj_name]
        attrs = [name for name in dir(obj) if not name.startswith('_')]
        
        if attrs:
            return f"Attributes for {obj_name}:\n" + '\n'.join(f"  {attr}" for attr in attrs)
        else:
            return f"No public attributes found for {obj_name}"
    
    def _framework(self, args: List[str]) -> str:
        """Show framework information"""
        try:
            from .inspector import inspect_framework
            info = inspect_framework()
            
            result = "Gary-Zero Framework Information:\n"
            result += f"Total modules: {info.get('total_modules', 0)}\n"
            
            dep_graph = info.get('dependency_graph', {})
            result += f"Dependency graph: {dep_graph.get('nodes', 0)} nodes, {dep_graph.get('edges', 0)} edges\n"
            result += f"Circular dependencies: {dep_graph.get('circular_dependencies', 0)}\n"
            
            arch_metrics = info.get('architecture_metrics', {})
            if arch_metrics:
                result += f"Average coupling: {arch_metrics.get('average_coupling', 0):.2f}\n"
                result += f"Stability score: {arch_metrics.get('stability_score', 0):.2f}\n"
            
            return result
            
        except Exception as e:
            return f"Error getting framework information: {e}"
    
    def _benchmark(self, args: List[str]) -> str:
        """Run performance benchmark"""
        if not args:
            return "Usage: %benchmark <code>"
        
        code_str = ' '.join(args)
        
        try:
            import timeit
            
            # Run benchmark
            times = timeit.repeat(
                stmt=code_str,
                globals=self.repl.session.variables,
                repeat=5,
                number=1000
            )
            
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            result = f"Benchmark Results (1000 iterations, 5 repeats):\n"
            result += f"Average: {avg_time:.6f}s\n"
            result += f"Min: {min_time:.6f}s\n"
            result += f"Max: {max_time:.6f}s\n"
            result += f"Per iteration: {avg_time/1000:.9f}s\n"
            
            return result
            
        except Exception as e:
            return f"Error running benchmark: {e}"
    
    def _memory(self, args: List[str]) -> str:
        """Show memory usage"""
        try:
            try:
                import psutil
                process = psutil.Process()
                memory_info = process.memory_info()
                
                result = "Memory Usage:\n"
                result += f"RSS: {memory_info.rss / 1024 / 1024:.2f} MB\n"
                result += f"VMS: {memory_info.vms / 1024 / 1024:.2f} MB\n"
                result += f"Memory percent: {process.memory_percent():.2f}%\n"
            except ImportError:
                result = "Memory Usage:\n"
                result += "psutil not available - limited memory info\n"
            
            # Garbage collection stats
            import gc
            gc_stats = gc.get_stats()
            result += f"GC collections: {gc_stats}\n"
            result += f"GC objects: {len(gc.get_objects())}\n"
            
            return result
            
        except Exception as e:
            return f"Error getting memory information: {e}"
    
    def _gc(self, args: List[str]) -> str:
        """Run garbage collection"""
        try:
            import gc
            
            before = len(gc.get_objects())
            collected = gc.collect()
            after = len(gc.get_objects())
            
            result = f"Garbage Collection:\n"
            result += f"Objects before: {before}\n"
            result += f"Objects after: {after}\n"
            result += f"Objects collected: {collected}\n"
            result += f"Objects freed: {before - after}\n"
            
            return result
            
        except Exception as e:
            return f"Error running garbage collection: {e}"


class InteractiveShell(code.InteractiveConsole):
    """Enhanced interactive shell with advanced features"""
    
    def __init__(self, locals=None, filename="<console>"):
        super().__init__(locals, filename)
        self.session = REPLSession(
            session_id=f"repl_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            start_time=datetime.now(),
            commands_executed=0,
            variables=self.locals,
            history=[],
            last_result=None
        )
        
        self.command_processor = CommandProcessor(self)
        self._running = True
        self._setup_completion()
    
    def _setup_completion(self):
        """Setup tab completion"""
        try:
            import rlcompleter
            readline.set_completer(rlcompleter.Completer(self.locals).complete)
            readline.parse_and_bind("tab: complete")
            
            # Enable history
            try:
                readline.read_history_file()
            except FileNotFoundError:
                pass
            
        except ImportError:
            pass  # readline not available
    
    def runsource(self, source, filename="<input>", symbol="single"):
        """Execute source in the interpreter"""
        # Add to history
        if source.strip():
            self.session.history.append(source)
        
        # Check for special commands
        if self.command_processor.is_command(source):
            result = self.command_processor.execute_command(source)
            if result.success:
                if result.output:
                    print(result.output)
                self.session.last_result = result.result
            else:
                print(f"Error: {result.error}")
            return False  # Complete command
        
        # Execute normal Python code
        try:
            self.session.commands_executed += 1
            
            # Compile and execute
            compiled = self.compile(source, filename, symbol)
            if compiled is None:
                return True  # More input needed
            
            # Execute with result capture
            if symbol == "single":
                # Capture expression results
                try:
                    result = eval(compiled, self.locals)
                    if result is not None:
                        self.session.last_result = result
                        print(repr(result))
                except SyntaxError:
                    # Not an expression, execute as statement
                    exec(compiled, self.locals)
            else:
                exec(compiled, self.locals)
            
            return False  # Complete command
            
        except (OverflowError, SyntaxError, ValueError):
            # Let the base class handle these
            return super().runsource(source, filename, symbol)
        except SystemExit:
            raise
        except:
            # Print traceback
            self.showtraceback()
            return False  # Complete command
    
    def interact(self, banner=None, exitmsg=None):
        """Enhanced interaction with custom banner"""
        if banner is None:
            banner = f"""
Gary-Zero Interactive Development Environment
Python {sys.version} on {sys.platform}
Session: {self.session.session_id}

Type '%help' for available commands, 'exit()' or Ctrl-D to exit.
"""
        
        if exitmsg is None:
            exitmsg = "Exiting Gary-Zero REPL..."
        
        # Save original ps1/ps2
        old_ps1 = getattr(sys, 'ps1', '>>> ')
        old_ps2 = getattr(sys, 'ps2', '... ')
        
        # Set custom prompts
        sys.ps1 = 'gary-zero>>> '
        sys.ps2 = 'gary-zero... '
        
        try:
            super().interact(banner, exitmsg)
        finally:
            # Restore prompts
            sys.ps1 = old_ps1
            sys.ps2 = old_ps2
            
            # Save history
            try:
                readline.write_history_file()
            except:
                pass


class DeveloperREPL:
    """Main REPL interface with advanced development features"""
    
    def __init__(self, initial_locals=None):
        self._shell = None
        self._initial_locals = initial_locals or {}
        self._profiler = PerformanceProfiler()
        self._debugger = AdvancedDebugger()
    
    def start(self, banner=None):
        """Start the interactive REPL"""
        # Setup initial namespace
        namespace = {
            '__name__': '__console__',
            '__doc__': None,
            # Add framework utilities
            'inspect_function': inspect_function,
            'inspect_class': inspect_class,
            'inspect_module': inspect_module,
            'analyze_code_quality': analyze_code_quality,
            'profiler': self._profiler,
            'debugger': self._debugger,
        }
        namespace.update(self._initial_locals)
        
        # Create and start shell
        self._shell = InteractiveShell(locals=namespace)
        
        try:
            self._shell.interact(banner=banner)
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt")
        except EOFError:
            print("\nEOF")
        finally:
            self._cleanup()
    
    def execute_code(self, code: str, capture_output: bool = True) -> CommandResult:
        """Execute code and return result"""
        if not self._shell:
            namespace = {'__name__': '__console__', '__doc__': None}
            namespace.update(self._initial_locals)
            self._shell = InteractiveShell(locals=namespace)
        
        start_time = time.time()
        
        try:
            if capture_output:
                # Capture stdout
                from io import StringIO
                old_stdout = sys.stdout
                sys.stdout = StringIO()
                
                try:
                    # Execute code
                    if self._shell.command_processor.is_command(code):
                        result = self._shell.command_processor.execute_command(code)
                        return result
                    else:
                        # Execute as Python code
                        exec(code, self._shell.locals)
                        output = sys.stdout.getvalue()
                        
                        return CommandResult(
                            success=True,
                            result=self._shell.session.last_result,
                            output=output,
                            error=None,
                            execution_time=time.time() - start_time,
                            timestamp=datetime.now()
                        )
                finally:
                    sys.stdout = old_stdout
            else:
                # Execute without capture
                exec(code, self._shell.locals)
                
                return CommandResult(
                    success=True,
                    result=self._shell.session.last_result,
                    output="",
                    error=None,
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            return CommandResult(
                success=False,
                result=None,
                output="",
                error=str(e),
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    def get_session_info(self) -> Optional[REPLSession]:
        """Get current session information"""
        return self._shell.session if self._shell else None
    
    def _cleanup(self):
        """Cleanup resources"""
        if self._shell:
            print(f"\nSession summary:")
            print(f"Commands executed: {self._shell.session.commands_executed}")
            print(f"Duration: {datetime.now() - self._shell.session.start_time}")
            print(f"Variables defined: {len([k for k in self._shell.session.variables.keys() if not k.startswith('_')])}")


# Async REPL support
class AsyncREPL:
    """Async-aware REPL for asynchronous development"""
    
    def __init__(self):
        self._loop = None
        self._repl = DeveloperREPL()
    
    async def start_async(self):
        """Start async REPL"""
        self._loop = asyncio.get_event_loop()
        
        # Add async utilities to namespace
        async_namespace = {
            'asyncio': asyncio,
            'await_result': self._await_result,
            'run_async': self._run_async
        }
        
        self._repl._initial_locals.update(async_namespace)
        self._repl.start()
    
    async def _await_result(self, coro):
        """Await a coroutine in the REPL"""
        if self._loop:
            return await coro
        else:
            return await coro
    
    def _run_async(self, coro):
        """Run async code synchronously"""
        if self._loop:
            return self._loop.run_until_complete(coro)
        else:
            return asyncio.run(coro)


# Global REPL instance
_global_repl = DeveloperREPL()

# Convenience functions
def start_repl(initial_locals=None, banner=None):
    """Start the Gary-Zero REPL"""
    repl = DeveloperREPL(initial_locals)
    repl.start(banner)

def execute_repl_code(code: str, capture_output: bool = True) -> CommandResult:
    """Execute code in global REPL"""
    return _global_repl.execute_code(code, capture_output)

async def start_async_repl():
    """Start async REPL"""
    async_repl = AsyncREPL()
    await async_repl.start_async()

# Import time for timing functions
import time