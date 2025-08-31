"""
E2B-based secure code execution for Gary Zero agent.
Enhanced with connection monitoring, session management, and performance tracking.
"""

import os
import time
from datetime import UTC, datetime
from typing import Any

from .base_executor import BaseCodeExecutor


class E2BCodeExecutor(BaseCodeExecutor):
    """Secure code execution using E2B cloud sandboxes with enhanced management."""

    def __init__(self):
        super().__init__()
        # Check if E2B is available
        if not os.getenv("E2B_API_KEY"):
            raise ValueError("E2B_API_KEY environment variable is required")

        # Import E2B here to avoid import errors if not available
        try:
            from e2b_code_interpreter import Sandbox

            self.Sandbox = Sandbox
        except ImportError:
            raise ImportError(
                "e2b-code-interpreter package not installed. Run: pip install e2b-code-interpreter"
            )

        # Enhanced tracking
        self.connection_stats = {
            "total_sessions": 0,
            "active_sessions": 0,
            "total_executions": 0,
            "failed_connections": 0,
            "last_connection_test": None,
        }
        self.session_health = {}  # Track health of each session

    def test_connection(self) -> dict[str, Any]:
        """Test E2B connection and return status."""
        try:
            # Create a temporary sandbox to test connection
            test_sandbox = self.Sandbox()

            # Run a simple test
            test_result = test_sandbox.run_code("print('E2B connection test')")

            # Close test sandbox
            test_sandbox.close()

            self.connection_stats["last_connection_test"] = datetime.now(UTC)

            return {
                "success": True,
                "message": "E2B connection successful",
                "test_output": test_result.text,
                "timestamp": self.connection_stats["last_connection_test"],
            }

        except Exception as e:
            self.connection_stats["failed_connections"] += 1
            return {"success": False, "error": str(e), "timestamp": datetime.now(UTC)}

    def create_session(self, session_id: str | None = None) -> str:
        """Create a new E2B sandbox session with enhanced tracking."""
        if session_id is None:
            session_id = self._generate_session_id()

        if session_id in self.sessions:
            return session_id

        try:
            # Create new E2B sandbox
            sandbox = self.Sandbox()

            self.sessions[session_id] = sandbox
            self.session_metadata[session_id] = self._create_session_metadata(
                session_id
            )

            # Initialize session health tracking
            self.session_health[session_id] = {
                "created_at": datetime.now(UTC),
                "last_used": datetime.now(UTC),
                "execution_count": 0,
                "error_count": 0,
                "status": "active",
            }

            # Update statistics
            self.connection_stats["total_sessions"] += 1
            self.connection_stats["active_sessions"] += 1

            print(f"✅ Created E2B session: {session_id}")
            return session_id

        except Exception as e:
            self.connection_stats["failed_connections"] += 1
            print(f"❌ Failed to create E2B session: {e}")
            raise

    def execute_code(
        self, session_id: str, code: str, language: str = "python"
    ) -> dict[str, Any]:
        """Execute code in the specified E2B session with enhanced monitoring."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        sandbox = self.sessions[session_id]

        try:
            start_time = time.time()

            # Update session health
            if session_id in self.session_health:
                self.session_health[session_id]["last_used"] = datetime.now(UTC)
                self.session_health[session_id]["execution_count"] += 1

            if language.lower() == "python":
                # Execute Python code using E2B
                execution = sandbox.run_code(code)

                # Update session metadata
                self.session_metadata[session_id]["execution_count"] += 1
                self.connection_stats["total_executions"] += 1

                result = {
                    "success": True,
                    "stdout": execution.text or "",
                    "stderr": execution.error or "",
                    "results": getattr(
                        execution, "results", []
                    ),  # Rich outputs (charts, tables, etc.)
                    "execution_time": time.time() - start_time,
                    "logs": {
                        "stdout": (
                            getattr(execution.logs, "stdout", [])
                            if hasattr(execution, "logs")
                            else []
                        ),
                        "stderr": (
                            getattr(execution.logs, "stderr", [])
                            if hasattr(execution, "logs")
                            else []
                        ),
                    },
                    "session_id": session_id,
                    "language": language,
                }

                # Check for errors and update health
                if execution.error:
                    self.session_health[session_id]["error_count"] += 1

                return result

            elif language.lower() in ["bash", "shell", "sh"]:
                # Execute shell commands
                execution = sandbox.run_code(
                    f"!{code}"
                )  # Use ! prefix for shell commands

                self.connection_stats["total_executions"] += 1

                result = {
                    "success": True,
                    "stdout": execution.text or "",
                    "stderr": execution.error or "",
                    "execution_time": time.time() - start_time,
                    "logs": {
                        "stdout": (
                            getattr(execution.logs, "stdout", [])
                            if hasattr(execution, "logs")
                            else []
                        ),
                        "stderr": (
                            getattr(execution.logs, "stderr", [])
                            if hasattr(execution, "logs")
                            else []
                        ),
                    },
                    "session_id": session_id,
                    "language": language,
                }

                if execution.error:
                    self.session_health[session_id]["error_count"] += 1

                return result
            else:
                raise ValueError(f"Unsupported language: {language}")

        except Exception as e:
            # Update error tracking
            if session_id in self.session_health:
                self.session_health[session_id]["error_count"] += 1

            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": "",
                "execution_time": (
                    time.time() - start_time if "start_time" in locals() else 0
                ),
                "session_id": session_id,
                "language": language,
            }

    def upload_file(
        self, session_id: str, file_path: str, content: bytes
    ) -> dict[str, Any]:
        """Upload a file to the E2B sandbox."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        sandbox = self.sessions[session_id]

        try:
            # Write file to sandbox
            with sandbox.filesystem.write(file_path, content) as f:
                pass

            return {"success": True, "file_path": file_path, "size": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def download_file(self, session_id: str, file_path: str) -> dict[str, Any]:
        """Download a file from the E2B sandbox."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        sandbox = self.sessions[session_id]

        try:
            # Read file from sandbox
            content = sandbox.filesystem.read(file_path)

            return {
                "success": True,
                "file_path": file_path,
                "content": content,
                "size": len(content),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_files(self, session_id: str, directory: str = ".") -> dict[str, Any]:
        """List files in the E2B sandbox directory."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        list_code = f"""
import os
files = []
for item in os.listdir('{directory}'):
    full_path = os.path.join('{directory}', item)
    is_dir = os.path.isdir(full_path)
    size = os.path.getsize(full_path) if not is_dir else 0
    files.append({{'name': item, 'is_directory': is_dir, 'size': size}})
print(files)
"""

        result = self.execute_code(session_id, list_code, "python")

        try:
            # Parse the output to get file list
            import ast

            files = ast.literal_eval(result["stdout"].strip())

            return {"success": True, "files": files, "directory": directory}
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse file list: {e}",
                "raw_output": result,
            }

    def get_session_health(self, session_id: str) -> dict[str, Any]:
        """Get health status of a specific session."""
        if session_id not in self.session_health:
            return {"error": "Session not found"}

        health = self.session_health[session_id].copy()

        # Calculate additional metrics
        if health["execution_count"] > 0:
            health["error_rate"] = health["error_count"] / health["execution_count"]
        else:
            health["error_rate"] = 0.0

        # Check if session is stale (no activity for 30+ minutes)
        time_since_last_use = datetime.now(UTC) - health["last_used"]
        health["minutes_since_last_use"] = time_since_last_use.total_seconds() / 60
        health["is_stale"] = health["minutes_since_last_use"] > 30

        return health

    def get_connection_stats(self) -> dict[str, Any]:
        """Get overall E2B connection statistics."""
        stats = self.connection_stats.copy()

        # Add calculated metrics
        if stats["total_sessions"] > 0:
            stats["failure_rate"] = (
                stats["failed_connections"] / stats["total_sessions"]
            )
        else:
            stats["failure_rate"] = 0.0

        # Add session health summary
        healthy_sessions = 0
        stale_sessions = 0

        for session_id in self.session_health:
            health = self.get_session_health(session_id)
            if health.get("error_rate", 0) < 0.1 and not health.get("is_stale", False):
                healthy_sessions += 1
            elif health.get("is_stale", False):
                stale_sessions += 1

        stats["healthy_sessions"] = healthy_sessions
        stats["stale_sessions"] = stale_sessions

        return stats

    def cleanup_stale_sessions(self) -> dict[str, Any]:
        """Clean up sessions that haven't been used recently."""
        stale_sessions = []
        cleaned_count = 0

        for session_id in list(self.session_health.keys()):
            health = self.get_session_health(session_id)
            if health.get("is_stale", False):
                stale_sessions.append(session_id)
                try:
                    self.close_session(session_id)
                    cleaned_count += 1
                except Exception as e:
                    print(f"Failed to clean up stale session {session_id}: {e}")

        return {
            "stale_sessions_found": len(stale_sessions),
            "cleaned_sessions": cleaned_count,
            "session_ids": stale_sessions,
        }

    def close_session(self, session_id: str):
        """Close and cleanup E2B session with enhanced tracking."""
        if session_id in self.sessions:
            try:
                sandbox = self.sessions[session_id]
                sandbox.close()
                print(f"✅ Closed E2B session: {session_id}")

                # Update statistics
                self.connection_stats["active_sessions"] -= 1

            except Exception as e:
                print(f"⚠️  Error closing E2B session {session_id}: {e}")
            finally:
                del self.sessions[session_id]
                if session_id in self.session_metadata:
                    del self.session_metadata[session_id]
                if session_id in self.session_health:
                    del self.session_health[session_id]

    def __del__(self):
        """Cleanup sessions on destruction."""
        try:
            self.cleanup_all()
        except:
            pass  # Ignore cleanup errors during destruction
