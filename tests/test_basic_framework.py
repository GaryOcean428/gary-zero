"""Simple unit tests for core framework components."""

from unittest.mock import MagicMock

import pytest


# Test basic functionality of the framework
class TestBasicFramework:
    """Test basic framework functionality."""

    def test_response_creation(self):
        """Test Response object creation."""
        from framework.helpers.tool import Response

        response = Response(message="test", break_loop=False)
        assert response.message == "test"
        assert response.break_loop is False

    def test_tool_creation(self):
        """Test Tool base class instantiation."""
        from framework.helpers.tool import Tool

        # Create a concrete implementation for testing
        class TestTool(Tool):
            async def execute(self, **kwargs):
                from framework.helpers.tool import Response
                return Response(message="test executed", break_loop=False)

        mock_agent = MagicMock()
        mock_agent.agent_name = "test_agent"
        mock_agent.context = MagicMock()

        tool = TestTool(
            agent=mock_agent,
            name="test_tool",
            method="test_method",
            args={},
            message="test message"
        )

        assert tool.name == "test_tool"
        assert tool.method == "test_method"
        assert tool.agent == mock_agent

    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """Test tool execution."""
        from framework.helpers.tool import Response, Tool

        class TestTool(Tool):
            async def execute(self, **kwargs):
                return Response(message="test executed", break_loop=False)

        mock_agent = MagicMock()
        mock_agent.agent_name = "test_agent"
        mock_agent.context = MagicMock()
        mock_agent.context.log = MagicMock()
        mock_agent.context.log.log = MagicMock()
        mock_agent.hist_add_tool_result = MagicMock()

        tool = TestTool(
            agent=mock_agent,
            name="test_tool",
            method="test_method",
            args={},
            message="test message"
        )

        result = await tool.execute()
        assert isinstance(result, Response)
        assert result.message == "test executed"
        assert result.break_loop is False
