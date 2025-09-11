"""
Advanced Debugger Module

Provides sophisticated debugging capabilities for Gary-Zero framework including
interactive debugging, breakpoint management, and runtime inspection.
"""

import asyncio
import inspect
import pdb
import sys
import threading
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Union
import logging

logger = logging.getLogger(__name__)


@dataclass
class Breakpoint:
    """Represents a debugging breakpoint"""
    id: str
    file_path: str
    line_number: int
    condition: Optional[str] = None
    hit_count: int = 0
    enabled: bool = True
    temporary: bool = False
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DebugFrame:
    """Represents a stack frame during debugging"""
    filename: str
    function_name: str
    line_number: int
    locals: Dict[str, Any] = field(default_factory=dict)
    globals: Dict[str, Any] = field(default_factory=dict)
    code_context: Optional[List[str]] = None


@dataclass
class DebugSession:
    """Represents an active debugging session"""
    session_id: str
    start_time: datetime = field(default_factory=datetime.now)
    breakpoints: Dict[str, Breakpoint] = field(default_factory=dict)
    call_stack: List[DebugFrame] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    exception_info: Optional[Exception] = None
    active: bool = True


class BreakpointManager:
    """Manages debugging breakpoints"""
    
    def __init__(self):
        self._breakpoints: Dict[str, Breakpoint] = {}
        self._next_id = 1
        self._lock = threading.Lock()
    
    def add_breakpoint(
        self, 
        file_path: str, 
        line_number: int, 
        condition: Optional[str] = None,
        temporary: bool = False
    ) -> str:
        """Add a new breakpoint"""
        with self._lock:
            bp_id = f"bp_{self._next_id}"
            self._next_id += 1
            
            breakpoint = Breakpoint(
                id=bp_id,
                file_path=file_path,
                line_number=line_number,
                condition=condition,
                temporary=temporary
            )
            
            self._breakpoints[bp_id] = breakpoint
            logger.info(f"Added breakpoint {bp_id} at {file_path}:{line_number}")
            return bp_id
    
    def remove_breakpoint(self, bp_id: str) -> bool:
        """Remove a breakpoint"""
        with self._lock:
            if bp_id in self._breakpoints:
                del self._breakpoints[bp_id]
                logger.info(f"Removed breakpoint {bp_id}")
                return True
            return False
    
    def enable_breakpoint(self, bp_id: str) -> bool:
        """Enable a breakpoint"""
        with self._lock:
            if bp_id in self._breakpoints:
                self._breakpoints[bp_id].enabled = True
                return True
            return False
    
    def disable_breakpoint(self, bp_id: str) -> bool:
        """Disable a breakpoint"""
        with self._lock:
            if bp_id in self._breakpoints:
                self._breakpoints[bp_id].enabled = False
                return True
            return False
    
    def get_breakpoints(self) -> List[Breakpoint]:
        """Get all breakpoints"""
        with self._lock:
            return list(self._breakpoints.values())
    
    def should_break(self, frame: Any) -> Optional[Breakpoint]:
        """Check if execution should break at current frame"""
        filename = frame.f_code.co_filename
        line_number = frame.f_lineno
        
        with self._lock:
            for bp in self._breakpoints.values():
                if (bp.enabled and 
                    bp.file_path in filename and 
                    bp.line_number == line_number):
                    
                    # Check condition if specified
                    if bp.condition:
                        try:
                            if not eval(bp.condition, frame.f_globals, frame.f_locals):
                                continue
                        except Exception as e:
                            logger.warning(f"Breakpoint condition error: {e}")
                            continue
                    
                    bp.hit_count += 1
                    
                    # Remove temporary breakpoint
                    if bp.temporary:
                        del self._breakpoints[bp.id]
                    
                    return bp
        
        return None


