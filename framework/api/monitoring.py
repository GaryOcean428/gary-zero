"""
API endpoints for unified logging and monitoring.

Provides REST endpoints to access logs, metrics, and benchmarking data.
"""

import time
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..logging.unified_logger import EventType, LogEvent, LogLevel, get_unified_logger
from ..performance.monitor import get_performance_monitor


class LogEventResponse(BaseModel):
    """Response model for log events."""

    event_id: str
    timestamp: float
    timestamp_iso: str
    event_type: str
    level: str
    message: str
    agent_id: str | None = None
    session_id: str | None = None
    user_id: str | None = None
    component: str | None = None
    tool_name: str | None = None
    duration_ms: float | None = None
    error_message: str | None = None
    metadata: dict[str, Any] | None = None


class LogStatisticsResponse(BaseModel):
    """Response model for log statistics."""

    total_events: int
    events_in_buffer: int
    events_by_type: dict[str, int]
    events_by_level: dict[str, int]
    buffer_utilization: float


class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics."""

    timestamp: float
    resource_usage: dict[str, Any]
    operation_metrics: dict[str, Any]
    alerts: list[dict[str, Any]]


class TimelineResponse(BaseModel):
    """Response model for execution timeline."""

    events: list[LogEventResponse]
    total_count: int
    time_range: dict[str, float]


# Create router
router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


@router.get("/logs", response_model=list[LogEventResponse])
async def get_logs(
    event_type: str | None = Query(None, description="Filter by event type"),
    level: str | None = Query(None, description="Filter by log level"),
    user_id: str | None = Query(None, description="Filter by user ID"),
    agent_id: str | None = Query(None, description="Filter by agent ID"),
    start_time: float | None = Query(None, description="Start timestamp"),
    end_time: float | None = Query(None, description="End timestamp"),
    limit: int = Query(100, description="Maximum number of events", le=1000),
):
    """Retrieve log events with optional filtering."""
    logger = get_unified_logger()

    # Convert string parameters to enums if provided
    event_type_enum = None
    if event_type:
        try:
            event_type_enum = EventType(event_type)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid event_type: {event_type}"
            )

    level_enum = None
    if level:
        try:
            level_enum = LogLevel(level)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid level: {level}")

    events = await logger.get_events(
        event_type=event_type_enum,
        level=level_enum,
        user_id=user_id,
        agent_id=agent_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )

    return [
        LogEventResponse(
            event_id=event.event_id,
            timestamp=event.timestamp,
            timestamp_iso=event.to_dict()["timestamp_iso"],
            event_type=event.event_type.value,
            level=event.level.value,
            message=event.message,
            agent_id=event.agent_id,
            session_id=event.session_id,
            user_id=event.user_id,
            component=event.component,
            tool_name=event.tool_name,
            duration_ms=event.duration_ms,
            error_message=event.error_message,
            metadata=event.metadata,
        )
        for event in events
    ]


@router.get("/logs/statistics", response_model=LogStatisticsResponse)
async def get_log_statistics():
    """Get logging statistics."""
    logger = get_unified_logger()
    stats = logger.get_statistics()

    return LogStatisticsResponse(**stats)


@router.get("/logs/timeline", response_model=TimelineResponse)
async def get_execution_timeline(
    agent_id: str | None = Query(None, description="Filter by agent ID"),
    session_id: str | None = Query(None, description="Filter by session ID"),
    start_time: float | None = Query(None, description="Start timestamp"),
    end_time: float | None = Query(None, description="End timestamp"),
):
    """Get execution timeline for analysis."""
    logger = get_unified_logger()

    events = await logger.get_execution_timeline(
        agent_id=agent_id,
        session_id=session_id,
        start_time=start_time,
        end_time=end_time,
    )

    # Calculate time range
    if events:
        min_time = min(event.timestamp for event in events)
        max_time = max(event.timestamp for event in events)
    else:
        min_time = max_time = time.time()

    response_events = [
        LogEventResponse(
            event_id=event.event_id,
            timestamp=event.timestamp,
            timestamp_iso=event.to_dict()["timestamp_iso"],
            event_type=event.event_type.value,
            level=event.level.value,
            message=event.message,
            agent_id=event.agent_id,
            session_id=event.session_id,
            user_id=event.user_id,
            component=event.component,
            tool_name=event.tool_name,
            duration_ms=event.duration_ms,
            error_message=event.error_message,
            metadata=event.metadata,
        )
        for event in events
    ]

    return TimelineResponse(
        events=response_events,
        total_count=len(events),
        time_range={"start": min_time, "end": max_time},
    )


@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    duration_seconds: int = Query(
        300, description="Duration in seconds for metrics", le=3600
    ),
):
    """Get performance metrics and resource usage."""
    monitor = get_performance_monitor()

    summary = monitor.get_performance_summary(duration_seconds=duration_seconds)

    return PerformanceMetricsResponse(
        timestamp=summary["timestamp"],
        resource_usage=summary["resource_usage"],
        operation_metrics=summary["operation_metrics"],
        alerts=summary["alerts"],
    )


@router.get("/performance/export")
async def export_performance_metrics(
    format: str = Query("json", description="Export format"),
):
    """Export performance metrics."""
    monitor = get_performance_monitor()

    try:
        exported_data = monitor.export_metrics(format=format)
        return {"format": format, "data": exported_data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring system."""
    logger = get_unified_logger()
    monitor = get_performance_monitor()

    # Basic health checks
    current_time = time.time()

    # Check if systems are responsive
    try:
        log_stats = logger.get_statistics()
        perf_summary = monitor.get_performance_summary(duration_seconds=60)

        health_status = {
            "status": "healthy",
            "timestamp": current_time,
            "systems": {
                "unified_logger": {
                    "status": "operational",
                    "total_events": log_stats["total_events"],
                    "buffer_utilization": log_stats["buffer_utilization"],
                },
                "performance_monitor": {
                    "status": "operational",
                    "alerts_count": len(perf_summary["alerts"]),
                },
            },
        }

        # Check for issues
        if log_stats["buffer_utilization"] > 0.9:
            health_status["warnings"] = health_status.get("warnings", [])
            health_status["warnings"].append("High log buffer utilization")

        if len(perf_summary["alerts"]) > 0:
            health_status["warnings"] = health_status.get("warnings", [])
            health_status["warnings"].append(
                f"{len(perf_summary['alerts'])} performance alerts active"
            )

        return health_status

    except Exception as e:
        return {"status": "unhealthy", "timestamp": current_time, "error": str(e)}


@router.post("/logs/test")
async def create_test_log_event(
    event_type: str = "system_event",
    message: str = "Test log event",
    agent_id: str | None = None,
):
    """Create a test log event for testing purposes."""
    logger = get_unified_logger()

    try:
        event_type_enum = EventType(event_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid event_type: {event_type}")

    event = LogEvent(
        event_type=event_type_enum,
        level=LogLevel.INFO,
        message=message,
        agent_id=agent_id,
        metadata={"test": True, "source": "api"},
    )

    await logger.log_event(event)

    return {
        "event_id": event.event_id,
        "message": "Test event created successfully",
        "timestamp": event.timestamp,
    }
