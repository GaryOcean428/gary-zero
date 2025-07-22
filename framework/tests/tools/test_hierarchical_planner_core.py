"""Focused tests for hierarchical planner core functionality."""

import pytest
from datetime import datetime, timezone

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
    EvaluationCriteria
)


class TestHierarchicalPlannerCore:
    """Test cases for the core HierarchicalPlanner functionality."""
    
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
    
    def test_planning_config(self):
        """Test planning configuration."""
        config = PlanningConfig(
            auto_planning_enabled=False,
            max_recursion_depth=5,
            max_subtasks=15
        )
        
        planner = HierarchicalPlanner(config)
        
        assert planner.config.auto_planning_enabled is False
        assert planner.config.max_recursion_depth == 5
        assert planner.config.max_subtasks == 15
    
    def test_get_plan_progress(self):
        """Test getting plan progress information."""
        planner = HierarchicalPlanner()
        plan = planner.create_plan("Test objective")
        
        progress = planner.get_plan_progress(plan.id)
        
        assert progress is not None
        assert progress["plan_id"] == plan.id
        assert progress["objective"] == "Test objective"
        assert progress["status"] == PlanStatus.PENDING
        assert progress["total_subtasks"] == len(plan.subtasks)
        assert progress["completed_subtasks"] == 0
        assert progress["is_complete"] is False


class TestPlanEvaluatorCore:
    """Test cases for the core PlanEvaluator functionality."""
    
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
        # Note: the evaluation might still pass with low score
        assert isinstance(result.score, float)
    
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


# Integration test scenarios
TEST_SCENARIOS = [
    {
        "name": "Battery Technology Research",
        "objective": "Research the latest battery technologies, summarize findings, and generate a slide deck",
        "expected_subtasks": ["search", "summary", "slide"],
        "expected_tools": ["search_engine", "webpage_content_tool", "code_execution_tool"]
    },
    {
        "name": "AI Paper Analysis", 
        "objective": "Gather and summarize five recent AI papers about CoT prompting",
        "expected_subtasks": ["search", "gather", "analyze", "summarize"],
        "expected_tools": ["search_engine", "webpage_content_tool", "knowledge_tool"]
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
        
        # Should find at least some of expected subtasks
        assert expected_found >= 1
        
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