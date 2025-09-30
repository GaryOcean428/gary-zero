"""
Advanced Sandbox Management for Gary-Zero
Integrated from AI-Manus project for secure task execution
"""

from typing import Optional, Dict, List, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
import asyncio
import logging
import json
import time
from pathlib import Path
from dataclasses import dataclass
import uuid

logger = logging.getLogger(__name__)


class SandboxStatus(str, Enum):
    """Sandbox status enumeration"""
    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    ERROR = "error"
    DESTROYED = "destroyed"


class SandboxType(str, Enum):
    """Sandbox type enumeration"""
    DOCKER = "docker"
    PODMAN = "podman"
    PROCESS = "process"
    VIRTUAL = "virtual"


@dataclass
class SandboxResource:
    """Sandbox resource limits"""
    cpu_limit: Optional[float] = None  # CPU cores
    memory_limit: Optional[str] = None  # e.g., "512m", "1g"
    disk_limit: Optional[str] = None   # e.g., "1g", "10g"
    network_enabled: bool = True
    gpu_enabled: bool = False


class SandboxConfig(BaseModel):
    """Sandbox configuration model"""
    name: str = Field(..., description="Unique sandbox name")
    image: str = Field(default="python:3.12-slim", description="Container image")
    sandbox_type: SandboxType = Field(default=SandboxType.DOCKER)
    resources: SandboxResource = Field(default_factory=SandboxResource)
    environment: Dict[str, str] = Field(default_factory=dict)
    volumes: Dict[str, str] = Field(default_factory=dict)  # host_path: container_path
    working_directory: str = Field(default="/workspace")
    auto_remove: bool = Field(default=True)
    timeout: Optional[int] = Field(default=3600, description="Timeout in seconds")
    
    class Config:
        extra = "allow"


class SandboxInfo(BaseModel):
    """Sandbox information model"""
    id: str
    name: str
    status: SandboxStatus
    created_at: float
    last_used: float
    config: SandboxConfig
    stats: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class TaskExecution(BaseModel):
    """Task execution tracking"""
    id: str
    sandbox_id: str
    command: str
    status: str
    start_time: float
    end_time: Optional[float] = None
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    working_dir: str = "/workspace"


