"""Global pytest configuration and fixtures."""

import os
import sys
from unittest.mock import MagicMock

import pytest

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing tools."""
    agent = MagicMock()
    agent.agent_name = "test_agent"
    agent.context = MagicMock()
    agent.context.id = "test_context_id"
    agent.context.log = MagicMock()
    agent.context.log.log = MagicMock()
    agent.hist_add_tool_result = MagicMock()
    return agent


@pytest.fixture
def mock_tool_args():
    """Standard tool arguments for testing."""
    return {
        "name": "test_tool",
        "method": "test_method",
        "args": {},
        "message": "test message",
    }
