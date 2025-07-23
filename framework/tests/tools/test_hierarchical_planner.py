"""Tests for the hierarchical planner functionality."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from framework.helpers.hierarchical_planner import (
    HierarchicalPlanner,
    HierarchicalPlan,
    Subtask,
    SubtaskStatus,
    PlanStatus,
    PlanningConfig
)
from framework.helpers.plan_evaluation import (
    PlanEvaluator,
    EvaluationResult,
    EvaluationCriteria,
    PlanAdjuster,
    EvaluationLoop
)
from framework.tools.planning_tool import PlanningTool


class TestHierarchicalPlanner:
    """Test cases for the HierarchicalPlanner class."""
    
    def test_create_plan_basic(self):
        """Test basic plan creation."""
        planner = HierarchicalPlanner()
        objective = "Research battery technologies and create a summary"
        
        plan = planner.create_plan(objective)
        
        assert plan is not None
        assert plan.objective == objective
        assert plan.status == PlanStatus.PENDING
        assert len(plan.subtasks) > 0
        assert plan.id in planner.active_plans
    
    def test_create_plan_with_context(self):
        """Test plan creation with context ID."""
        planner = HierarchicalPlanner()
        objective = "Test objective"
        context_id = "test_context_123"
        
        plan = planner.create_plan(objective, context_id)
        
        assert plan.context_id == context_id
    
    def test_battery_research_decomposition(self):
        """Test decomposition of battery research objective."""
        planner = HierarchicalPlanner()
        objective = "Research the latest battery technologies and summarize findings"
        
        plan = planner.create_plan(objective)
        
        assert len(plan.subtasks) >= 4  # Should have multiple research subtasks
        
        # Check for expected subtask types
        subtask_names = [s.name.lower() for s in plan.subtasks]
        assert any("search" in name for name in subtask_names)
        assert any("lithium" in name for name in subtask_names)
        assert any("summary" in name or "compile" in name for name in subtask_names)
    
    def test_presentation_plan_decomposition(self):
        """Test decomposition of presentation creation objective."""
        planner = HierarchicalPlanner()
        objective = "Create a slide deck about machine learning"
        
        plan = planner.create_plan(objective)
        
        assert len(plan.subtasks) >= 3
        
        # Check for presentation-specific subtasks
        subtask_names = [s.name.lower() for s in plan.subtasks]
        assert any("scope" in name or "outline" in name for name in subtask_names)
        assert any("slide" in name for name in subtask_names)
    
    def test_get_next_subtask(self):
        """Test getting the next executable subtask."""
        planner = HierarchicalPlanner()
        plan = planner.create_plan("Test objective")
        
        # Should get first subtask with no dependencies
        next_task = plan.get_next_subtask()
        assert next_task is not None
        assert next_task.status == SubtaskStatus.PENDING
        assert len(next_task.dependencies) == 0
    
    def test_subtask_dependencies(self):
        """Test that subtask dependencies are properly set."""
        planner = HierarchicalPlanner()
        plan = planner.create_plan("Research and summarize AI papers")
        
        # Check that later subtasks depend on earlier ones
        dependent_subtasks = [s for s in plan.subtasks if len(s.dependencies) > 0]
        assert len(dependent_subtasks) > 0
        
        # Verify dependency relationships are valid
        for subtask in dependent_subtasks:
            for dep_id in subtask.dependencies:
                dep_subtask = plan.get_subtask_by_id(dep_id)
                assert dep_subtask is not None
    
    def test_plan_progress_tracking(self):
        """Test plan progress tracking methods."""
        planner = HierarchicalPlanner()
        plan = planner.create_plan("Test objective")
        
        # Initially no subtasks should be completed
        assert not plan.is_complete()
        assert not plan.has_failed_subtasks()
        
        progress = plan.get_progress_summary()
        assert progress[SubtaskStatus.PENDING.value] == len(plan.subtasks)
        assert progress[SubtaskStatus.COMPLETED.value] == 0
        
        # Mark first subtask as completed
        if plan.subtasks:
            plan.subtasks[0].mark_completed("Test result")
            progress = plan.get_progress_summary()
            assert progress[SubtaskStatus.COMPLETED.value] == 1
    
    @patch('framework.helpers.task_scheduler.TaskScheduler')
    def test_execute_plan(self, mock_scheduler_class):
        """Test plan execution."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.get.return_value = mock_scheduler
        
        planner = HierarchicalPlanner()
        plan = planner.create_plan("Test objective")
        
        result = planner.execute_plan(plan.id)
        
        assert result is True
        assert plan.status == PlanStatus.IN_PROGRESS
        
        # Verify tasks were added to scheduler
        assert mock_scheduler.add_task.call_count == len(plan.subtasks)


