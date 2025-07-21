"""
Docker-based secure code execution for Gary Zero agent.
"""
import docker
import os
import time
import uuid
from typing import Dict, Any, Optional

from .base_executor import BaseCodeExecutor


class DockerCodeExecutor(BaseCodeExecutor):
    """Secure code execution using Docker containers."""
    
    def __init__(self, image_name: str = "python:3.13-slim", network_name: str = "gary-zero-net"):
        super().__init__()
        self.image_name = image_name
        self.network_name = network_name
        
        # Initialize Docker client
        try:
            self.client = docker.from_env()
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Docker: {e}")
        
        # Ensure network exists
        self._ensure_network()
        
        # Ensure image is available
        self._ensure_image()
    
    def _ensure_network(self):
        """Ensure the Docker network exists."""
        try:
            self.client.networks.get(self.network_name)
        except docker.errors.NotFound:
            try:
                self.client.networks.create(self.network_name, driver="bridge")
                print(f"✅ Created Docker network: {self.network_name}")
            except Exception as e:
                print(f"⚠️  Warning: Could not create network {self.network_name}: {e}")
    
    def _ensure_image(self):
        """Ensure the Docker image is available."""
        try:
            self.client.images.get(self.image_name)
        except docker.errors.ImageNotFound:
            try:
                print(f"📥 Pulling Docker image: {self.image_name}")
                self.client.images.pull(self.image_name)
                print(f"✅ Pulled Docker image: {self.image_name}")
            except Exception as e:
                print(f"❌ Failed to pull image {self.image_name}: {e}")
                raise
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new execution session with persistent container."""
        if session_id is None:
            session_id = self._generate_session_id()
            
        if session_id in self.sessions:
            return session_id
            
        try:
            # Create container with mounted workspace
            container = self.client.containers.run(
                self.image_name,
                command="python -c 'import time; time.sleep(86400)'",  # Keep container running
                detach=True,
                name=f"gary-zero-{session_id}",
                volumes={
                    f"gary-zero-workspace-{session_id}": {
                        'bind': '/workspace', 
                        'mode': 'rw'
                    }
                },
                environment={
                    'PYTHONPATH': '/workspace',
                    'SESSION_ID': session_id
                },
                mem_limit='512m',
                cpu_period=100000,
                cpu_quota=50000,  # 50% CPU limit
                remove=False,
                network=self.network_name,
                working_dir='/workspace'
            )
            
            # Wait a moment for container to start
            time.sleep(1)
            
            # Install common packages
            self._setup_container_environment(container)
            
            self.sessions[session_id] = container
            self.session_metadata[session_id] = self._create_session_metadata(session_id)
            
            print(f"✅ Created Docker session: {session_id}")
            return session_id
            
        except Exception as e:
            print(f"❌ Failed to create Docker session: {e}")
            raise
    
    def _setup_container_environment(self, container):
        """Setup the container environment with common packages."""
        try:
            # Update package list and install common tools
            setup_commands = [
                "apt-get update",
                "apt-get install -y build-essential curl git vim",
                "pip install --no-cache-dir numpy pandas matplotlib requests beautifulsoup4 ipython scikit-learn seaborn pillow"
            ]
            
            for cmd in setup_commands:
                exec_result = container.exec_run(cmd, user="root")
                if exec_result.exit_code != 0:
                    print(f"⚠️  Warning: Setup command failed: {cmd}")
                    
        except Exception as e:
            print(f"⚠️  Warning: Container setup failed: {e}")
    
    def execute_code(self, session_id: str, code: str, language: str = "python") -> Dict[str, Any]:
        """Execute code in the specified session."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
            
        container = self.sessions[session_id]
        
        try:
            # Ensure container is running
            container.reload()
            if container.status != 'running':
                container.start()
                time.sleep(1)  # Give container time to start
            
            if language.lower() == "python":
                return self._execute_python(container, code)
            elif language.lower() in ["bash", "shell", "sh"]:
                return self._execute_shell(container, code)
            else:
                raise ValueError(f"Unsupported language: {language}")
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": "",
                "execution_time": 0
            }
    
    def _execute_python(self, container, code: str) -> Dict[str, Any]:
        """Execute Python code in container."""
        # Write code to temporary file
        code_file = f"/workspace/temp/code_{uuid.uuid4().hex}.py"
        
        # Create temp directory if it doesn't exist
        container.exec_run("mkdir -p /workspace/temp", user="root")
        
        # Write code to file
        exec_result = container.exec_run(
            ["python", "-c", f"with open('{code_file}', 'w') as f: f.write({repr(code)})"],
            user="root"
        )
        
        if exec_result.exit_code != 0:
            return {
                "success": False,
                "error": f"Failed to write code: {exec_result.output.decode()}",
                "stdout": "",
                "stderr": "",
                "execution_time": 0
            }
        
        # Execute the code
        start_time = time.time()
        exec_result = container.exec_run(
            ["python", code_file],
            user="root",
            workdir="/workspace"
        )
        execution_time = time.time() - start_time
        
        # Clean up code file
        container.exec_run(["rm", "-f", code_file], user="root")
        
        output = exec_result.output.decode() if exec_result.output else ""
        
        return {
            "success": exec_result.exit_code == 0,
            "stdout": output,
            "stderr": "" if exec_result.exit_code == 0 else output,
            "execution_time": execution_time,
            "exit_code": exec_result.exit_code
        }
    
    def _execute_shell(self, container, command: str) -> Dict[str, Any]:
        """Execute shell command in container."""
        start_time = time.time()
        exec_result = container.exec_run(
            ["bash", "-c", command],
            user="root",
            workdir="/workspace"
        )
        execution_time = time.time() - start_time
        
        output = exec_result.output.decode() if exec_result.output else ""
        
        return {
            "success": exec_result.exit_code == 0,
            "stdout": output,
            "stderr": "" if exec_result.exit_code == 0 else output,
            "execution_time": execution_time,
            "exit_code": exec_result.exit_code
        }
    
    def close_session(self, session_id: str):
        """Close and cleanup session."""
        if session_id in self.sessions:
            container = self.sessions[session_id]
            try:
                container.stop()
                container.remove()
                
                # Clean up volume
                try:
                    volume_name = f"gary-zero-workspace-{session_id}"
                    volume = self.client.volumes.get(volume_name)
                    volume.remove()
                except docker.errors.NotFound:
                    pass  # Volume already removed
                
                print(f"✅ Closed Docker session: {session_id}")
            except Exception as e:
                print(f"⚠️  Error closing session {session_id}: {e}")
            finally:
                del self.sessions[session_id]
                if session_id in self.session_metadata:
                    del self.session_metadata[session_id]