class AdvancedDebugger:
    """Advanced debugging system for Gary-Zero framework"""
    
    def __init__(self):
        self._sessions: Dict[str, DebugSession] = {}
        self._breakpoint_manager = BreakpointManager()
        self._active_session: Optional[str] = None
        self._original_trace_func = None
        self._debugging = False
        self._lock = threading.Lock()
    
    def start_session(self, session_id: Optional[str] = None) -> str:
        """Start a new debugging session"""
        if session_id is None:
            session_id = f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with self._lock:
            session = DebugSession(session_id=session_id)
            self._sessions[session_id] = session
            self._active_session = session_id
            
            logger.info(f"Started debugging session {session_id}")
            return session_id
    
    def stop_session(self, session_id: str) -> bool:
        """Stop a debugging session"""
        with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.active = False
                if hasattr(session, 'start_time'):
                    from datetime import datetime
                    session.duration = (datetime.now() - session.start_time).total_seconds()
                else:
                    session.duration = 0.0
                    
                if self._active_session == session_id:
                    self._active_session = None
                    self._stop_tracing()
                logger.info(f"Stopped debugging session {session_id}")
                return True
            return False
    
    def get_session(self, session_id: str) -> Optional[DebugSession]:
        """Get debugging session by ID"""
        return self._sessions.get(session_id)
    
    def get_active_session(self) -> Optional[DebugSession]:
        """Get currently active debugging session"""
        if self._active_session:
            return self._sessions.get(self._active_session)
        return None
    
    @contextmanager
    def debug_context(self, session_id: Optional[str] = None):
        """Context manager for debugging a code block"""
        session_id = self.start_session(session_id)
        try:
            self._start_tracing()
            yield session_id
        finally:
            self.stop_session(session_id)
    
    def add_breakpoint(
        self, 
        file_path: str, 
        line_number: int, 
        condition: Optional[str] = None,
        temporary: bool = False
    ) -> str:
        """Add a breakpoint"""
        return self._breakpoint_manager.add_breakpoint(
            file_path, line_number, condition, temporary
        )
    
    def remove_breakpoint(self, bp_id: str) -> bool:
        """Remove a breakpoint"""
        return self._breakpoint_manager.remove_breakpoint(bp_id)
    
    def get_breakpoints(self) -> List[Breakpoint]:
        """Get all breakpoints"""
        return self._breakpoint_manager.get_breakpoints()
    
    def step_into(self):
        """Step into next line of code"""
        if self._active_session:
            # Add temporary breakpoint at next line
            frame = sys._getframe(1)
            self.add_breakpoint(
                frame.f_code.co_filename,
                frame.f_lineno + 1,
                temporary=True
            )
    
    def step_over(self):
        """Step over current line"""
        if self._active_session:
            # Add temporary breakpoint after current function call
            frame = sys._getframe(1)
            self.add_breakpoint(
                frame.f_code.co_filename,
                frame.f_lineno + 1,
                temporary=True
            )
    
    def continue_execution(self):
        """Continue execution until next breakpoint"""
        pass  # Execution continues normally
    
    def inspect_variable(self, var_name: str, frame: Optional[Any] = None) -> Any:
        """Inspect a variable's value"""
        if frame is None:
            frame = sys._getframe(1)
        
        # Check locals first
        if var_name in frame.f_locals:
            return frame.f_locals[var_name]
        
        # Check globals
        if var_name in frame.f_globals:
            return frame.f_globals[var_name]
        
        raise NameError(f"Variable '{var_name}' not found")
    
    def get_call_stack(self, frame: Optional[Any] = None) -> List[DebugFrame]:
        """Get current call stack"""
        if frame is None:
            frame = sys._getframe(1)
        
        stack = []
        while frame:
            debug_frame = DebugFrame(
                filename=frame.f_code.co_filename,
                function_name=frame.f_code.co_name,
                line_number=frame.f_lineno,
                locals=dict(frame.f_locals),
                globals=dict(frame.f_globals)
            )
            stack.append(debug_frame)
            frame = frame.f_back
        
        return stack
    
    def _start_tracing(self):
        """Start execution tracing"""
        if not self._debugging:
            self._original_trace_func = sys.gettrace()
            sys.settrace(self._trace_function)
            self._debugging = True
            logger.info("Started execution tracing")
    
    def _stop_tracing(self):
        """Stop execution tracing"""
        if self._debugging:
            sys.settrace(self._original_trace_func)
            self._debugging = False
            logger.info("Stopped execution tracing")
    
    def _trace_function(self, frame, event, arg):
        """Trace function for debugging"""
        if event == 'line':
            # Check for breakpoints
            breakpoint = self._breakpoint_manager.should_break(frame)
            if breakpoint:
                session = self.get_active_session()
                if session:
                    # Update session with current state
                    session.call_stack = self.get_call_stack(frame)
                    session.variables = dict(frame.f_locals)
                    
                    logger.info(f"Hit breakpoint {breakpoint.id} at {breakpoint.file_path}:{breakpoint.line_number}")
                    
                    # Enter interactive debugger
                    self._enter_interactive_mode(frame, breakpoint)
        
        elif event == 'exception':
            session = self.get_active_session()
            if session:
                session.exception_info = arg
                logger.error(f"Exception in debug session: {arg}")
        
        return self._trace_function
    
    def _enter_interactive_mode(self, frame, breakpoint: Breakpoint):
        """Enter interactive debugging mode"""
        print(f"\n--- Gary-Zero Debugger ---")
        print(f"Breakpoint {breakpoint.id} hit at {breakpoint.file_path}:{breakpoint.line_number}")
        print(f"Function: {frame.f_code.co_name}")
        print(f"Hit count: {breakpoint.hit_count}")
        
        # Show code context
        try:
            with open(breakpoint.file_path, 'r') as f:
                lines = f.readlines()
                start = max(0, breakpoint.line_number - 3)
                end = min(len(lines), breakpoint.line_number + 2)
                
                print("\nCode context:")
                for i in range(start, end):
                    marker = ">>> " if i + 1 == breakpoint.line_number else "    "
                    print(f"{marker}{i + 1:4d}: {lines[i].rstrip()}")
        except Exception:
            pass
        
        # Interactive prompt
        print("\nDebugger commands:")
        print("  c/continue - continue execution")
        print("  s/step - step into next line")
        print("  n/next - step over current line")
        print("  l/locals - show local variables")
        print("  g/globals - show global variables")
        print("  bt/backtrace - show call stack")
        print("  q/quit - quit debugger")
        
        while True:
            try:
                cmd = input("(gary-debug) ").strip().lower()
                
                if cmd in ['c', 'continue']:
                    break
                elif cmd in ['s', 'step']:
                    self.step_into()
                    break
                elif cmd in ['n', 'next']:
                    self.step_over()
                    break
                elif cmd in ['l', 'locals']:
                    print("Local variables:")
                    for name, value in frame.f_locals.items():
                        print(f"  {name} = {repr(value)}")
                elif cmd in ['g', 'globals']:
                    print("Global variables:")
                    for name, value in frame.f_globals.items():
                        if not name.startswith('__'):
                            print(f"  {name} = {repr(value)}")
                elif cmd in ['bt', 'backtrace']:
                    stack = self.get_call_stack(frame)
                    print("Call stack:")
                    for i, debug_frame in enumerate(stack):
                        print(f"  {i}: {debug_frame.function_name} at {debug_frame.filename}:{debug_frame.line_number}")
                elif cmd in ['q', 'quit']:
                    if self._active_session:
                        self.stop_session(self._active_session)
                    break
                elif cmd.startswith('p '):
                    # Print variable
                    var_name = cmd[2:].strip()
                    try:
                        value = self.inspect_variable(var_name, frame)
                        print(f"{var_name} = {repr(value)}")
                    except NameError as e:
                        print(f"Error: {e}")
                else:
                    print("Unknown command. Type 'c' to continue.")
                    
            except KeyboardInterrupt:
                print("\nUse 'q' to quit debugger")
            except EOFError:
                break


