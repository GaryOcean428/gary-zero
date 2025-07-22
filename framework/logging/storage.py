"""
Persistent storage for unified logging system.

Provides SQLite-based storage for log events with proper indexing and querying.
"""

import asyncio
import json
import sqlite3
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from .unified_logger import EventType, LogEvent, LogLevel


class LogStorage(ABC):
    """Abstract base class for log storage backends."""

    @abstractmethod
    async def store_event(self, event: LogEvent) -> None:
        """Store a single log event."""
        pass

    @abstractmethod
    async def get_events(self,
                        event_type: EventType | None = None,
                        level: LogLevel | None = None,
                        start_time: float | None = None,
                        end_time: float | None = None,
                        limit: int = 100) -> list[LogEvent]:
        """Retrieve events with filtering."""
        pass

    @abstractmethod
    async def get_statistics(self) -> dict[str, Any]:
        """Get storage statistics."""
        pass


class SqliteStorage(LogStorage):
    """SQLite-based storage for log events."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection_lock = asyncio.Lock()
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS log_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    agent_id TEXT,
                    session_id TEXT,
                    user_id TEXT,
                    component TEXT,
                    function_name TEXT,
                    tool_name TEXT,
                    input_data TEXT,  -- JSON
                    output_data TEXT, -- JSON
                    metadata TEXT,    -- JSON
                    duration_ms REAL,
                    cpu_usage REAL,
                    memory_usage REAL,
                    error_type TEXT,
                    error_message TEXT,
                    stack_trace TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for efficient querying
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON log_events(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON log_events(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_level ON log_events(level)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_id ON log_events(agent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON log_events(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tool_name ON log_events(tool_name)")

            conn.commit()

    async def store_event(self, event: LogEvent) -> None:
        """Store a single log event."""
        async with self._connection_lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO log_events (
                        event_id, timestamp, event_type, level, message,
                        agent_id, session_id, user_id, component, function_name, tool_name,
                        input_data, output_data, metadata,
                        duration_ms, cpu_usage, memory_usage,
                        error_type, error_message, stack_trace
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.timestamp,
                    event.event_type.value,
                    event.level.value,
                    event.message,
                    event.agent_id,
                    event.session_id,
                    event.user_id,
                    event.component,
                    event.function_name,
                    event.tool_name,
                    json.dumps(event.input_data) if event.input_data else None,
                    json.dumps(event.output_data) if event.output_data else None,
                    json.dumps(event.metadata) if event.metadata else None,
                    event.duration_ms,
                    event.cpu_usage,
                    event.memory_usage,
                    event.error_type,
                    event.error_message,
                    event.stack_trace
                ))
                conn.commit()

    async def get_events(self,
                        event_type: EventType | None = None,
                        level: LogLevel | None = None,
                        agent_id: str | None = None,
                        user_id: str | None = None,
                        start_time: float | None = None,
                        end_time: float | None = None,
                        limit: int = 100) -> list[LogEvent]:
        """Retrieve events with filtering."""
        query = "SELECT * FROM log_events WHERE 1=1"
        params = []

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.value)

        if level:
            query += " AND level = ?"
            params.append(level.value)

        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        async with self._connection_lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()

        events = []
        for row in rows:
            event = LogEvent(
                event_id=row['event_id'],
                timestamp=row['timestamp'],
                event_type=EventType(row['event_type']),
                level=LogLevel(row['level']),
                message=row['message'],
                agent_id=row['agent_id'],
                session_id=row['session_id'],
                user_id=row['user_id'],
                component=row['component'],
                function_name=row['function_name'],
                tool_name=row['tool_name'],
                input_data=json.loads(row['input_data']) if row['input_data'] else None,
                output_data=json.loads(row['output_data']) if row['output_data'] else None,
                metadata=json.loads(row['metadata']) if row['metadata'] else None,
                duration_ms=row['duration_ms'],
                cpu_usage=row['cpu_usage'],
                memory_usage=row['memory_usage'],
                error_type=row['error_type'],
                error_message=row['error_message'],
                stack_trace=row['stack_trace']
            )
            events.append(event)

        return events

    async def get_statistics(self) -> dict[str, Any]:
        """Get storage statistics."""
        async with self._connection_lock:
            with sqlite3.connect(self.db_path) as conn:
                # Total events
                total_count = conn.execute("SELECT COUNT(*) FROM log_events").fetchone()[0]

                # Events by type
                type_counts = {}
                for row in conn.execute("""
                    SELECT event_type, COUNT(*) as count 
                    FROM log_events 
                    GROUP BY event_type
                """):
                    type_counts[row[0]] = row[1]

                # Events by level
                level_counts = {}
                for row in conn.execute("""
                    SELECT level, COUNT(*) as count 
                    FROM log_events 
                    GROUP BY level
                """):
                    level_counts[row[0]] = row[1]

                # Recent activity (last 24 hours)
                recent_cutoff = time.time() - (24 * 3600)
                recent_count = conn.execute(
                    "SELECT COUNT(*) FROM log_events WHERE timestamp > ?",
                    (recent_cutoff,)
                ).fetchone()[0]

                # Database file size
                db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

        return {
            "total_events": total_count,
            "events_by_type": type_counts,
            "events_by_level": level_counts,
            "recent_events_24h": recent_count,
            "database_size_bytes": db_size
        }

    async def cleanup_old_events(self, days_to_keep: int = 30) -> int:
        """Remove events older than specified days."""
        cutoff_time = time.time() - (days_to_keep * 24 * 3600)

        async with self._connection_lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM log_events WHERE timestamp < ?",
                    (cutoff_time,)
                )
                deleted_count = cursor.rowcount
                conn.commit()

        return deleted_count

    async def export_events(self,
                          output_file: str,
                          start_time: float | None = None,
                          end_time: float | None = None) -> int:
        """Export events to JSON file."""
        events = await self.get_events(
            start_time=start_time,
            end_time=end_time,
            limit=100000  # Large limit for export
        )

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            for event in events:
                f.write(event.to_json() + '\n')

        return len(events)
