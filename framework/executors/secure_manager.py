"""
Secure Code Execution Manager for Gary Zero agent.
Intelligently chooses between E2B, Docker, and fallback execution.
"""
import os
from typing import Any


class SecureCodeExecutionManager:
    """Manager that chooses the best available secure execution environment."""

    def __init__(self):
        self.executor = None
        self.executor_type = None
        self._initialize_executor()

    def _initialize_executor(self):
        """Initialize the best available executor."""
        # Try E2B first (production-ready, cloud sandbox)
        if self._try_e2b():
            return

        # Try Docker second (local development)
        if self._try_docker():
            return

        # If both fail, we'll use the existing local execution as fallback
        print("⚠️  Warning: No secure executor available. Using fallback to existing local execution.")
        self.executor_type = "fallback"

    def _try_e2b(self) -> bool:
        """Try to initialize E2B executor."""
        try:
            if not os.getenv('E2B_API_KEY'):
                print("💡 E2B_API_KEY not found - skipping E2B executor")
                return False

            from .e2b_executor import E2BCodeExecutor
            self.executor = E2BCodeExecutor()
            self.executor_type = "e2b"
            print("✅ Using E2B secure execution environment")
            return True
        except Exception as e:
            print(f"⚠️  E2B executor failed to initialize: {e}")
            return False

    def _try_docker(self) -> bool:
        """Try to initialize Docker executor."""
        try:
            from .docker_executor import DockerCodeExecutor
            self.executor = DockerCodeExecutor()
            self.executor_type = "docker"
            print("✅ Using Docker secure execution environment")
            return True
        except Exception as e:
            print(f"⚠️  Docker executor failed to initialize: {e}")
            return False

    def is_secure_execution_available(self) -> bool:
        """Check if secure execution is available."""
        return self.executor_type in ["e2b", "docker"]

    def get_executor_info(self) -> dict[str, str]:
        """Get information about the current executor."""
        return {
            "type": self.executor_type,
            "secure": str(self.executor_type in ["e2b", "docker"]),
            "description": {
                "e2b": "E2B Cloud Sandbox - Enterprise-grade isolation",
                "docker": "Docker Container - Local secure execution",
                "fallback": "Local execution - No isolation (security risk)"
            }.get(self.executor_type, "Unknown")
        }

    def create_session(self, session_id: str | None = None) -> str:
        """Create a new execution session."""
        if self.executor:
            return self.executor.create_session(session_id)
        else:
            # Fallback - generate session ID but no actual session
            import uuid
            return str(uuid.uuid4()) if session_id is None else session_id

    def execute_code(self, session_id: str, code: str, language: str = "python") -> dict[str, Any]:
        """Execute code in the specified session."""
        if self.executor:
            result = self.executor.execute_code(session_id, code, language)
            # Add executor type to result for debugging
            result["executor_type"] = self.executor_type
            return result
        else:
            # Fallback - return indication that secure execution is not available
            return {
                "success": False,
                "error": "Secure execution not available - would use local execution (not implemented in this secure version)",
                "executor_type": "fallback",
                "security_warning": "This would execute code directly on the host system without isolation"
            }

    def install_package(self, session_id: str, package: str) -> dict[str, Any]:
        """Install a package in the session."""
        if self.executor:
            result = self.executor.install_package(session_id, package)
            result["executor_type"] = self.executor_type
            return result
        else:
            return {
                "success": False,
                "error": "Secure execution not available for package installation",
                "executor_type": "fallback"
            }

    def get_session_info(self, session_id: str) -> dict[str, Any]:
        """Get information about the session."""
        if self.executor:
            info = self.executor.get_session_info(session_id)
            info["executor_type"] = self.executor_type
            return info
        else:
            return {
                "error": "Session not available",
                "executor_type": "fallback"
            }

    def close_session(self, session_id: str):
        """Close and cleanup session."""
        if self.executor:
            self.executor.close_session(session_id)

    def cleanup_all(self):
        """Cleanup all sessions."""
        if self.executor:
            self.executor.cleanup_all()

    # E2B-specific methods (only available if using E2B)
    def upload_file(self, session_id: str, file_path: str, content: bytes) -> dict[str, Any]:
        """Upload a file to the execution environment (E2B only)."""
        if self.executor_type == "e2b" and hasattr(self.executor, 'upload_file'):
            return self.executor.upload_file(session_id, file_path, content)
        else:
            return {
                "success": False,
                "error": f"File upload not supported in {self.executor_type} executor"
            }

    def download_file(self, session_id: str, file_path: str) -> dict[str, Any]:
        """Download a file from the execution environment (E2B only)."""
        if self.executor_type == "e2b" and hasattr(self.executor, 'download_file'):
            return self.executor.download_file(session_id, file_path)
        else:
            return {
                "success": False,
                "error": f"File download not supported in {self.executor_type} executor"
            }

    def list_files(self, session_id: str, directory: str = ".") -> dict[str, Any]:
        """List files in the execution environment (E2B only)."""
        if self.executor_type == "e2b" and hasattr(self.executor, 'list_files'):
            return self.executor.list_files(session_id, directory)
        else:
            return {
                "success": False,
                "error": f"File listing not supported in {self.executor_type} executor"
            }