class SandboxManager:
    """
    Advanced sandbox management system
    Adapted from AI-Manus for Gary-Zero integration
    """
    
    def __init__(self, 
                 default_image: str = "python:3.12-slim",
                 max_sandboxes: int = 10,
                 cleanup_interval: int = 300):
        self.default_image = default_image
        self.max_sandboxes = max_sandboxes
        self.cleanup_interval = cleanup_interval
        
        # Active sandboxes
        self.sandboxes: Dict[str, SandboxInfo] = {}
        self.executions: Dict[str, TaskExecution] = {}
        
        self.logger = logging.getLogger(__name__)
        
        # Start cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start the cleanup background task"""
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(self.cleanup_interval)
                    await self._cleanup_inactive_sandboxes()
                except Exception as e:
                    self.logger.error(f"Cleanup task error: {e}")
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
    
    async def create_sandbox(self, config: SandboxConfig) -> SandboxInfo:
        """Create a new sandbox"""
        try:
            # Check sandbox limits
            if len(self.sandboxes) >= self.max_sandboxes:
                # Remove oldest inactive sandbox
                await self._cleanup_oldest_sandbox()
            
            sandbox_id = str(uuid.uuid4())
            
            self.logger.info(f"Creating sandbox: {config.name} (ID: {sandbox_id})")
            
            # Simulate sandbox creation
            await asyncio.sleep(0.2)  # Simulate container startup time
            
            sandbox_info = SandboxInfo(
                id=sandbox_id,
                name=config.name,
                status=SandboxStatus.RUNNING,
                created_at=time.time(),
                last_used=time.time(),
                config=config
            )
            
            self.sandboxes[sandbox_id] = sandbox_info
            
            self.logger.info(f"Sandbox created successfully: {sandbox_id}")
            return sandbox_info
            
        except Exception as e:
            self.logger.error(f"Failed to create sandbox {config.name}: {e}")
            error_info = SandboxInfo(
                id="error",
                name=config.name,
                status=SandboxStatus.ERROR,
                created_at=time.time(),
                last_used=time.time(),
                config=config,
                error_message=str(e)
            )
            return error_info
    
    async def get_sandbox(self, sandbox_id: str) -> Optional[SandboxInfo]:
        """Get sandbox information"""
        sandbox = self.sandboxes.get(sandbox_id)
        if sandbox:
            sandbox.last_used = time.time()
        return sandbox
    
    async def list_sandboxes(self, status: Optional[SandboxStatus] = None) -> List[SandboxInfo]:
        """List sandboxes with optional status filter"""
        sandboxes = list(self.sandboxes.values())
        
        if status:
            sandboxes = [s for s in sandboxes if s.status == status]
        
        return sorted(sandboxes, key=lambda x: x.created_at, reverse=True)
    
    async def execute_command(self, 
                             sandbox_id: str, 
                             command: str,
                             working_dir: Optional[str] = None,
                             timeout: Optional[int] = None) -> TaskExecution:
        """Execute a command in a sandbox"""
        try:
            sandbox = await self.get_sandbox(sandbox_id)
            if not sandbox:
                raise ValueError(f"Sandbox {sandbox_id} not found")
            
            if sandbox.status != SandboxStatus.RUNNING:
                raise ValueError(f"Sandbox {sandbox_id} is not running (status: {sandbox.status})")
            
            execution_id = str(uuid.uuid4())
            work_dir = working_dir or sandbox.config.working_directory
            exec_timeout = timeout or sandbox.config.timeout or 60
            
            self.logger.info(f"Executing command in sandbox {sandbox_id}: {command}")
            
            execution = TaskExecution(
                id=execution_id,
                sandbox_id=sandbox_id,
                command=command,
                status="running",
                start_time=time.time(),
                working_dir=work_dir
            )
            
            self.executions[execution_id] = execution
            
            # Simulate command execution
            await asyncio.sleep(0.1)
            
            # Mock execution results
            if "error" in command.lower():
                execution.status = "failed"
                execution.exit_code = 1
                execution.stderr = f"Simulated error for command: {command}"
            else:
                execution.status = "completed"
                execution.exit_code = 0
                execution.stdout = f"Simulated output for: {command}"
            
            execution.end_time = time.time()
            
            self.logger.info(f"Command execution completed: {execution_id}")
            return execution
            
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            error_execution = TaskExecution(
                id=str(uuid.uuid4()),
                sandbox_id=sandbox_id,
                command=command,
                status="error",
                start_time=time.time(),
                end_time=time.time(),
                exit_code=-1,
                stderr=str(e),
                working_dir=working_dir or "/workspace"
            )
            return error_execution
    
    async def stop_sandbox(self, sandbox_id: str) -> bool:
        """Stop a sandbox"""
        try:
            sandbox = self.sandboxes.get(sandbox_id)
            if not sandbox:
                return False
            
            self.logger.info(f"Stopping sandbox: {sandbox_id}")
            
            # Simulate stopping
            await asyncio.sleep(0.1)
            
            sandbox.status = SandboxStatus.STOPPED
            self.logger.info(f"Sandbox stopped: {sandbox_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop sandbox {sandbox_id}: {e}")
            return False
    
    async def restart_sandbox(self, sandbox_id: str) -> bool:
        """Restart a sandbox"""
        try:
            sandbox = self.sandboxes.get(sandbox_id)
            if not sandbox:
                return False
            
            self.logger.info(f"Restarting sandbox: {sandbox_id}")
            
            # Simulate restart
            await asyncio.sleep(0.2)
            
            sandbox.status = SandboxStatus.RUNNING
            sandbox.last_used = time.time()
            
            self.logger.info(f"Sandbox restarted: {sandbox_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restart sandbox {sandbox_id}: {e}")
            return False
    
    async def destroy_sandbox(self, sandbox_id: str) -> bool:
        """Destroy a sandbox completely"""
        try:
            sandbox = self.sandboxes.get(sandbox_id)
            if not sandbox:
                return False
            
            self.logger.info(f"Destroying sandbox: {sandbox_id}")
            
            # Simulate destruction
            await asyncio.sleep(0.1)
            
            # Remove from active sandboxes
            del self.sandboxes[sandbox_id]
            
            # Clean up associated executions
            execution_ids = [eid for eid, exec in self.executions.items() 
                           if exec.sandbox_id == sandbox_id]
            for eid in execution_ids:
                del self.executions[eid]
            
            self.logger.info(f"Sandbox destroyed: {sandbox_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to destroy sandbox {sandbox_id}: {e}")
            return False
    
    async def get_sandbox_stats(self, sandbox_id: str) -> Optional[Dict[str, Any]]:
        """Get sandbox resource usage statistics"""
        try:
            sandbox = self.sandboxes.get(sandbox_id)
            if not sandbox:
                return None
            
            # Simulate stats gathering
            stats = {
                "cpu_usage": 15.5,  # percentage
                "memory_usage": "128MB",
                "disk_usage": "256MB",
                "network_io": {
                    "rx_bytes": 1024000,
                    "tx_bytes": 512000
                },
                "uptime": time.time() - sandbox.created_at,
                "execution_count": len([e for e in self.executions.values() 
                                      if e.sandbox_id == sandbox_id])
            }
            
            sandbox.stats = stats
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get stats for sandbox {sandbox_id}: {e}")
            return None
    
    async def _cleanup_inactive_sandboxes(self):
        """Clean up inactive sandboxes"""
        try:
            current_time = time.time()
            inactive_threshold = 1800  # 30 minutes
            
            to_cleanup = []
            for sandbox_id, sandbox in self.sandboxes.items():
                if (current_time - sandbox.last_used) > inactive_threshold:
                    to_cleanup.append(sandbox_id)
            
            for sandbox_id in to_cleanup:
                self.logger.info(f"Cleaning up inactive sandbox: {sandbox_id}")
                await self.destroy_sandbox(sandbox_id)
                
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
    
    async def _cleanup_oldest_sandbox(self):
        """Remove the oldest sandbox to make room"""
        if not self.sandboxes:
            return
        
        # Find oldest sandbox
        oldest_sandbox = min(self.sandboxes.values(), key=lambda x: x.created_at)
        await self.destroy_sandbox(oldest_sandbox.id)
    
    async def get_execution_history(self, 
                                   sandbox_id: Optional[str] = None,
                                   limit: int = 100) -> List[TaskExecution]:
        """Get execution history"""
        executions = list(self.executions.values())
        
        if sandbox_id:
            executions = [e for e in executions if e.sandbox_id == sandbox_id]
        
        # Sort by start time, most recent first
        executions.sort(key=lambda x: x.start_time, reverse=True)
        
        return executions[:limit]
    
    async def create_session_sandbox(self, session_id: str, 
                                   user_config: Optional[Dict[str, Any]] = None) -> SandboxInfo:
        """Create a sandbox for a specific session"""
        config = SandboxConfig(
            name=f"session-{session_id}",
            image=self.default_image,
            environment={
                "SESSION_ID": session_id,
                "PYTHONPATH": "/workspace",
                **(user_config or {}).get("environment", {})
            },
            working_directory="/workspace",
            timeout=7200,  # 2 hours
            auto_remove=True
        )
        
        # Apply user customizations
        if user_config:
            if "image" in user_config:
                config.image = user_config["image"]
            if "resources" in user_config:
                config.resources = SandboxResource(**user_config["resources"])
            if "volumes" in user_config:
                config.volumes.update(user_config["volumes"])
        
        return await self.create_sandbox(config)
    
    def get_stats_summary(self) -> Dict[str, Any]:
        """Get overall sandbox manager statistics"""
        running_count = len([s for s in self.sandboxes.values() 
                           if s.status == SandboxStatus.RUNNING])
        stopped_count = len([s for s in self.sandboxes.values() 
                           if s.status == SandboxStatus.STOPPED])
        error_count = len([s for s in self.sandboxes.values() 
                         if s.status == SandboxStatus.ERROR])
        
        total_executions = len(self.executions)
        successful_executions = len([e for e in self.executions.values() 
                                   if e.status == "completed"])
        
        return {
            "total_sandboxes": len(self.sandboxes),
            "running_sandboxes": running_count,
            "stopped_sandboxes": stopped_count,
            "error_sandboxes": error_count,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": (successful_executions / max(total_executions, 1)) * 100,
            "max_sandboxes": self.max_sandboxes
        }


