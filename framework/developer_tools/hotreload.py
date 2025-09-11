"""
Hot Reload Module

Provides hot reloading capabilities for rapid development with automatic
file watching and module reloading.
"""

import asyncio
import importlib
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False


class FileWatcher:
    """File system watcher for detecting changes"""
    
    def __init__(self):
        self._observers: List[Any] = []
        self._handlers: Dict[str, Any] = {}
        self._watching = False
    
    def watch_directory(self, path: str, callback: Callable[[str], None], 
                       patterns: Optional[List[str]] = None, recursive: bool = True):
        """Watch a directory for changes"""
        if not HAS_WATCHDOG:
            logger.warning("Watchdog not available, file watching disabled")
            return
        
        class ChangeHandler(FileSystemEventHandler):
            def __init__(self, callback_func, file_patterns=None):
                self.callback = callback_func
                self.patterns = file_patterns or ['*.py']
                super().__init__()
            
            def on_modified(self, event):
                if not event.is_directory:
                    file_path = event.src_path
                    
                    # Check if file matches patterns
                    if self._matches_patterns(file_path, self.patterns):
                        logger.info(f"File changed: {file_path}")
                        self.callback(file_path)
            
            def _matches_patterns(self, file_path: str, patterns: List[str]) -> bool:
                """Check if file matches any pattern"""
                for pattern in patterns:
                    if file_path.endswith(pattern.replace('*', '')):
                        return True
                return False
        
        handler = ChangeHandler(callback, patterns)
        observer = Observer()
        observer.schedule(handler, path, recursive=recursive)
        
        self._handlers[path] = handler
        self._observers.append(observer)
        
        if not self._watching:
            self.start_watching()
    
    def start_watching(self):
        """Start file watching"""
        if not HAS_WATCHDOG or self._watching:
            return
        
        for observer in self._observers:
            observer.start()
        
        self._watching = True
        logger.info("Started file watching")
    
    def stop_watching(self):
        """Stop file watching"""
        if not self._watching:
            return
        
        for observer in self._observers:
            observer.stop()
            observer.join()
        
        self._observers.clear()
        self._handlers.clear()
        self._watching = False
        logger.info("Stopped file watching")


class ModuleReloader:
    """Handles module reloading"""
    
    def __init__(self):
        self._loaded_modules: Dict[str, float] = {}  # module_name -> last_modified_time
        self._reload_callbacks: Dict[str, List[Callable]] = {}
        self._dependencies: Dict[str, Set[str]] = {}  # module -> dependent modules
    
    def register_module(self, module_name: str, callback: Optional[Callable] = None):
        """Register a module for hot reloading"""
        if module_name in sys.modules:
            module = sys.modules[module_name]
            if hasattr(module, '__file__') and module.__file__:
                file_path = module.__file__
                if file_path.endswith('.pyc'):
                    file_path = file_path[:-1]  # Convert .pyc to .py
                
                if os.path.exists(file_path):
                    self._loaded_modules[module_name] = os.path.getmtime(file_path)
                    
                    if callback:
                        if module_name not in self._reload_callbacks:
                            self._reload_callbacks[module_name] = []
                        self._reload_callbacks[module_name].append(callback)
                    
                    logger.info(f"Registered module for reloading: {module_name}")
    
    def reload_module(self, module_name: str) -> bool:
        """Reload a specific module"""
        if module_name not in sys.modules:
            logger.warning(f"Module {module_name} not in sys.modules")
            return False
        
        try:
            # Get the module
            module = sys.modules[module_name]
            
            # Reload dependencies first
            if module_name in self._dependencies:
                for dep in self._dependencies[module_name]:
                    self.reload_module(dep)
            
            # Reload the module
            importlib.reload(module)
            
            # Update last modified time
            if hasattr(module, '__file__') and module.__file__:
                file_path = module.__file__
                if file_path.endswith('.pyc'):
                    file_path = file_path[:-1]
                
                if os.path.exists(file_path):
                    self._loaded_modules[module_name] = os.path.getmtime(file_path)
            
            # Execute callbacks
            if module_name in self._reload_callbacks:
                for callback in self._reload_callbacks[module_name]:
                    try:
                        callback(module)
                    except Exception as e:
                        logger.error(f"Error in reload callback for {module_name}: {e}")
            
            logger.info(f"Successfully reloaded module: {module_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload module {module_name}: {e}")
            return False
    
    def reload_from_file(self, file_path: str) -> bool:
        """Reload module based on file path"""
        # Convert file path to module name
        module_name = self._file_path_to_module_name(file_path)
        if module_name:
            return self.reload_module(module_name)
        return False
    
    def check_for_changes(self) -> List[str]:
        """Check for module changes and return list of changed modules"""
        changed_modules = []
        
        for module_name, last_modified in self._loaded_modules.items():
            if module_name in sys.modules:
                module = sys.modules[module_name]
                if hasattr(module, '__file__') and module.__file__:
                    file_path = module.__file__
                    if file_path.endswith('.pyc'):
                        file_path = file_path[:-1]
                    
                    if os.path.exists(file_path):
                        current_modified = os.path.getmtime(file_path)
                        if current_modified > last_modified:
                            changed_modules.append(module_name)
        
        return changed_modules
    
    def _file_path_to_module_name(self, file_path: str) -> Optional[str]:
        """Convert file path to module name"""
        if not file_path.endswith('.py'):
            return None
        
        # Try to find matching module in sys.modules
        abs_file_path = os.path.abspath(file_path)
        
        for module_name, module in sys.modules.items():
            if hasattr(module, '__file__') and module.__file__:
                module_file = module.__file__
                if module_file.endswith('.pyc'):
                    module_file = module_file[:-1]
                
                if os.path.abspath(module_file) == abs_file_path:
                    return module_name
        
        return None