class TestPlanEvaluator:
    """Test cases for the PlanEvaluator class."""
    
    def test_evaluate_successful_output(self):
        """Test evaluation of successful subtask output."""
        evaluator = PlanEvaluator()
        subtask = Subtask(
            id="test_id",
            name="Test task",
            description="Test description",
            tool_name="search_engine"
        )
        
        output = "Found 5 relevant results about battery technology: http://example.com/battery1"
        result = evaluator.evaluate_subtask_output(subtask, output)
        
        assert result.success is True
        assert result.score > 0.5
        assert "http" in output  # Should detect URLs
    
    def test_evaluate_failed_output(self):
        """Test evaluation of failed subtask output."""
        evaluator = PlanEvaluator()
        subtask = Subtask(
            id="test_id",
            name="Test task",
            description="Test description"
        )
        
        # Empty output should fail
        result = evaluator.evaluate_subtask_output(subtask, "")
        
        assert result.success is False
        assert result.score == 0.0
        assert result.requires_retry is True
    
    def test_evaluate_with_criteria(self):
        """Test evaluation with specific criteria."""
        evaluator = PlanEvaluator()
        subtask = Subtask(
            id="test_id",
            name="Test task",
            description="Test description"
        )
        
        criteria = EvaluationCriteria(
            min_length=50,
            required_keywords=["battery", "technology"],
            expected_format="json"
        )
        
        # Short output missing keywords
        output = "Short response"
        result = evaluator.evaluate_subtask_output(subtask, output, criteria)
        
        assert result.success is False
        assert "too short" in result.feedback.lower()
        assert "missing required keywords" in result.feedback.lower()
    
    def test_tool_specific_evaluation(self):
        """Test tool-specific evaluation logic."""
        evaluator = PlanEvaluator()
        
        # Test search engine evaluation
        search_subtask = Subtask(
            id="search_id",
            name="Search",
            description="Search for information",
            tool_name="search_engine"
        )
        
        good_search = "Found 10 results: http://example.com"
        result = evaluator.evaluate_subtask_output(search_subtask, good_search)
        assert result.score > 0.6
        
        bad_search = "No results found"
        result = evaluator.evaluate_subtask_output(search_subtask, bad_search)
        assert result.score < 0.5
    
    def test_evaluation_history(self):
        """Test that evaluation history is stored."""
        evaluator = PlanEvaluator()
        subtask = Subtask(
            id="test_id",
            name="Test task",
            description="Test description"
        )
        
        # Evaluate multiple times
        evaluator.evaluate_subtask_output(subtask, "First result")
        evaluator.evaluate_subtask_output(subtask, "Second result")
        
        assert subtask.id in evaluator.evaluation_history
        assert len(evaluator.evaluation_history[subtask.id]) == 2


