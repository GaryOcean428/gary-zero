"""Process management for the application.

This module provides a thread-safe way to manage the application process
and server instances without using global variables.
"""

from __future__ import annotations

import os
import sys
from typing import Any

from .print_style import PrintStyle
from .runtime import is_dockerized


class ProcessManager:
    """Manages the application process and server instances.

    This class provides a singleton instance that manages the application
    process lifecycle and server instances.
    """

    _instance: ProcessManager | None = None
    _server: Any = None

    def __new__(cls) -> ProcessManager:
        """Ensure only one instance of ProcessManager exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> ProcessManager:
        """Get the singleton instance of ProcessManager."""
        if cls._instance is None:
            cls._instance = ProcessManager()
        return cls._instance

    def set_server(self, server: Any) -> None:
        """Set the current server instance.

        Args:
            server: The server instance to manage.
        """
        self._server = server

    def get_server(self) -> Any:
        """Get the current server instance.

        Returns:
            The current server instance, or None if not set.
        """
        return self._server

    def stop_server(self) -> None:
        """Stop the current server if it's running."""
        if self._server:
            self._server.shutdown()
            self._server = None

    def reload(self) -> None:
        """Reload the application process."""
        self.stop_server()
        if is_dockerized():
            self.exit_process()
        else:
            self.restart_process()

    @staticmethod
    def restart_process() -> None:
        """Restart the current Python process."""
        PrintStyle.standard("Restarting process...")
        python = sys.executable
        os.execv(python, [python] + sys.argv)

    @staticmethod
    def exit_process() -> None:
        """Exit the current process."""
        PrintStyle.standard("Exiting process...")
        sys.exit(0)


# Global instance for backward compatibility
process_manager = ProcessManager()