# Debugging decorators and utilities
def debug_function(func: Callable) -> Callable:
    """Decorator to debug a specific function"""
    def wrapper(*args, **kwargs):
        debugger = AdvancedDebugger()
        with debugger.debug_context():
            # Add breakpoint at function entry
            debugger.add_breakpoint(
                func.__code__.co_filename,
                func.__code__.co_firstlineno,
                temporary=True
            )
            return func(*args, **kwargs)
    return wrapper


def breakpoint_here(condition: Optional[str] = None):
    """Add a programmatic breakpoint"""
    frame = sys._getframe(1)
    debugger = AdvancedDebugger()
    
    if not debugger.get_active_session():
        debugger.start_session()
    
    bp_id = debugger.add_breakpoint(
        frame.f_code.co_filename,
        frame.f_lineno,
        condition=condition,
        temporary=True
    )
    
    # Trigger the breakpoint
    debugger._start_tracing()


class RemoteDebugger:
    """Remote debugging capabilities"""
    
    def __init__(self, port: int = 5678):
        self.port = port
        self._server = None
        self._debugger = AdvancedDebugger()
    
    async def start_server(self):
        """Start remote debugging server"""
        # Implementation would include WebSocket or TCP server
        # for remote debugging connections
        logger.info(f"Remote debugger server started on port {self.port}")
    
    async def stop_server(self):
        """Stop remote debugging server"""
        if self._server:
            # Stop server implementation
            logger.info("Remote debugger server stopped")


# Global debugger instance
_global_debugger = AdvancedDebugger()

# Convenience functions
def start_debugging(session_id: Optional[str] = None) -> str:
    """Start a global debugging session"""
    return _global_debugger.start_session(session_id)

def stop_debugging(session_id: str) -> bool:
    """Stop a global debugging session"""
    return _global_debugger.stop_session(session_id)

def add_breakpoint(file_path: str, line_number: int, condition: Optional[str] = None) -> str:
    """Add a global breakpoint"""
    return _global_debugger.add_breakpoint(file_path, line_number, condition)

def remove_breakpoint(bp_id: str) -> bool:
    """Remove a global breakpoint"""
    return _global_debugger.remove_breakpoint(bp_id)