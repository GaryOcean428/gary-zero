"""Tests for the scheduler tool."""

import os
import sys
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from framework.helpers.task_scheduler import PlannedTask
from framework.tools.scheduler import SchedulerTool

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestSchedulerTool:
    """Test cases for the SchedulerTool class."""

    @pytest.fixture
    def scheduler_tool(self, mock_agent, mock_tool_args):
        """Fixture to create a SchedulerTool instance with a mock agent."""
        return SchedulerTool(agent=mock_agent, **mock_tool_args)

    @pytest.fixture
    def mock_task_scheduler(self):
        """Fixture to mock the TaskScheduler singleton."""
        with patch("framework.helpers.task_scheduler.TaskScheduler") as mock_scheduler:
            mock_instance = mock_scheduler.get.return_value
            yield mock_instance

    @pytest.mark.asyncio
    async def test_create_planned_task_success(
        self, scheduler_tool, mock_task_scheduler
    ):
        """Test successful creation of a planned task."""
        # Setup test data
        task_name = "test_task"
        system_prompt = "Test system prompt"
        prompt = "Test prompt"
        future_time = datetime.now(UTC) + timedelta(hours=1)
        plan = [future_time.isoformat()]
        attachments = ["file1.txt"]

        # Mock the task scheduler
        mock_task = MagicMock(spec=PlannedTask)
        mock_task_scheduler.add_task.return_value = "test_task_id"
        mock_task_scheduler.get_task.return_value = mock_task

        # Call the method under test
        result = await scheduler_tool.create_planned_task(
            name=task_name,
            system_prompt=system_prompt,
            prompt=prompt,
            plan=plan,
            attachments=attachments,
            dedicated_context=False,
        )

        # Verify the result
        assert result.message == "Task created and scheduled: test_task_id"
        assert result.break_loop is False

        # Verify the task was added to the scheduler
        mock_task_scheduler.add_task.assert_called_once()
        added_task = mock_task_scheduler.add_task.call_args[0][0]
        assert isinstance(added_task, PlannedTask)
        assert added_task.name == task_name
        assert added_task.system_prompt == system_prompt
        assert added_task.prompt == prompt
        assert len(added_task.plan.todo) == 1
        assert added_task.context_id == "test_context_id"

    @pytest.mark.asyncio
    async def test_create_planned_task_dedicated_context(
        self, scheduler_tool, mock_task_scheduler
    ):
        """Test creating a planned task with dedicated context."""
        # Setup test data
        future_time = datetime.now(UTC) + timedelta(hours=1)
        plan = [future_time.isoformat()]

        # Mock the task scheduler
        mock_task_scheduler.add_task.return_value = "test_task_id"

        # Call the method under test with dedicated_context=True
        await scheduler_tool.create_planned_task(
            name="test_task",
            system_prompt="Test",
            prompt="Test",
            plan=plan,
            dedicated_context=True,
        )

        # Verify the task was created with no context_id
        added_task = mock_task_scheduler.add_task.call_args[0][0]
        assert added_task.context_id is None

    @pytest.mark.asyncio
    async def test_create_planned_task_invalid_plan(
        self, scheduler_tool, mock_task_scheduler
    ):
        """Test creating a planned task with an invalid plan."""
        # Call with invalid datetime string
        result = await scheduler_tool.create_planned_task(
            name="test_task",
            system_prompt="Test",
            prompt="Test",
            plan=["not-a-valid-datetime"],
            dedicated_context=False,
        )

        # Verify error response
        assert "Invalid datetime string in plan" in result.message
        assert result.break_loop is False
        mock_task_scheduler.add_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_tasks(self, scheduler_tool, mock_task_scheduler):
        """Test listing scheduled tasks."""
        # Setup mock tasks
        mock_task1 = MagicMock()
        mock_task1.name = "task1"
        mock_task1.task_id = "id1"
        mock_task1.state = "PENDING"
        mock_task1.next_run = datetime.now(UTC)
        mock_task1.context_id = "test_context_id"

        mock_task2 = MagicMock()
        mock_task2.name = "task2"
        mock_task2.task_id = "id2"
        mock_task2.state = "SCHEDULED"
        mock_task2.next_run = datetime.now(UTC) + timedelta(hours=1)
        mock_task2.context_id = "other_context_id"

        mock_task_scheduler.get_tasks.return_value = [mock_task1, mock_task2]

        # Call the method under test
        result = await scheduler_tool.list_tasks()

        # Verify the result
        assert "task1" in result.message
        assert (
            "task2" not in result.message
        )  # Should only show tasks in current context
        assert "PENDING" in result.message
        assert result.break_loop is False
