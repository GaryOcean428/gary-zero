"""End-to-end test scenarios for hierarchical planning capabilities.

This module contains test scenarios that validate the system's ability to execute
multi-step reasoning tasks with minimal manual intervention.
"""

import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from framework.helpers.enhanced_scheduler import EnhancedHierarchicalScheduler
from framework.helpers.hierarchical_planner import PlanStatus, SubtaskStatus
from framework.helpers.planner_config import PlannerSettings


class TestEndToEndScenarios:
    """Test end-to-end execution scenarios requiring multi-step reasoning."""
    
    @pytest.fixture
    def enhanced_scheduler(self):
        """Create an enhanced scheduler for testing."""
        return EnhancedHierarchicalScheduler()
    
    def test_battery_technology_research_scenario(self, enhanced_scheduler):
        """Test the battery technology research scenario.
        
        This should:
        1. Research the latest battery technologies
        2. Summarize findings
        3. Generate a slide deck
        """
        objective = "Research the latest battery technologies, summarize findings, and generate a slide deck"
        
        # Create plan
        plan = enhanced_scheduler.create_and_execute_plan(
            objective=objective,
            context_id="test_context",
            auto_execute=False  # Don't auto-execute for testing
        )
        
        # Verify plan structure
        assert plan is not None
        assert plan.objective == objective
        assert len(plan.subtasks) >= 4  # Should have multiple research steps
        
        # Verify expected subtasks are present
        subtask_names = [s.name.lower() for s in plan.subtasks]
        assert any("search" in name for name in subtask_names)
        assert any("summary" in name or "compile" in name for name in subtask_names)
        
        # Verify tool assignments
        assigned_tools = {s.tool_name for s in plan.subtasks if s.tool_name}
        expected_tools = {"search_engine", "webpage_content_tool", "knowledge_tool", "response"}
        assert len(assigned_tools.intersection(expected_tools)) >= 2
        
        # Verify dependency structure
        dependent_tasks = [s for s in plan.subtasks if s.dependencies]
        assert len(dependent_tasks) > 0
        
        # Check specific subtask patterns for battery research
        subtask_descriptions = " ".join([s.description.lower() for s in plan.subtasks])
        assert "battery" in subtask_descriptions
        assert "technolog" in subtask_descriptions  # Match both "technology" and "technologies"
        
        return plan
    
    def test_ai_paper_analysis_scenario(self, enhanced_scheduler):
        """Test AI paper analysis scenario.
        
        This should:
        1. Gather recent AI papers about CoT prompting
        2. Analyze the papers
        3. Summarize findings
        """
        objective = "Gather and summarize five recent AI papers about CoT prompting"
        
        plan = enhanced_scheduler.create_and_execute_plan(
            objective=objective,
            context_id="test_context",
            auto_execute=False
        )
        
        # Verify plan structure
        assert plan is not None
        assert len(plan.subtasks) >= 3
        
        # Check for research-specific patterns
        subtask_text = " ".join([s.name + " " + s.description for s in plan.subtasks]).lower()
        assert "search" in subtask_text or "gather" in subtask_text
        assert "summarize" in subtask_text or "analyze" in subtask_text
        
        # Verify appropriate tools are assigned
        assigned_tools = {s.tool_name for s in plan.subtasks if s.tool_name}
        research_tools = {"search_engine", "webpage_content_tool", "knowledge_tool"}
        assert len(assigned_tools.intersection(research_tools)) >= 1
        
        return plan
    
    def test_software_development_scenario(self, enhanced_scheduler):
        """Test software development scenario.
        
        This should create a structured plan for building a React dashboard.
        """
        objective = "Create a React dashboard with real-time data visualization"
        
        plan = enhanced_scheduler.create_and_execute_plan(
            objective=objective,
            context_id="test_context", 
            auto_execute=False
        )
        
        # Verify plan structure
        assert plan is not None
        assert len(plan.subtasks) >= 3
        
        # Check for development-specific patterns
        subtask_text = " ".join([s.name + " " + s.description for s in plan.subtasks]).lower()
        
        # Should have planning/design phases
        assert any(word in subtask_text for word in ["scope", "outline", "design", "plan"])
        
        # Should have implementation phases  
        assert any(word in subtask_text for word in ["create", "implement", "build", "develop"])
        
        # Should use code execution tools
        assigned_tools = {s.tool_name for s in plan.subtasks if s.tool_name}
        assert "code_execution_tool" in assigned_tools
        
        return plan
    
    @patch('framework.helpers.task_management.TaskScheduler')
    def test_plan_execution_with_scheduler(self, mock_scheduler_class, enhanced_scheduler):
        """Test plan execution integration with TaskScheduler."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.get.return_value = mock_scheduler
        
        objective = "Research AI developments and create summary"
        
        # Create and execute plan
        plan = enhanced_scheduler.create_and_execute_plan(
            objective=objective,
            context_id="test_context",
            auto_execute=True
        )
        
        # Verify plan was created and execution started
        assert plan.status == PlanStatus.IN_PROGRESS
        assert len(plan.subtasks) > 0
        
        # Verify tasks were scheduled
        assert mock_scheduler.add_task.call_count == len(plan.subtasks)
        
        # Check that tasks were created with enhanced prompts
        added_tasks = [call.args[0] for call in mock_scheduler.add_task.call_args_list]
        for task in added_tasks:
            assert "hierarchical plan" in task.system_prompt.lower()
            assert "evaluation" in task.prompt.lower() or "guidelines" in task.prompt.lower()
    
    def test_enhanced_configuration_integration(self, enhanced_scheduler):
        """Test configuration integration with enhanced features."""
        # Test default configuration
        config = enhanced_scheduler.config
        assert config.auto_planning_enabled is True
        assert config.verification_enabled is True
        assert config.retry_failed_subtasks is True
        
        # Test configuration update
        new_config = enhanced_scheduler.update_configuration(
            max_subtasks=15,
            verification_enabled=False
        )
        
        assert new_config["max_subtasks"] == 15
        assert new_config["verification_enabled"] is False
        assert enhanced_scheduler.config.max_subtasks == 15
        assert enhanced_scheduler.config.verification_enabled is False
    
    def test_plan_status_monitoring(self, enhanced_scheduler):
        """Test enhanced plan status monitoring."""
        objective = "Test objective for monitoring"
        
        plan = enhanced_scheduler.create_and_execute_plan(
            objective=objective,
            auto_execute=False
        )
        
        # Get enhanced status
        status = enhanced_scheduler.get_enhanced_plan_status(plan.id)
        
        assert status is not None
        assert status["plan_id"] == plan.id
        assert status["objective"] == objective
        assert "subtask_details" in status
        assert "evaluation_enabled" in status
        assert "retry_enabled" in status
        
        # Verify subtask details
        subtask_details = status["subtask_details"]
        assert len(subtask_details) == len(plan.subtasks)
        
        for detail in subtask_details:
            assert "id" in detail
            assert "name" in detail
            assert "status" in detail
            assert "tool" in detail
            assert detail["status"] == SubtaskStatus.PENDING.value
    
    def test_evaluation_criteria_application(self, enhanced_scheduler):
        """Test that evaluation criteria are properly applied."""
        # Create a plan
        plan = enhanced_scheduler.create_and_execute_plan(
            "Research and analyze data about machine learning",
            auto_execute=False
        )
        
        # Test evaluation on a mock subtask completion
        subtask = plan.subtasks[0]
        
        # Simulate good output
        good_output = "Found comprehensive research on machine learning including 10 relevant papers with detailed analysis of neural networks, deep learning architectures, and recent advances in transformer models. Sources include: https://arxiv.org/abs/2023.12345, https://nature.com/articles/ml2023"
        
        evaluation = enhanced_scheduler.monitor.evaluation_loop.evaluator.evaluate_subtask_output(
            subtask, good_output
        )
        
        assert evaluation.success is True
        assert evaluation.score > 0.7  # Should be high quality
        
        # Test poor output
        poor_output = "No results"
        
        evaluation = enhanced_scheduler.monitor.evaluation_loop.evaluator.evaluate_subtask_output(
            subtask, poor_output
        )
        
        assert evaluation.score < 0.5  # Should be low quality
    
    def test_tool_selection_appropriateness(self, enhanced_scheduler):
        """Test that appropriate tools are selected for different subtask types."""
        test_scenarios = [
            {
                "objective": "Research latest developments in quantum computing",
                "expected_tools": ["search_engine", "webpage_content_tool"],
                "keywords": ["search", "research", "quantum"]
            },
            {
                "objective": "Create a Python script for data analysis",
                "expected_tools": ["code_execution_tool"],
                "keywords": ["create", "script", "python"]
            },
            {
                "objective": "Analyze and summarize customer feedback data",
                "expected_tools": ["knowledge_tool", "code_execution_tool"],
                "keywords": ["analyze", "summarize", "data"]
            }
        ]
        
        for scenario in test_scenarios:
            plan = enhanced_scheduler.create_and_execute_plan(
                scenario["objective"],
                auto_execute=False
            )
            
            # Check tool assignments
            assigned_tools = {s.tool_name for s in plan.subtasks if s.tool_name}
            expected_tools = set(scenario["expected_tools"])
            
            # Should use at least one of the expected tools
            assert len(assigned_tools.intersection(expected_tools)) > 0, f"No expected tools found for: {scenario['objective']}"
            
            # Check that subtasks mention relevant keywords
            subtask_text = " ".join([s.description.lower() for s in plan.subtasks])
            keyword_matches = sum(1 for keyword in scenario["keywords"] if keyword in subtask_text)
            assert keyword_matches >= len(scenario["keywords"]) // 2, f"Not enough keyword matches for: {scenario['objective']}"


class TestPerformanceMetrics:
    """Test scenarios for validating success metrics."""
    
    def test_appropriate_tool_selection_rate(self):
        """Test that appropriate tools are selected in ≥80% of test runs."""
        enhanced_scheduler = EnhancedHierarchicalScheduler()
        
        test_objectives = [
            ("Research artificial intelligence trends", ["search_engine", "webpage_content_tool"]),
            ("Create a data visualization", ["code_execution_tool"]),
            ("Analyze text documents", ["knowledge_tool", "code_execution_tool"]),
            ("Search for academic papers", ["search_engine", "webpage_content_tool"]),
            ("Generate a report", ["response", "knowledge_tool"]),
            ("Build a web application", ["code_execution_tool"]),
            ("Summarize research findings", ["knowledge_tool", "response"]),
            ("Find latest news articles", ["search_engine", "webpage_content_tool"]),
            ("Process and analyze data", ["code_execution_tool", "knowledge_tool"]),
            ("Create presentation slides", ["code_execution_tool", "response"])
        ]
        
        appropriate_selections = 0
        total_tests = len(test_objectives)
        
        for objective, expected_tools in test_objectives:
            plan = enhanced_scheduler.create_and_execute_plan(
                objective,
                auto_execute=False
            )
            
            assigned_tools = {s.tool_name for s in plan.subtasks if s.tool_name}
            expected_set = set(expected_tools)
            
            # Consider it appropriate if at least one expected tool is used
            if len(assigned_tools.intersection(expected_set)) > 0:
                appropriate_selections += 1
        
        success_rate = appropriate_selections / total_tests
        assert success_rate >= 0.8, f"Tool selection success rate {success_rate:.2%} is below 80% threshold"
    
    def test_minimal_manual_intervention_required(self):
        """Test that plans can execute with minimal manual intervention."""
        enhanced_scheduler = EnhancedHierarchicalScheduler()
        
        # Test complex objectives that should decompose into clear subtasks
        complex_objectives = [
            "Research the latest battery technologies, summarize findings, and generate a slide deck",
            "Gather and summarize five recent AI papers about chain-of-thought prompting",
            "Analyze customer feedback data and create a dashboard with recommendations"
        ]
        
        for objective in complex_objectives:
            plan = enhanced_scheduler.create_and_execute_plan(
                objective,
                auto_execute=False
            )
            
            # Verify plan has clear structure
            assert len(plan.subtasks) >= 3, f"Plan too simple for: {objective}"
            assert len(plan.subtasks) <= enhanced_scheduler.config.max_subtasks, f"Plan too complex for: {objective}"
            
            # Verify dependencies are reasonable (not every task depends on every other task)
            total_dependencies = sum(len(s.dependencies) for s in plan.subtasks)
            max_reasonable_deps = len(plan.subtasks) * 2  # Reasonable heuristic
            assert total_dependencies <= max_reasonable_deps, f"Too many dependencies for: {objective}"
            
            # Verify all dependencies are valid
            for subtask in plan.subtasks:
                for dep_id in subtask.dependencies:
                    assert plan.get_subtask_by_id(dep_id) is not None, f"Invalid dependency in plan for: {objective}"
    
    def test_plan_decomposition_quality(self):
        """Test the quality of plan decomposition."""
        enhanced_scheduler = EnhancedHierarchicalScheduler()
        
        # Test that plans have logical progression
        objective = "Research renewable energy technologies and create an investment recommendation"
        plan = enhanced_scheduler.create_and_execute_plan(objective, auto_execute=False)
        
        # Should have research phases before analysis phases
        research_indices = []
        analysis_indices = []
        
        for i, subtask in enumerate(plan.subtasks):
            description = subtask.description.lower()
            if any(word in description for word in ["search", "research", "find", "gather"]):
                research_indices.append(i)
            elif any(word in description for word in ["analyze", "synthesize", "recommend", "create"]):
                analysis_indices.append(i)
        
        # Research should generally come before analysis
        if research_indices and analysis_indices:
            avg_research_pos = sum(research_indices) / len(research_indices)
            avg_analysis_pos = sum(analysis_indices) / len(analysis_indices)
            assert avg_research_pos < avg_analysis_pos, "Analysis should generally come after research"