class TestPlanAdjuster:
    """Test cases for the PlanAdjuster class."""
    
    def test_retry_with_alternative_tool(self):
        """Test retrying with alternative tool."""
        evaluator = PlanEvaluator()
        adjuster = PlanAdjuster(evaluator)
        
        plan = HierarchicalPlan(
            id="test_plan",
            objective="Test objective",
            subtasks=[
                Subtask(
                    id="subtask1",
                    name="Failed task",
                    description="This task failed",
                    tool_name="search_engine"
                )
            ]
        )
        
        failed_subtask = plan.subtasks[0]
        evaluation_result = EvaluationResult(
            success=False,
            score=0.3,
            feedback="Search failed",
            requires_retry=True,
            alternative_tool="webpage_content_tool"
        )
        
        result = adjuster.adjust_plan_after_failure(plan, failed_subtask, evaluation_result)
        
        assert result is True
        assert len(plan.subtasks) == 2  # Original + retry
        assert plan.subtasks[1].tool_name == "webpage_content_tool"
        assert failed_subtask.status == SubtaskStatus.SKIPPED
    
    def test_split_complex_subtask(self):
        """Test splitting complex subtasks."""
        evaluator = PlanEvaluator()
        adjuster = PlanAdjuster(evaluator)
        
        plan = HierarchicalPlan(
            id="test_plan", 
            objective="Test objective",
            subtasks=[
                Subtask(
                    id="complex_task",
                    name="Complex task",
                    description="Do task A and also do task B and then do task C",
                    tool_name="code_execution_tool"
                )
            ]
        )
        
        failed_subtask = plan.subtasks[0]
        evaluation_result = EvaluationResult(
            success=False,
            score=0.2,
            feedback="Task too complex",
            requires_retry=True
        )
        
        result = adjuster.adjust_plan_after_failure(plan, failed_subtask, evaluation_result)
        
        assert result is True
        assert len(plan.subtasks) > 1  # Should be split into multiple tasks
        assert failed_subtask.status == SubtaskStatus.SKIPPED


class TestEvaluationLoop:
    """Test cases for the EvaluationLoop class."""
    
    def test_process_successful_completion(self):
        """Test processing successful subtask completion."""
        loop = EvaluationLoop()
        
        plan = HierarchicalPlan(
            id="test_plan",
            objective="Test objective",
            subtasks=[
                Subtask(
                    id="test_subtask",
                    name="Test task",
                    description="Test description"
                )
            ]
        )
        
        subtask = plan.subtasks[0]
        output = "This is a good result with sufficient detail"
        
        result = loop.process_subtask_completion(plan, subtask, output)
        
        assert result is True
        assert subtask.status == SubtaskStatus.COMPLETED
        assert subtask.result == output
    
    def test_process_failed_completion_with_adjustment(self):
        """Test processing failed completion that gets adjusted."""
        loop = EvaluationLoop()
        
        plan = HierarchicalPlan(
            id="test_plan",
            objective="Test objective", 
            subtasks=[
                Subtask(
                    id="test_subtask",
                    name="Test task",
                    description="Search for information and gather data",
                    tool_name="search_engine"
                )
            ]
        )
        
        subtask = plan.subtasks[0]
        output = "No results"  # This should trigger failure and adjustment
        
        result = loop.process_subtask_completion(plan, subtask, output)
        
        # Should return False indicating plan was adjusted
        assert result is False


