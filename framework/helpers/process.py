"""Process management for the application.

This module provides backward compatibility for code that imports directly from process.
New code should use ProcessManager from process_manager.py instead.
"""

from .process_manager import process_manager as _process_manager

# Backward compatibility functions
set_server = _process_manager.set_server
get_server = _process_manager.get_server
stop_server = _process_manager.stop_server
reload = _process_manager.reload
restart_process = _process_manager.restart_process
exit_process = _process_manager.exit_process