class AutoReloader:
    """Automatic reloader with file watching"""
    
    def __init__(self):
        self._file_watcher = FileWatcher()
        self._module_reloader = ModuleReloader()
        self._watch_paths: List[str] = []
        self._enabled = False
        self._reload_delay = 0.5  # Delay to batch file changes
        self._pending_reloads: Set[str] = set()
        self._reload_timer: Optional[threading.Timer] = None
    
    def enable(self, watch_paths: Optional[List[str]] = None, 
               patterns: Optional[List[str]] = None):
        """Enable automatic reloading"""
        if self._enabled:
            return
        
        if watch_paths is None:
            # Default to current working directory and common Python paths
            watch_paths = [
                os.getcwd(),
                *[p for p in sys.path if os.path.isdir(p) and not p.endswith('site-packages')]
            ]
        
        self._watch_paths = watch_paths
        
        # Setup file watching
        for path in watch_paths:
            self._file_watcher.watch_directory(
                path, 
                self._on_file_changed,
                patterns or ['*.py'],
                recursive=True
            )
        
        # Register existing modules
        for module_name in sys.modules:
            if not module_name.startswith('_') and '.' in module_name:
                self._module_reloader.register_module(module_name)
        
        self._enabled = True
        logger.info(f"Enabled auto-reloading for paths: {watch_paths}")
    
    def disable(self):
        """Disable automatic reloading"""
        if not self._enabled:
            return
        
        self._file_watcher.stop_watching()
        
        if self._reload_timer:
            self._reload_timer.cancel()
        
        self._enabled = False
        self._pending_reloads.clear()
        logger.info("Disabled auto-reloading")
    
    def add_reload_callback(self, module_name: str, callback: Callable):
        """Add callback for module reload"""
        self._module_reloader.register_module(module_name, callback)
    
    def _on_file_changed(self, file_path: str):
        """Handle file change event"""
        if not self._enabled:
            return
        
        # Add to pending reloads
        self._pending_reloads.add(file_path)
        
        # Cancel existing timer
        if self._reload_timer:
            self._reload_timer.cancel()
        
        # Start new timer to batch changes
        self._reload_timer = threading.Timer(self._reload_delay, self._process_pending_reloads)
        self._reload_timer.start()
    
    def _process_pending_reloads(self):
        """Process pending reload requests"""
        if not self._pending_reloads:
            return
        
        reloaded_modules = []
        
        for file_path in self._pending_reloads:
            try:
                if self._module_reloader.reload_from_file(file_path):
                    module_name = self._module_reloader._file_path_to_module_name(file_path)
                    if module_name:
                        reloaded_modules.append(module_name)
            except Exception as e:
                logger.error(f"Error reloading {file_path}: {e}")
        
        if reloaded_modules:
            logger.info(f"Auto-reloaded modules: {', '.join(reloaded_modules)}")
        
        self._pending_reloads.clear()


