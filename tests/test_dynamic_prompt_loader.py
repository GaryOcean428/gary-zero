"""
Tests for dynamic prompt loader functionality.
"""

import os
import json
import tempfile
import unittest
import shutil
from pathlib import Path
from framework.helpers.dynamic_prompt_loader import DynamicPromptLoader


class TestDynamicPromptLoader(unittest.TestCase):
    
    def setUp(self):
        # Create temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.loader = DynamicPromptLoader()
        # Override the prompts directory for testing
        self.loader.prompts_dir = self.test_dir
        
        # Create subdirectories
        for subdir in ["system", "tools", "agents", "dynamic"]:
            os.makedirs(os.path.join(self.test_dir, subdir), exist_ok=True)
    
    def tearDown(self):
        # Clean up temporary directory
        if self.loader.observer:
            self.loader.stop_watching()
        shutil.rmtree(self.test_dir)
    
    def test_json_prompt_loading(self):
        """Test loading JSON format prompts."""
        agent_data = {
            "name": "Test Agent",
            "description": "A test agent",
            "capabilities": ["test1", "test2"]
        }
        
        # Create test JSON file
        json_file = os.path.join(self.test_dir, "agents", "test_agent.json")
        with open(json_file, 'w') as f:
            json.dump(agent_data, f)
        
        # Load the prompt
        self.loader.reload_prompt_file(json_file)
        
        # Verify it was loaded
        rel_path = "agents/test_agent.json"
        prompt = self.loader.get_prompt(rel_path)
        self.assertIsNotNone(prompt)
        self.assertEqual(prompt["name"], "Test Agent")
        
        # Verify agent registry was updated
        agent_prompt = self.loader.get_agent_prompt("test_agent")
        self.assertIsNotNone(agent_prompt)
        self.assertEqual(agent_prompt["name"], "Test Agent")
    
    def test_text_prompt_loading(self):
        """Test loading plain text prompts."""
        prompt_content = "This is a test prompt for the agent."
        
        # Create test text file
        text_file = os.path.join(self.test_dir, "system", "test_prompt.txt")
        with open(text_file, 'w') as f:
            f.write(prompt_content)
        
        # Load the prompt
        self.loader.reload_prompt_file(text_file)
        
        # Verify it was loaded
        rel_path = "system/test_prompt.txt"
        prompt = self.loader.get_prompt(rel_path)
        self.assertIsNotNone(prompt)
        self.assertEqual(prompt["content"], prompt_content)
    
    def test_agent_registry(self):
        """Test agent registry functionality."""
        # Create multiple agent files
        agents = [
            {"name": "Agent 1", "id": "agent1"},
            {"name": "Agent 2", "id": "agent2"}
        ]
        
        for i, agent in enumerate(agents):
            json_file = os.path.join(self.test_dir, "agents", f"agent{i+1}.json")
            with open(json_file, 'w') as f:
                json.dump(agent, f)
            self.loader.reload_prompt_file(json_file)
        
        # Test listing agents
        agent_list = self.loader.list_agents()
        self.assertEqual(len(agent_list), 2)
        
        # Verify agent IDs
        agent_ids = [agent["id"] for agent in agent_list]
        self.assertIn("agent1", agent_ids)
        self.assertIn("agent2", agent_ids)
    
    def test_prompt_removal(self):
        """Test prompt file removal."""
        # Create and load a test prompt
        json_file = os.path.join(self.test_dir, "agents", "temp_agent.json")
        with open(json_file, 'w') as f:
            json.dump({"name": "Temp Agent"}, f)
        
        self.loader.reload_prompt_file(json_file)
        
        # Verify it was loaded
        rel_path = "agents/temp_agent.json"
        self.assertIsNotNone(self.loader.get_prompt(rel_path))
        self.assertIsNotNone(self.loader.get_agent_prompt("temp_agent"))
        
        # Remove the prompt
        self.loader.remove_prompt_file(json_file)
        
        # Verify it was removed
        self.assertIsNone(self.loader.get_prompt(rel_path))
        self.assertIsNone(self.loader.get_agent_prompt("temp_agent"))
    
    def test_stats_collection(self):
        """Test statistics collection."""
        # Initially empty
        stats = self.loader.get_stats()
        self.assertEqual(stats["total_prompts"], 0)
        self.assertEqual(stats["total_agents"], 0)
        
        # Add some prompts
        for i in range(3):
            json_file = os.path.join(self.test_dir, "agents", f"agent{i}.json")
            with open(json_file, 'w') as f:
                json.dump({"name": f"Agent {i}"}, f)
            self.loader.reload_prompt_file(json_file)
        
        # Check updated stats
        stats = self.loader.get_stats()
        self.assertEqual(stats["total_prompts"], 3)
        self.assertEqual(stats["total_agents"], 3)
        self.assertEqual(len(stats["agent_list"]), 3)


if __name__ == '__main__':
    unittest.main()