class TestPlanningTool:
    """Test cases for the PlanningTool class."""
    
    @pytest.fixture
    def planning_tool(self):
        """Create a PlanningTool instance for testing."""
        tool = PlanningTool(
            agent=MagicMock(),
            name="planning_tool",
            method="create_plan"
        )
        tool.agent.context.id = "test_context"
        return tool
    
    @pytest.mark.asyncio
    async def test_create_plan_success(self, planning_tool):
        """Test successful plan creation through tool."""
        planning_tool.method = "create_plan"
        
        response = await planning_tool.execute(
            objective="Research AI developments and create summary"
        )
        
        assert response.break_loop is False
        assert "Created hierarchical plan" in response.message
        assert "subtasks" in response.message
    
    @pytest.mark.asyncio
    async def test_create_plan_missing_objective(self, planning_tool):
        """Test plan creation with missing objective."""
        planning_tool.method = "create_plan"
        
        response = await planning_tool.execute()
        
        assert "Objective is required" in response.message
    
    @pytest.mark.asyncio
    async def test_get_plan_status(self, planning_tool):
        """Test getting plan status."""
        # First create a plan
        planning_tool.method = "create_plan"
        create_response = await planning_tool.execute(
            objective="Test objective"
        )
        
        # Extract plan ID from response
        plan_id = None
        for plan_id, plan in planning_tool.planner.active_plans.items():
            break
        
        # Now get status
        planning_tool.method = "get_plan_status"
        response = await planning_tool.execute(plan_id=plan_id)
        
        assert response.break_loop is False
        assert "Plan Status" in response.message
        assert "Test objective" in response.message
    
    @pytest.mark.asyncio
    async def test_list_plans(self, planning_tool):
        """Test listing plans."""
        # Create a couple of plans first
        planning_tool.method = "create_plan"
        await planning_tool.execute(objective="First objective")
        await planning_tool.execute(objective="Second objective")
        
        # List plans
        planning_tool.method = "list_plans"
        response = await planning_tool.execute()
        
        assert response.break_loop is False
        assert "Active Plans" in response.message
        assert "First objective" in response.message
        assert "Second objective" in response.message
    
    @pytest.mark.asyncio
    async def test_configure_planner(self, planning_tool):
        """Test planner configuration."""
        planning_tool.method = "configure_planner"
        
        # Test getting current config
        response = await planning_tool.execute()
        assert "Current Planner Configuration" in response.message
        
        # Test updating config
        response = await planning_tool.execute(
            auto_planning_enabled=False,
            max_subtasks=5
        )
        assert "configuration updated" in response.message
        assert "auto_planning_enabled: False" in response.message


# Integration test data for end-to-end scenarios
TEST_SCENARIOS = [
    {
        "name": "Battery Technology Research",
        "objective": "Research the latest battery technologies, summarize findings, and generate a slide deck",
        "expected_subtasks": ["search", "lithium", "solid-state", "summary", "slide"],
        "expected_tools": ["search_engine", "webpage_content_tool", "code_execution_tool"]
    },
    {
        "name": "AI Paper Analysis", 
        "objective": "Gather and summarize five recent AI papers about CoT prompting",
        "expected_subtasks": ["search", "gather", "analyze", "summarize"],
        "expected_tools": ["search_engine", "webpage_content_tool", "knowledge_tool"]
    },
    {
        "name": "Software Development",
        "objective": "Create a React dashboard with real-time data visualization",
        "expected_subtasks": ["scope", "outline", "create", "format"],
        "expected_tools": ["code_execution_tool"]
    }
]


class TestIntegrationScenarios:
    """Integration tests for complete planning scenarios."""
    
    @pytest.mark.parametrize("scenario", TEST_SCENARIOS)
    def test_end_to_end_planning(self, scenario):
        """Test end-to-end planning for different scenarios."""
        planner = HierarchicalPlanner()
        
        plan = planner.create_plan(scenario["objective"])
        
        # Verify plan structure
        assert plan is not None
        assert len(plan.subtasks) >= 3  # Should have multiple steps
        
        # Check for expected subtask patterns
        subtask_text = " ".join([s.name + " " + s.description for s in plan.subtasks]).lower()
        
        expected_found = 0
        for expected in scenario["expected_subtasks"]:
            if expected.lower() in subtask_text:
                expected_found += 1
        
        # Should find at least half of expected subtasks
        assert expected_found >= len(scenario["expected_subtasks"]) // 2
        
        # Check tool assignments
        assigned_tools = {s.tool_name for s in plan.subtasks if s.tool_name}
        expected_tools = set(scenario["expected_tools"])
        
        # Should use some of the expected tools
        assert len(assigned_tools.intersection(expected_tools)) > 0
        
        # Verify dependency structure
        dependent_tasks = [s for s in plan.subtasks if s.dependencies]
        assert len(dependent_tasks) > 0  # Should have some dependencies
        
        # Verify all dependencies are valid
        for subtask in dependent_tasks:
            for dep_id in subtask.dependencies:
                assert plan.get_subtask_by_id(dep_id) is not None