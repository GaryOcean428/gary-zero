"""
Base class for secure code executors.
"""
import time
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseCodeExecutor(ABC):
    """Base class for secure code execution environments."""
    
    def __init__(self):
        self.sessions: Dict[str, Any] = {}
        self.session_metadata: Dict[str, Dict[str, Any]] = {}
    
    @abstractmethod
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new execution session."""
        pass
    
    @abstractmethod
    def execute_code(self, session_id: str, code: str, language: str = "python") -> Dict[str, Any]:
        """Execute code in the specified session."""
        pass
    
    @abstractmethod
    def close_session(self, session_id: str):
        """Close and cleanup session."""
        pass
    
    def install_package(self, session_id: str, package: str) -> Dict[str, Any]:
        """Install a package in the session. Default implementation using pip."""
        install_code = f"import subprocess; subprocess.run(['pip', 'install', '{package}'], check=True, capture_output=True, text=True)"
        return self.execute_code(session_id, install_code, "python")
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get information about the session."""
        if session_id not in self.session_metadata:
            return {"error": "Session not found"}
            
        metadata = self.session_metadata[session_id].copy()
        metadata["session_id"] = session_id
        metadata["uptime"] = time.time() - metadata.get("created_at", time.time())
        
        return metadata
    
    def cleanup_all(self):
        """Cleanup all sessions."""
        for session_id in list(self.sessions.keys()):
            self.close_session(session_id)
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return str(uuid.uuid4())
    
    def _create_session_metadata(self, session_id: str) -> Dict[str, Any]:
        """Create initial session metadata."""
        return {
            "created_at": time.time(),
            "execution_count": 0,
            "package_installs": []
        }