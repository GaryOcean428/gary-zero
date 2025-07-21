"""
Async utilities and patterns for performance optimization.

Provides enhanced async functionality including:
- Async connection pooling
- Background task management
- Async context managers
- Resource management utilities
"""

import asyncio
import time
import weakref
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List, Optional, Union, AsyncGenerator, Coroutine
import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Background task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BackgroundTask:
    """Background task representation."""
    id: str
    name: str
    coro: Coroutine
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None
    priority: int = 0  # Higher numbers = higher priority


class AsyncPool:
    """Async connection/resource pool with configurable limits."""
    
    def __init__(self, 
                 factory: Callable[[], Any],
                 max_size: int = 10,
                 min_size: int = 1,
                 timeout: float = 30.0,
                 cleanup_func: Optional[Callable] = None):
        self.factory = factory
        self.max_size = max_size
        self.min_size = min_size
        self.timeout = timeout
        self.cleanup_func = cleanup_func
        
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._created_count = 0
        self._active_count = 0
        self._lock = asyncio.Lock()
        self._closed = False
    
    async def _create_resource(self) -> Any:
        """Create a new resource."""
        try:
            resource = await asyncio.get_event_loop().run_in_executor(
                None, self.factory
            )
            self._created_count += 1
            return resource
        except Exception as e:
            logger.error(f"Failed to create pool resource: {e}")
            raise
    
    async def _initialize_pool(self) -> None:
        """Initialize the pool with minimum resources."""
        async with self._lock:
            if self._created_count < self.min_size:
                for _ in range(self.min_size - self._created_count):
                    try:
                        resource = await self._create_resource()
                        await self._pool.put(resource)
                    except Exception as e:
                        logger.warning(f"Failed to initialize pool resource: {e}")
    
    async def acquire(self) -> Any:
        """Acquire a resource from the pool."""
        if self._closed:
            raise RuntimeError("Pool is closed")
        
        # Initialize pool if needed
        if self._created_count == 0:
            await self._initialize_pool()
        
        try:
            # Try to get existing resource
            resource = await asyncio.wait_for(
                self._pool.get(), timeout=0.1
            )
        except asyncio.TimeoutError:
            # Create new resource if pool is not full
            async with self._lock:
                if self._created_count < self.max_size:
                    resource = await self._create_resource()
                else:
                    # Wait for available resource
                    resource = await asyncio.wait_for(
                        self._pool.get(), timeout=self.timeout
                    )
        
        self._active_count += 1
        return resource
    
    async def release(self, resource: Any) -> None:
        """Release a resource back to the pool."""
        if self._closed:
            if self.cleanup_func:
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.cleanup_func, resource
                    )
                except Exception as e:
                    logger.warning(f"Error cleaning up resource: {e}")
            return
        
        self._active_count -= 1
        
        try:
            await self._pool.put(resource)
        except Exception as e:
            logger.warning(f"Failed to return resource to pool: {e}")
            # Clean up the resource if we can't return it
            if self.cleanup_func:
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.cleanup_func, resource
                    )
                except Exception as cleanup_error:
                    logger.warning(f"Error cleaning up resource: {cleanup_error}")
    
    @asynccontextmanager
    async def get(self):
        """Context manager for acquiring and releasing resources."""
        resource = await self.acquire()
        try:
            yield resource
        finally:
            await self.release(resource)
    
    async def close(self) -> None:
        """Close the pool and clean up all resources."""
        self._closed = True
        
        # Clean up all resources in the pool
        while not self._pool.empty():
            try:
                resource = await asyncio.wait_for(self._pool.get(), timeout=0.1)
                if self.cleanup_func:
                    try:
                        await asyncio.get_event_loop().run_in_executor(
                            None, self.cleanup_func, resource
                        )
                    except Exception as e:
                        logger.warning(f"Error cleaning up resource during close: {e}")
            except asyncio.TimeoutError:
                break
    
    def stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            'total_created': self._created_count,
            'active_count': self._active_count,
            'available_count': self._pool.qsize(),
            'max_size': self.max_size,
            'min_size': self.min_size,
            'is_closed': self._closed
        }