class HotReloadManager:
    """Main hot reload manager"""
    
    def __init__(self):
        self._auto_reloader = AutoReloader()
        self._development_mode = False
        self._reload_hooks: List[Callable] = []
    
    def enable_development_mode(self, watch_paths: Optional[List[str]] = None):
        """Enable development mode with hot reloading"""
        if self._development_mode:
            return
        
        self._development_mode = True
        self._auto_reloader.enable(watch_paths)
        
        logger.info("Enabled development mode with hot reloading")
    
    def disable_development_mode(self):
        """Disable development mode"""
        if not self._development_mode:
            return
        
        self._development_mode = False
        self._auto_reloader.disable()
        
        logger.info("Disabled development mode")
    
    def add_reload_hook(self, hook: Callable):
        """Add hook to be called after any module reload"""
        self._reload_hooks.append(hook)
    
    def manually_reload_module(self, module_name: str) -> bool:
        """Manually reload a specific module"""
        success = self._auto_reloader._module_reloader.reload_module(module_name)
        
        if success:
            # Execute reload hooks
            for hook in self._reload_hooks:
                try:
                    hook(module_name)
                except Exception as e:
                    logger.error(f"Error in reload hook: {e}")
        
        return success
    
    def get_status(self) -> Dict[str, Any]:
        """Get hot reload status"""
        return {
            'development_mode': self._development_mode,
            'watching_paths': self._auto_reloader._watch_paths if self._development_mode else [],
            'registered_modules': len(self._auto_reloader._module_reloader._loaded_modules),
            'reload_hooks': len(self._reload_hooks)
        }


# Decorators for hot reload support
def hot_reloadable(func: Callable) -> Callable:
    """Decorator to make a function hot-reloadable"""
    def wrapper(*args, **kwargs):
        # Check if module needs reloading
        module_name = func.__module__
        manager = _global_manager
        
        if manager._development_mode:
            # Check for changes and reload if necessary
            changed = manager._auto_reloader._module_reloader.check_for_changes()
            if module_name in changed:
                manager._auto_reloader._module_reloader.reload_module(module_name)
        
        return func(*args, **kwargs)
    
    return wrapper


def reload_on_change(module_name: str):
    """Decorator to reload module when file changes"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Register module for watching
            _global_manager._auto_reloader._module_reloader.register_module(module_name)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Global manager instance
_global_manager = HotReloadManager()

# Convenience functions
def enable_hot_reload(watch_paths: Optional[List[str]] = None):
    """Enable hot reload for development"""
    _global_manager.enable_development_mode(watch_paths)

def disable_hot_reload():
    """Disable hot reload"""
    _global_manager.disable_development_mode()

def reload_module(module_name: str) -> bool:
    """Manually reload a module"""
    return _global_manager.manually_reload_module(module_name)

def add_reload_hook(hook: Callable):
    """Add hook for module reloads"""
    _global_manager.add_reload_hook(hook)

def get_reload_status() -> Dict[str, Any]:
    """Get hot reload status"""
    return _global_manager.get_status()


# Context manager for temporary hot reload
class hot_reload_context:
    """Context manager for temporary hot reload activation"""
    
    def __init__(self, watch_paths: Optional[List[str]] = None):
        self.watch_paths = watch_paths
        self.was_enabled = False
    
    def __enter__(self):
        self.was_enabled = _global_manager._development_mode
        if not self.was_enabled:
            enable_hot_reload(self.watch_paths)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.was_enabled:
            disable_hot_reload()


# FastAPI integration
try:
    from fastapi import FastAPI
    
    def setup_fastapi_hot_reload(app: FastAPI, watch_paths: Optional[List[str]] = None):
        """Setup hot reload for FastAPI application"""
        
        @app.on_event("startup")
        async def startup_event():
            enable_hot_reload(watch_paths)
            logger.info("Hot reload enabled for FastAPI app")
        
        @app.on_event("shutdown")
        async def shutdown_event():
            disable_hot_reload()
            logger.info("Hot reload disabled for FastAPI app")
        
        # Add reload endpoint for manual reloading
        @app.post("/dev/reload/{module_name}")
        async def manual_reload(module_name: str):
            success = reload_module(module_name)
            return {"success": success, "module": module_name}
        
        @app.get("/dev/reload/status")
        async def reload_status():
            return get_reload_status()

except ImportError:
    pass  # FastAPI not available