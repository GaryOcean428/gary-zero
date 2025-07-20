"""
E2B-based secure code execution for Gary Zero agent.
"""
import os
import time
from typing import Dict, Any, Optional

from .base_executor import BaseCodeExecutor


class E2BCodeExecutor(BaseCodeExecutor):
    """Secure code execution using E2B cloud sandboxes."""
    
    def __init__(self):
        super().__init__()
        # Check if E2B is available
        if not os.getenv('E2B_API_KEY'):
            raise ValueError("E2B_API_KEY environment variable is required")
        
        # Import E2B here to avoid import errors if not available
        try:
            from e2b_code_interpreter import Sandbox
            self.Sandbox = Sandbox
        except ImportError:
            raise ImportError("e2b-code-interpreter package not installed. Run: pip install e2b-code-interpreter")
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new E2B sandbox session."""
        if session_id is None:
            session_id = self._generate_session_id()
            
        if session_id in self.sessions:
            return session_id
            
        try:
            # Create new E2B sandbox
            sandbox = self.Sandbox()
            
            self.sessions[session_id] = sandbox
            self.session_metadata[session_id] = self._create_session_metadata(session_id)
            
            print(f"✅ Created E2B session: {session_id}")
            return session_id
            
        except Exception as e:
            print(f"❌ Failed to create E2B session: {e}")
            raise
    
    def execute_code(self, session_id: str, code: str, language: str = "python") -> Dict[str, Any]:
        """Execute code in the specified E2B session."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
            
        sandbox = self.sessions[session_id]
        
        try:
            start_time = time.time()
            
            if language.lower() == "python":
                # Execute Python code using E2B
                execution = sandbox.run_code(code)
                
                # Update session metadata
                self.session_metadata[session_id]["execution_count"] += 1
                
                return {
                    "success": True,
                    "stdout": execution.text or "",
                    "stderr": execution.error or "",
                    "results": getattr(execution, 'results', []),  # Rich outputs (charts, tables, etc.)
                    "execution_time": time.time() - start_time,
                    "logs": {
                        "stdout": getattr(execution.logs, 'stdout', []) if hasattr(execution, 'logs') else [],
                        "stderr": getattr(execution.logs, 'stderr', []) if hasattr(execution, 'logs') else []
                    }
                }
                
            elif language.lower() in ["bash", "shell", "sh"]:
                # Execute shell commands
                execution = sandbox.run_code(f"!{code}")  # Use ! prefix for shell commands
                
                return {
                    "success": True,
                    "stdout": execution.text or "",
                    "stderr": execution.error or "",
                    "execution_time": time.time() - start_time,
                    "logs": {
                        "stdout": getattr(execution.logs, 'stdout', []) if hasattr(execution, 'logs') else [],
                        "stderr": getattr(execution.logs, 'stderr', []) if hasattr(execution, 'logs') else []
                    }
                }
            else:
                raise ValueError(f"Unsupported language: {language}")
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": "",
                "execution_time": time.time() - start_time if 'start_time' in locals() else 0
            }
    
    def upload_file(self, session_id: str, file_path: str, content: bytes) -> Dict[str, Any]:
        """Upload a file to the E2B sandbox."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
            
        sandbox = self.sessions[session_id]
        
        try:
            # Write file to sandbox
            with sandbox.filesystem.write(file_path, content) as f:
                pass
                
            return {
                "success": True,
                "file_path": file_path,
                "size": len(content)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def download_file(self, session_id: str, file_path: str) -> Dict[str, Any]:
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
                "size": len(content)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_files(self, session_id: str, directory: str = ".") -> Dict[str, Any]:
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
            
            return {
                "success": True,
                "files": files,
                "directory": directory
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse file list: {e}",
                "raw_output": result
            }
    
    def close_session(self, session_id: str):
        """Close and cleanup E2B session."""
        if session_id in self.sessions:
            try:
                sandbox = self.sessions[session_id]
                sandbox.close()
                print(f"✅ Closed E2B session: {session_id}")
            except Exception as e:
                print(f"⚠️  Error closing E2B session {session_id}: {e}")
            finally:
                del self.sessions[session_id]
                if session_id in self.session_metadata:
                    del self.session_metadata[session_id]
    
    def __del__(self):
        """Cleanup sessions on destruction."""
        try:
            self.cleanup_all()
        except:
            pass  # Ignore cleanup errors during destruction