class BackgroundTaskManager:
    """Manager for background async tasks with prioritization."""
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self._tasks: Dict[str, BackgroundTask] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._lock = asyncio.Lock()
        self._shutdown = False
    
    async def _execute_task(self, task: BackgroundTask) -> None:
        """Execute a background task with error handling."""
        async with self._semaphore:
            if self._shutdown:
                task.status = TaskStatus.CANCELLED
                return
            
            task.status = TaskStatus.RUNNING
            task.started_at = time.time()
            
            try:
                task.result = await task.coro
                task.status = TaskStatus.COMPLETED
            except asyncio.CancelledError:
                task.status = TaskStatus.CANCELLED
                raise
            except Exception as e:
                task.error = e
                task.status = TaskStatus.FAILED
                logger.error(f"Background task {task.name} failed: {e}")
            finally:
                task.completed_at = time.time()
                async with self._lock:
                    self._running_tasks.pop(task.id, None)
    
    async def submit(self, 
                    name: str,
                    coro: Coroutine,
                    priority: int = 0,
                    task_id: Optional[str] = None) -> str:
        """Submit a coroutine as a background task."""
        if self._shutdown:
            raise RuntimeError("Task manager is shutdown")
        
        if task_id is None:
            task_id = f"{name}_{int(time.time() * 1000000)}"
        
        background_task = BackgroundTask(
            id=task_id,
            name=name,
            coro=coro,
            priority=priority
        )
        
        async with self._lock:
            self._tasks[task_id] = background_task
            
            # Create and start asyncio task
            asyncio_task = asyncio.create_task(self._execute_task(background_task))
            self._running_tasks[task_id] = asyncio_task
        
        return task_id
    
    async def wait(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """Wait for a specific task to complete and return its result."""
        if task_id not in self._tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self._tasks[task_id]
        
        # If task is already completed, return immediately
        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            if task.status == TaskStatus.FAILED:
                raise task.error
            elif task.status == TaskStatus.CANCELLED:
                raise asyncio.CancelledError()
            return task.result
        
        # Wait for the asyncio task
        if task_id in self._running_tasks:
            try:
                await asyncio.wait_for(self._running_tasks[task_id], timeout=timeout)
                return task.result
            except asyncio.TimeoutError:
                raise
            except Exception:
                if task.error:
                    raise task.error
                raise
        
        raise RuntimeError(f"Task {task_id} is not running")
    
    async def cancel(self, task_id: str) -> bool:
        """Cancel a specific task."""
        async with self._lock:
            if task_id in self._running_tasks:
                asyncio_task = self._running_tasks[task_id]
                asyncio_task.cancel()
                return True
            
            if task_id in self._tasks:
                task = self._tasks[task_id]
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.CANCELLED
                    return True
        
        return False
    
    async def wait_all(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Wait for all tasks to complete."""
        if not self._running_tasks:
            return {}
        
        try:
            await asyncio.wait_for(
                asyncio.gather(*self._running_tasks.values(), return_exceptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for all tasks to complete")
        
        return {task_id: task.result for task_id, task in self._tasks.items()
                if task.status == TaskStatus.COMPLETED}
    
    async def shutdown(self, timeout: Optional[float] = 30.0) -> None:
        """Shutdown the task manager and cancel all running tasks."""
        self._shutdown = True
        
        # Cancel all running tasks
        cancel_tasks = []
        async with self._lock:
            for asyncio_task in self._running_tasks.values():
                asyncio_task.cancel()
                cancel_tasks.append(asyncio_task)
        
        if cancel_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*cancel_tasks, return_exceptions=True),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.warning("Timeout during task manager shutdown")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status information for a specific task."""
        if task_id not in self._tasks:
            return None
        
        task = self._tasks[task_id]
        return {
            'id': task.id,
            'name': task.name,
            'status': task.status.value,
            'created_at': task.created_at,
            'started_at': task.started_at,
            'completed_at': task.completed_at,
            'duration': (
                (task.completed_at or time.time()) - (task.started_at or task.created_at)
                if task.started_at else None
            ),
            'priority': task.priority,
            'has_error': task.error is not None
        }
    
    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Dict[str, Any]]:
        """List all tasks, optionally filtered by status."""
        tasks = []
        for task in self._tasks.values():
            if status is None or task.status == status:
                task_info = self.get_task_status(task.id)
                if task_info:
                    tasks.append(task_info)
        
        return sorted(tasks, key=lambda x: x['priority'], reverse=True)
    
    def stats(self) -> Dict[str, Any]:
        """Get task manager statistics."""
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = sum(
                1 for task in self._tasks.values() if task.status == status
            )
        
        return {
            'total_tasks': len(self._tasks),
            'running_tasks': len(self._running_tasks),
            'max_concurrent': self.max_concurrent,
            'is_shutdown': self._shutdown,
            'status_counts': status_counts
        }


class AsyncContextManager:
    """Utility class for creating async context managers."""
    
    def __init__(self, 
                 enter_func: Optional[Callable] = None,
                 exit_func: Optional[Callable] = None):
        self.enter_func = enter_func
        self.exit_func = exit_func
        self.resource = None
    
    async def __aenter__(self):
        if self.enter_func:
            if asyncio.iscoroutinefunction(self.enter_func):
                self.resource = await self.enter_func()
            else:
                self.resource = self.enter_func()
        return self.resource
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.exit_func:
            if asyncio.iscoroutinefunction(self.exit_func):
                await self.exit_func(self.resource, exc_type, exc_val, exc_tb)
            else:
                self.exit_func(self.resource, exc_type, exc_val, exc_tb)


def async_timeout(timeout: float):
    """Decorator to add timeout to async functions."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
        return wrapper
    return decorator


def async_retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator to add retry logic to async functions."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay} seconds..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}"
                        )
            
            raise last_exception
        return wrapper
    return decorator


# Global instances
_default_task_manager = None

def get_task_manager() -> BackgroundTaskManager:
    """Get the default background task manager."""
    global _default_task_manager
    if _default_task_manager is None:
        _default_task_manager = BackgroundTaskManager()
    return _default_task_manager


async def run_background(name: str, coro: Coroutine, priority: int = 0) -> str:
    """Run a coroutine in the background using the default task manager."""
    return await get_task_manager().submit(name, coro, priority)