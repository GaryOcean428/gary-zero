"""Tests for domain events module."""

import asyncio
import pytest
from datetime import datetime

from framework.domain.events import (
    DomainEvent,
    AgentCreatedEvent,
    MessageProcessedEvent,
    ToolExecutedEvent,
    EventBus,
    get_event_bus,
    reset_event_bus,
)


class TestDomainEvent:
    """Test domain event base class."""
    
    def test_event_creation(self):
        """Test creating domain events."""
        event = AgentCreatedEvent(agent_id="test-agent")
        
        assert event.event_id is not None
        assert isinstance(event.timestamp, datetime)
        assert event.agent_id == "test-agent"
        assert event.event_type == "agent.created"
    
    def test_event_with_aggregate_id(self):
        """Test event with aggregate ID."""
        event = MessageProcessedEvent(
            aggregate_id="msg-123",
            message_id="msg-123",
            agent_id="agent-456"
        )
        
        assert event.aggregate_id == "msg-123"
        assert event.message_id == "msg-123"
        assert event.agent_id == "agent-456"


class TestEventBus:
    """Test event bus functionality."""
    
    def setup_method(self):
        """Set up each test."""
        reset_event_bus()
        self.event_bus = get_event_bus()
        self.received_events = []
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_event_bus()
    
    def sync_handler(self, event: DomainEvent):
        """Synchronous event handler for testing."""
        self.received_events.append(event)
    
    async def async_handler(self, event: DomainEvent):
        """Asynchronous event handler for testing."""
        self.received_events.append(event)
    
    def test_register_handler(self):
        """Test registering event handlers."""
        self.event_bus.register_handler("test.event", self.sync_handler)
        count = self.event_bus.get_handler_count("test.event")
        assert count == 1
    
    def test_unregister_handler(self):
        """Test unregistering event handlers."""
        self.event_bus.register_handler("test.event", self.sync_handler)
        self.event_bus.unregister_handler("test.event", self.sync_handler)
        count = self.event_bus.get_handler_count("test.event")
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_publish_to_sync_handler(self):
        """Test publishing events to synchronous handlers."""
        self.event_bus.register_handler("agent.created", self.sync_handler)
        
        event = AgentCreatedEvent(agent_id="test-agent")
        await self.event_bus.publish(event)
        
        assert len(self.received_events) == 1
        assert self.received_events[0].agent_id == "test-agent"
    
    @pytest.mark.asyncio
    async def test_publish_to_async_handler(self):
        """Test publishing events to asynchronous handlers."""
        self.event_bus.register_handler("agent.created", self.async_handler)
        
        event = AgentCreatedEvent(agent_id="test-agent")
        await self.event_bus.publish(event)
        
        assert len(self.received_events) == 1
        assert self.received_events[0].agent_id == "test-agent"
    
    @pytest.mark.asyncio
    async def test_publish_to_multiple_handlers(self):
        """Test publishing events to multiple handlers."""
        events_received_1 = []
        events_received_2 = []
        
        def handler_1(event):
            events_received_1.append(event)
        
        def handler_2(event):
            events_received_2.append(event)
        
        self.event_bus.register_handler("agent.created", handler_1)
        self.event_bus.register_handler("agent.created", handler_2)
        
        event = AgentCreatedEvent(agent_id="test-agent")
        await self.event_bus.publish(event)
        
        assert len(events_received_1) == 1
        assert len(events_received_2) == 1
    
    @pytest.mark.asyncio
    async def test_middleware(self):
        """Test event middleware."""
        middleware_events = []
        
        def middleware(event):
            middleware_events.append(event)
        
        self.event_bus.register_middleware(middleware)
        self.event_bus.register_handler("agent.created", self.sync_handler)
        
        event = AgentCreatedEvent(agent_id="test-agent")
        await self.event_bus.publish(event)
        
        # Both middleware and handler should receive the event
        assert len(middleware_events) == 1
        assert len(self.received_events) == 1
    
    @pytest.mark.asyncio
    async def test_publish_no_handlers(self):
        """Test publishing events with no registered handlers."""
        event = AgentCreatedEvent(agent_id="test-agent")
        # Should not raise an exception
        await self.event_bus.publish(event)
    
    def test_clear_handlers(self):
        """Test clearing event handlers."""
        self.event_bus.register_handler("agent.created", self.sync_handler)
        self.event_bus.register_handler("message.processed", self.sync_handler)
        
        # Clear specific event type
        self.event_bus.clear_handlers("agent.created")
        assert self.event_bus.get_handler_count("agent.created") == 0
        assert self.event_bus.get_handler_count("message.processed") == 1
        
        # Clear all handlers
        self.event_bus.clear_handlers()
        assert self.event_bus.get_handler_count("message.processed") == 0


class TestEventTypes:
    """Test specific event types."""
    
    def test_agent_created_event(self):
        """Test AgentCreatedEvent."""
        event = AgentCreatedEvent(
            agent_id="agent-123",
            agent_type="chat",
            configuration={"model": "gpt-4", "temperature": 0.7}
        )
        
        assert event.event_type == "agent.created"
        assert event.agent_id == "agent-123"
        assert event.agent_type == "chat"
        assert event.configuration["model"] == "gpt-4"
    
    def test_message_processed_event(self):
        """Test MessageProcessedEvent."""
        event = MessageProcessedEvent(
            message_id="msg-123",
            agent_id="agent-456",
            content="Hello, world!",
            processing_time_ms=150.5
        )
        
        assert event.event_type == "message.processed"
        assert event.message_id == "msg-123"
        assert event.agent_id == "agent-456"
        assert event.content == "Hello, world!"
        assert event.processing_time_ms == 150.5
    
    def test_tool_executed_event(self):
        """Test ToolExecutedEvent."""
        event = ToolExecutedEvent(
            tool_name="file_reader",
            agent_id="agent-789",
            parameters={"path": "/test/file.txt"},
            result={"content": "file content"},
            execution_time_ms=50.0
        )
        
        assert event.event_type == "tool.executed"
        assert event.tool_name == "file_reader"
        assert event.agent_id == "agent-789"
        assert event.parameters["path"] == "/test/file.txt"
        assert event.result["content"] == "file content"


def test_global_event_bus():
    """Test global event bus instance."""
    reset_event_bus()
    
    bus1 = get_event_bus()
    bus2 = get_event_bus()
    
    # Should return the same instance
    assert bus1 is bus2
    
    # Reset should create new instance
    reset_event_bus()
    bus3 = get_event_bus()
    assert bus3 is not bus1