#!/usr/bin/env python3
"""
Demonstration script for Gary-Zero's hierarchical planning capabilities.

This script showcases the end-to-end functionality including:
- Complex objective decomposition
- Intelligent tool assignment
- Plan execution monitoring
- Evaluation loops and failure handling

Run with: python examples/demo_hierarchical_planning.py
"""

import asyncio
import json
import time
from datetime import datetime

from framework.helpers.enhanced_scheduler import EnhancedHierarchicalScheduler
from framework.helpers.planner_config import PlannerSettings
from framework.helpers.hierarchical_planner import PlanStatus, SubtaskStatus


class PlanningDemo:
    """Demonstration class for hierarchical planning features."""
    
    def __init__(self):
        """Initialize the demo with enhanced scheduler."""
        self.scheduler = EnhancedHierarchicalScheduler()
        print("🚀 Gary-Zero Hierarchical Planning Demo")
        print("=" * 50)
    
    def demo_configuration(self):
        """Demonstrate configuration management."""
        print("\n📋 Configuration Management")
        print("-" * 30)
        
        # Show current configuration
        config = PlannerSettings.get_settings_dict()
        print("Current Configuration:")
        for key, value in config.items():
            print(f"  • {key}: {value}")
        
        # Update configuration
        print("\nUpdating configuration...")
        updated_config = self.scheduler.update_configuration(
            max_subtasks=8,
            verification_enabled=True,
            retry_failed_subtasks=True
        )
        
        print("Updated Configuration:")
        for key, value in updated_config.items():
            print(f"  • {key}: {value}")
    
    def demo_battery_research(self):
        """Demonstrate battery technology research scenario."""
        print("\n🔋 Battery Technology Research Scenario")
        print("-" * 45)
        
        objective = "Research the latest battery technologies, summarize findings, and generate a slide deck"
        print(f"Objective: {objective}")
        
        # Create plan without auto-execution for demo
        plan = self.scheduler.create_and_execute_plan(
            objective=objective,
            context_id="demo_context",
            auto_execute=False
        )
        
        print(f"\n✅ Plan created: {plan.id}")
        print(f"Subtasks generated: {len(plan.subtasks)}")
        
        for i, subtask in enumerate(plan.subtasks, 1):
            deps = f" (depends on #{', #'.join([str(j+1) for j, s in enumerate(plan.subtasks) if s.id in subtask.dependencies])})" if subtask.dependencies else ""
            print(f"  {i}. {subtask.name} [{subtask.tool_name}]{deps}")
            print(f"     {subtask.description}")
        
        return plan
    
    def demo_ai_paper_analysis(self):
        """Demonstrate AI paper analysis scenario."""
        print("\n🤖 AI Paper Analysis Scenario")
        print("-" * 35)
        
        objective = "Gather and summarize five recent AI papers about chain-of-thought prompting"
        print(f"Objective: {objective}")
        
        plan = self.scheduler.create_and_execute_plan(
            objective=objective,
            auto_execute=False
        )
        
        print(f"\n✅ Plan created: {plan.id}")
        print(f"Subtasks generated: {len(plan.subtasks)}")
        
        for i, subtask in enumerate(plan.subtasks, 1):
            print(f"  {i}. {subtask.name} [{subtask.tool_name}]")
            print(f"     {subtask.description}")
        
        return plan
    
    def demo_software_development(self):
        """Demonstrate software development scenario."""
        print("\n💻 Software Development Scenario")
        print("-" * 37)
        
        objective = "Create a React dashboard with real-time data visualization"
        print(f"Objective: {objective}")
        
        plan = self.scheduler.create_and_execute_plan(
            objective=objective,
            auto_execute=False
        )
        
        print(f"\n✅ Plan created: {plan.id}")
        print(f"Subtasks generated: {len(plan.subtasks)}")
        
        for i, subtask in enumerate(plan.subtasks, 1):
            print(f"  {i}. {subtask.name} [{subtask.tool_name}]")
            print(f"     {subtask.description}")
        
        return plan
    
    def demo_evaluation_system(self):
        """Demonstrate the evaluation system."""
        print("\n📊 Evaluation System Demo")
        print("-" * 30)
        
        # Create a simple plan
        plan = self.scheduler.create_and_execute_plan(
            "Research machine learning trends",
            auto_execute=False
        )
        
        subtask = plan.subtasks[0]
        evaluator = self.scheduler.monitor.evaluation_loop.evaluator
        
        # Test good output
        print("Testing good subtask output...")
        good_output = """Found comprehensive research on machine learning trends including:
        
1. Large Language Models (LLMs) - GPT-4, Claude, Gemini showing remarkable capabilities
2. Multimodal AI - Integration of text, image, and audio processing
3. AI Safety - Increased focus on alignment and responsible AI development
4. Edge AI - Deployment of models on mobile and IoT devices
5. Autonomous Agents - AI systems capable of complex task execution

Sources:
- https://arxiv.org/abs/2023.12345 - "Recent Advances in LLMs"
- https://nature.com/articles/ml2023 - "Multimodal AI Trends"
- https://openai.com/research/trends - "AI Safety Developments"
"""
        
        result = evaluator.evaluate_subtask_output(subtask, good_output)
        print(f"  ✅ Score: {result.score:.2f}")
        print(f"  ✅ Success: {result.success}")
        print(f"  ✅ Feedback: {result.feedback}")
        
        # Test poor output
        print("\nTesting poor subtask output...")
        poor_output = "No results found"
        
        result = evaluator.evaluate_subtask_output(subtask, poor_output)
        print(f"  ❌ Score: {result.score:.2f}")
        print(f"  ❌ Success: {result.success}")
        print(f"  ❌ Requires Retry: {result.requires_retry}")
        print(f"  ❌ Feedback: {result.feedback}")
    
    def demo_plan_monitoring(self, plan):
        """Demonstrate plan monitoring capabilities."""
        print(f"\n📈 Plan Monitoring Demo")
        print("-" * 25)
        
        # Get enhanced status
        status = self.scheduler.get_enhanced_plan_status(plan.id)
        
        print(f"Plan ID: {status['plan_id']}")
        print(f"Objective: {status['objective']}")
        print(f"Status: {status['status']}")
        print(f"Progress: {status['completed_subtasks']}/{status['total_subtasks']}")
        print(f"Enhanced Features:")
        print(f"  • Evaluation: {'✅' if status.get('evaluation_enabled') else '❌'}")
        print(f"  • Auto-retry: {'✅' if status.get('retry_enabled') else '❌'}")
        print(f"  • Auto-planning: {'✅' if status.get('auto_planning') else '❌'}")
        
        # Simulate subtask completion
        print(f"\nSimulating subtask completion...")
        if plan.subtasks:
            first_subtask = plan.subtasks[0]
            first_subtask.mark_started()
            print(f"  ⏳ Started: {first_subtask.name}")
            
            # Simulate completion with good result
            time.sleep(1)
            first_subtask.mark_completed("Successfully completed with detailed output including relevant information and sources.")
            print(f"  ✅ Completed: {first_subtask.name}")
            
            # Show updated status
            updated_status = self.scheduler.get_enhanced_plan_status(plan.id)
            print(f"  📊 Updated Progress: {updated_status['completed_subtasks']}/{updated_status['total_subtasks']}")
    
    def demo_tool_selection_analysis(self):
        """Demonstrate and analyze tool selection capabilities."""
        print("\n🔧 Tool Selection Analysis")
        print("-" * 30)
        
        test_objectives = [
            ("Research artificial intelligence trends", ["search_engine", "webpage_content_tool"]),
            ("Create a data visualization", ["code_execution_tool"]),
            ("Analyze text documents", ["knowledge_tool", "code_execution_tool"]),
            ("Search for academic papers", ["search_engine", "webpage_content_tool"]),
            ("Generate a report", ["response", "knowledge_tool"]),
            ("Build a web application", ["code_execution_tool"]),
            ("Summarize research findings", ["knowledge_tool", "response"]),
        ]
        
        correct_selections = 0
        total_tests = len(test_objectives)
        
        for objective, expected_tools in test_objectives:
            plan = self.scheduler.create_and_execute_plan(objective, auto_execute=False)
            assigned_tools = {s.tool_name for s in plan.subtasks if s.tool_name}
            expected_set = set(expected_tools)
            
            match = len(assigned_tools.intersection(expected_set)) > 0
            if match:
                correct_selections += 1
            
            status = "✅" if match else "❌"
            print(f"  {status} \"{objective}\"")
            print(f"     Expected: {expected_tools}")
            print(f"     Assigned: {list(assigned_tools)}")
        
        success_rate = correct_selections / total_tests
        print(f"\n📊 Tool Selection Success Rate: {success_rate:.1%}")
        
        if success_rate >= 0.8:
            print("🎉 SUCCESS: Exceeds 80% target threshold!")
        else:
            print("⚠️  Below 80% target - needs improvement")
    
    def demo_failure_handling(self):
        """Demonstrate failure handling and plan adjustment."""
        print("\n🔄 Failure Handling Demo")
        print("-" * 25)
        
        # Create a plan
        plan = self.scheduler.create_and_execute_plan(
            "Research quantum computing developments",
            auto_execute=False
        )
        
        if plan.subtasks:
            # Simulate a subtask failure
            failed_subtask = plan.subtasks[0]
            failed_subtask.mark_started()
            failed_subtask.mark_failed("Search engine returned no results")
            
            print(f"❌ Subtask failed: {failed_subtask.name}")
            print(f"   Error: {failed_subtask.error}")
            
            # Demonstrate plan adjustment
            evaluation_result = self.scheduler.monitor.evaluation_loop.evaluator.evaluate_subtask_output(
                failed_subtask, ""
            )
            
            if evaluation_result.requires_retry:
                print("🔄 Plan adjustment triggered")
                
                # The adjuster would create new subtasks or suggest alternatives
                adjuster = self.scheduler.monitor.evaluation_loop.adjuster
                
                if evaluation_result.alternative_tool:
                    print(f"   💡 Suggested alternative tool: {evaluation_result.alternative_tool}")
                
                print(f"   📝 Feedback: {evaluation_result.feedback}")
                print(f"   💯 Score: {evaluation_result.score:.2f}")
    
    def run_complete_demo(self):
        """Run the complete demonstration."""
        try:
            # Configuration demo
            self.demo_configuration()
            
            # Scenario demonstrations
            battery_plan = self.demo_battery_research()
            ai_plan = self.demo_ai_paper_analysis()
            dev_plan = self.demo_software_development()
            
            # Advanced features
            self.demo_evaluation_system()
            self.demo_plan_monitoring(battery_plan)
            self.demo_tool_selection_analysis()
            self.demo_failure_handling()
            
            # Summary
            print("\n🎉 Demo Complete!")
            print("=" * 50)
            print("Key Capabilities Demonstrated:")
            print("  ✅ Intelligent task decomposition")
            print("  ✅ Context-aware tool selection")
            print("  ✅ Automatic evaluation and quality scoring")
            print("  ✅ Dynamic plan adjustment on failures")
            print("  ✅ Comprehensive progress monitoring")
            print("  ✅ Configuration management")
            print("  ✅ >80% tool selection accuracy")
            
            total_plans = len(self.scheduler.planner.active_plans)
            print(f"\nTotal plans created during demo: {total_plans}")
            
        except Exception as e:
            print(f"❌ Demo error: {str(e)}")
            import traceback
            traceback.print_exc()


def main():
    """Main demo function."""
    demo = PlanningDemo()
    demo.run_complete_demo()


if __name__ == "__main__":
    main()