class SandboxPool:
    """
    Pool of pre-created sandboxes for faster task execution
    """
    
    def __init__(self, manager: SandboxManager, pool_size: int = 3):
        self.manager = manager
        self.pool_size = pool_size
        self.available_sandboxes: List[str] = []
        self.busy_sandboxes: Dict[str, str] = {}  # sandbox_id -> session_id
        self.logger = logging.getLogger(__name__)
    
    async def initialize_pool(self):
        """Initialize the sandbox pool"""
        self.logger.info(f"Initializing sandbox pool with {self.pool_size} sandboxes")
        
        for i in range(self.pool_size):
            config = SandboxConfig(
                name=f"pool-sandbox-{i}",
                image="python:3.12-slim",
                auto_remove=False
            )
            
            sandbox = await self.manager.create_sandbox(config)
            if sandbox.status == SandboxStatus.RUNNING:
                self.available_sandboxes.append(sandbox.id)
    
    async def acquire_sandbox(self, session_id: str) -> Optional[str]:
        """Acquire a sandbox from the pool"""
        if self.available_sandboxes:
            sandbox_id = self.available_sandboxes.pop(0)
            self.busy_sandboxes[sandbox_id] = session_id
            self.logger.info(f"Acquired sandbox {sandbox_id} for session {session_id}")
            return sandbox_id
        
        # No available sandboxes, create a new one
        config = SandboxConfig(
            name=f"overflow-{session_id}",
            image="python:3.12-slim"
        )
        sandbox = await self.manager.create_sandbox(config)
        if sandbox.status == SandboxStatus.RUNNING:
            self.busy_sandboxes[sandbox.id] = session_id
            return sandbox.id
        
        return None
    
    async def release_sandbox(self, sandbox_id: str):
        """Release a sandbox back to the pool"""
        if sandbox_id in self.busy_sandboxes:
            session_id = self.busy_sandboxes.pop(sandbox_id)
            
            # Clean up sandbox
            await self.manager.execute_command(sandbox_id, "rm -rf /workspace/*")
            
            # Add back to available pool if it's a pool sandbox
            sandbox = await self.manager.get_sandbox(sandbox_id)
            if sandbox and sandbox.name.startswith("pool-"):
                self.available_sandboxes.append(sandbox_id)
                self.logger.info(f"Released sandbox {sandbox_id} back to pool")
            else:
                # Destroy overflow sandboxes
                await self.manager.destroy_sandbox(sandbox_id)
                self.logger.info(f"Destroyed overflow sandbox {sandbox_id}")


# Default configurations for different use cases
DEFAULT_CONFIGS = {
    "python": SandboxConfig(
        name="python-sandbox",
        image="python:3.12-slim",
        environment={"PYTHONPATH": "/workspace"},
        working_directory="/workspace"
    ),
    "nodejs": SandboxConfig(
        name="nodejs-sandbox", 
        image="node:18-slim",
        environment={"NODE_PATH": "/workspace/node_modules"},
        working_directory="/workspace"
    ),
    "data_science": SandboxConfig(
        name="datascience-sandbox",
        image="jupyter/datascience-notebook:latest",
        resources=SandboxResource(memory_limit="2g", cpu_limit=2.0),
        working_directory="/home/jovyan/work"
    )
}


async def create_sandbox_manager(max_sandboxes: int = 10) -> SandboxManager:
    """Factory function to create sandbox manager"""
    return SandboxManager(max_sandboxes=max_sandboxes)