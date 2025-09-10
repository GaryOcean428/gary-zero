"""Tests for domain entities module."""

import pytest
from datetime import datetime

from framework.domain.entities import (
    DomainEntity,
    Agent,
    Message,
    Tool,
    Session,
)
from framework.domain.events import (
    AgentCreatedEvent,
    MessageProcessedEvent,
    ToolExecutedEvent,
)


class TestDomainEntity:
    """Test base domain entity functionality."""
    
    def test_entity_creation(self):
        """Test creating domain entities."""
        agent = Agent(name="Test Agent", agent_type="chat")
        
        assert agent.id is not None
        assert isinstance(agent.created_at, datetime)
        assert isinstance(agent.updated_at, datetime)
        assert agent.version == 1
        assert agent.entity_type == "agent"
    
    def test_entity_equality(self):
        """Test entity equality by ID."""
        agent1 = Agent(id="same-id", name="Agent 1")
        agent2 = Agent(id="same-id", name="Agent 2")
        agent3 = Agent(id="different-id", name="Agent 3")
        
        assert agent1 == agent2  # Same ID
        assert agent1 != agent3  # Different ID
        assert hash(agent1) == hash(agent2)  # Same hash for same ID
    
    def test_update_timestamp(self):
        """Test updating timestamp and version."""
        agent = Agent(name="Test Agent")
        original_updated = agent.updated_at
        original_version = agent.version
        
        agent.update_timestamp()
        
        assert agent.updated_at > original_updated
        assert agent.version == original_version + 1
    
    def test_domain_events(self):
        """Test raising and managing domain events."""
        agent = Agent(name="Test Agent")
        
        # Initially no events
        assert len(agent.get_uncommitted_events()) == 0
        
        # Activate agent (raises event)
        agent.activate()
        
        # Should have events now
        events = agent.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], AgentCreatedEvent)
        assert events[0].aggregate_id == agent.id
        
        # Mark as committed
        agent.mark_events_as_committed()
        assert len(agent.get_uncommitted_events()) == 0


class TestAgent:
    """Test Agent entity functionality."""
    
    def test_agent_creation(self):
        """Test creating agents."""
        agent = Agent(
            name="Chat Agent",
            agent_type="conversational",
            configuration={"model": "gpt-4", "temperature": 0.7}
        )
        
        assert agent.name == "Chat Agent"
        assert agent.agent_type == "conversational"
        assert agent.status == "created"
        assert agent.configuration["model"] == "gpt-4"
    
    def test_agent_activation(self):
        """Test agent activation."""
        agent = Agent(name="Test Agent")
        assert agent.status == "created"
        
        agent.activate()
        assert agent.status == "active"
        
        # Should raise event
        events = agent.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], AgentCreatedEvent)
    
    def test_agent_pause(self):
        """Test agent pause."""
        agent = Agent(name="Test Agent")
        agent.activate()
        agent.mark_events_as_committed()
        
        agent.pause()
        assert agent.status == "paused"
    
    def test_agent_stop(self):
        """Test agent stop."""
        agent = Agent(name="Test Agent")
        agent.activate()
        
        agent.stop()
        assert agent.status == "stopped"
    
    def test_agent_lifecycle(self):
        """Test complete agent lifecycle."""
        agent = Agent(name="Test Agent")
        
        # Created -> Active
        agent.activate()
        assert agent.status == "active"
        
        # Active -> Paused
        agent.pause()
        assert agent.status == "paused"
        
        # Paused -> Stopped
        agent.stop()
        assert agent.status == "stopped"


class TestMessage:
    """Test Message entity functionality."""
    
    def test_message_creation(self):
        """Test creating messages."""
        message = Message(
            content="Hello, world!",
            sender_id="user-123",
            recipient_id="agent-456",
            message_type="text",
            metadata={"priority": "high"}
        )
        
        assert message.content == "Hello, world!"
        assert message.sender_id == "user-123"
        assert message.recipient_id == "agent-456"
        assert message.message_type == "text"
        assert message.metadata["priority"] == "high"
        assert not message.processed
    
    def test_message_processing(self):
        """Test message processing."""
        message = Message(
            content="Test message",
            sender_id="user-123",
            recipient_id="agent-456"
        )
        
        assert not message.processed
        
        message.mark_as_processed(processing_time_ms=150.5)
        assert message.processed
        
        # Should raise event
        events = message.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], MessageProcessedEvent)
        assert events[0].processing_time_ms == 150.5


class TestTool:
    """Test Tool entity functionality."""
    
    def test_tool_creation(self):
        """Test creating tools."""
        tool = Tool(
            name="file_reader",
            description="Read files from disk",
            parameters_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                }
            }
        )
        
        assert tool.name == "file_reader"
        assert tool.description == "Read files from disk"
        assert tool.enabled
        assert "path" in tool.parameters_schema["properties"]
    
    def test_tool_execution(self):
        """Test tool execution."""
        tool = Tool(name="calculator", description="Basic math")
        
        tool.execute(
            agent_id="agent-123",
            parameters={"operation": "add", "a": 2, "b": 3},
            result={"answer": 5},
            execution_time_ms=25.0
        )
        
        # Should raise event
        events = tool.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ToolExecutedEvent)
        assert events[0].tool_name == "calculator"
        assert events[0].agent_id == "agent-123"
        assert events[0].result["answer"] == 5


class TestSession:
    """Test Session entity functionality."""
    
    def test_session_creation(self):
        """Test creating sessions."""
        session = Session(
            user_id="user-123",
            session_type="user",
            metadata={"browser": "chrome"}
        )
        
        assert session.user_id == "user-123"
        assert session.session_type == "user"
        assert session.status == "active"
        assert session.end_time is None
        assert session.metadata["browser"] == "chrome"
    
    def test_session_end(self):
        """Test ending sessions."""
        session = Session(user_id="user-123")
        assert session.status == "active"
        assert session.end_time is None
        
        session.end_session()
        assert session.status == "ended"
        assert session.end_time is not None
    
    def test_session_duration(self):
        """Test session duration calculation."""
        session = Session(user_id="user-123")
        
        # Should have some duration even if not ended
        duration = session.duration_seconds
        assert duration >= 0
        
        # End session and check duration
        session.end_session()
        final_duration = session.duration_seconds
        assert final_duration >= duration