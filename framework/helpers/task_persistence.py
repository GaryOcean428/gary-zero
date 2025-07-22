"""Task persistence module for storing tasks in database.

This module provides database storage and retrieval for tasks,
enabling persistent task tracking across sessions.
"""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from framework.helpers.task_manager import Task, TaskCategory, TaskStatus, TaskUpdate


class TaskDatabase:
    """Database interface for task persistence."""

    def __init__(self, db_path: str = "tmp/tasks.db"):
        """Initialize the task database.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path

        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize the database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Tasks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    status TEXT,
                    priority INTEGER,
                    progress REAL,
                    created_at TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    context_id TEXT,
                    agent_id TEXT,
                    parent_id TEXT,
                    subtask_ids TEXT,  -- JSON array
                    result TEXT,
                    error_message TEXT,
                    metadata TEXT  -- JSON object
                )
            ''')

            # Task updates table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_updates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT,
                    timestamp TEXT,
                    status TEXT,
                    progress REAL,
                    message TEXT,
                    agent_id TEXT,
                    FOREIGN KEY (task_id) REFERENCES tasks (id)
                )
            ''')

            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks (category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_context ON tasks (context_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_updates_task ON task_updates (task_id)')

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper error handling."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        try:
            yield conn
        finally:
            conn.close()

    def save_task(self, task: Task) -> bool:
        """Save a task to the database.
        
        Args:
            task: The task to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT OR REPLACE INTO tasks (
                        id, title, description, category, status, priority,
                        progress, created_at, started_at, completed_at,
                        context_id, agent_id, parent_id, subtask_ids,
                        result, error_message, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task.id,
                    task.title,
                    task.description,
                    task.category.value if task.category else None,
                    task.status.value,
                    task.priority,
                    task.progress,
                    task.created_at.isoformat() if task.created_at else None,
                    task.started_at.isoformat() if task.started_at else None,
                    task.completed_at.isoformat() if task.completed_at else None,
                    task.context_id,
                    task.agent_id,
                    task.parent_id,
                    json.dumps(task.subtask_ids),
                    task.result,
                    task.error_message,
                    json.dumps(task.metadata)
                ))

                conn.commit()
                return True

        except Exception as e:
            print(f"Error saving task {task.id}: {e}")
            return False

    def load_task(self, task_id: str) -> Task | None:
        """Load a task from the database.
        
        Args:
            task_id: The ID of the task to load
            
        Returns:
            The task if found, None otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
                row = cursor.fetchone()

                if not row:
                    return None

                return self._row_to_task(row)

        except Exception as e:
            print(f"Error loading task {task_id}: {e}")
            return None

    def load_all_tasks(self) -> list[Task]:
        """Load all tasks from the database.
        
        Returns:
            List of all tasks
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
                rows = cursor.fetchall()

                return [self._row_to_task(row) for row in rows]

        except Exception as e:
            print(f"Error loading all tasks: {e}")
            return []

    def load_tasks_by_status(self, status: TaskStatus) -> list[Task]:
        """Load tasks with a specific status.
        
        Args:
            status: The task status to filter by
            
        Returns:
            List of tasks with the specified status
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC',
                    (status.value,)
                )
                rows = cursor.fetchall()

                return [self._row_to_task(row) for row in rows]

        except Exception as e:
            print(f"Error loading tasks by status {status}: {e}")
            return []

    def load_tasks_by_context(self, context_id: str) -> list[Task]:
        """Load tasks for a specific context.
        
        Args:
            context_id: The context ID to filter by
            
        Returns:
            List of tasks for the specified context
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM tasks WHERE context_id = ? ORDER BY created_at DESC',
                    (context_id,)
                )
                rows = cursor.fetchall()

                return [self._row_to_task(row) for row in rows]

        except Exception as e:
            print(f"Error loading tasks by context {context_id}: {e}")
            return []

    def save_task_update(self, update: TaskUpdate) -> bool:
        """Save a task update to the database.
        
        Args:
            update: The task update to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO task_updates (
                        task_id, timestamp, status, progress, message, agent_id
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    update.task_id,
                    update.timestamp.isoformat(),
                    update.status.value,
                    update.progress,
                    update.message,
                    update.agent_id
                ))

                conn.commit()
                return True

        except Exception as e:
            print(f"Error saving task update: {e}")
            return False

    def load_task_updates(self, task_id: str) -> list[TaskUpdate]:
        """Load all updates for a specific task.
        
        Args:
            task_id: The task ID to get updates for
            
        Returns:
            List of task updates
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM task_updates WHERE task_id = ? ORDER BY timestamp ASC',
                    (task_id,)
                )
                rows = cursor.fetchall()

                updates = []
                for row in rows:
                    updates.append(TaskUpdate(
                        task_id=row['task_id'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        status=TaskStatus(row['status']),
                        progress=row['progress'],
                        message=row['message'],
                        agent_id=row['agent_id']
                    ))

                return updates

        except Exception as e:
            print(f"Error loading task updates for {task_id}: {e}")
            return []

    def delete_task(self, task_id: str) -> bool:
        """Delete a task and its updates from the database.
        
        Args:
            task_id: The ID of the task to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Delete task updates first
                cursor.execute('DELETE FROM task_updates WHERE task_id = ?', (task_id,))

                # Delete the task
                cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))

                conn.commit()
                return True

        except Exception as e:
            print(f"Error deleting task {task_id}: {e}")
            return False

    def get_statistics(self) -> dict[str, Any]:
        """Get database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Total tasks
                cursor.execute('SELECT COUNT(*) FROM tasks')
                total_tasks = cursor.fetchone()[0]

                # Tasks by status
                status_counts = {}
                for status in TaskStatus:
                    cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = ?', (status.value,))
                    status_counts[status.value] = cursor.fetchone()[0]

                # Tasks by category
                category_counts = {}
                for category in TaskCategory:
                    cursor.execute('SELECT COUNT(*) FROM tasks WHERE category = ?', (category.value,))
                    category_counts[category.value] = cursor.fetchone()[0]

                # Total updates
                cursor.execute('SELECT COUNT(*) FROM task_updates')
                total_updates = cursor.fetchone()[0]

                return {
                    "total_tasks": total_tasks,
                    "total_updates": total_updates,
                    "status_distribution": status_counts,
                    "category_distribution": category_counts
                }

        except Exception as e:
            print(f"Error getting database statistics: {e}")
            return {}

    def _row_to_task(self, row) -> Task:
        """Convert a database row to a Task object.
        
        Args:
            row: Database row
            
        Returns:
            Task object
        """
        return Task(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            category=TaskCategory(row['category']) if row['category'] else TaskCategory.OTHER,
            status=TaskStatus(row['status']),
            priority=row['priority'],
            progress=row['progress'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            context_id=row['context_id'],
            agent_id=row['agent_id'],
            parent_id=row['parent_id'],
            subtask_ids=json.loads(row['subtask_ids']) if row['subtask_ids'] else [],
            result=row['result'],
            error_message=row['error_message'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )


# Global database instance
_database_instance: TaskDatabase | None = None


def get_task_database() -> TaskDatabase:
    """Get the global task database instance."""
    global _database_instance
    if _database_instance is None:
        _database_instance = TaskDatabase()
    return _database_instance
