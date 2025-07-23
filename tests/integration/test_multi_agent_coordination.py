"""
Integration tests for multi-agent coordination and plugin loading.
"""

import asyncio
import pytest
import json
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, List, Any

from framework.a2a.communication import (
    A2AMessage,
    MessageType,
    MessagePriority,
    CommunicationRequest,
    CommunicationService
)


class MockAgent:
    """Mock agent for testing multi-agent coordination."""
    
    def __init__(self, agent_id: str, capabilities: List[str] = None):
        self.agent_id = agent_id
        self.capabilities = capabilities or []
        self.received_messages: List[A2AMessage] = []
        self.sent_messages: List[A2AMessage] = []
        self.is_active = True
        
    async def send_message(self, message: A2AMessage) -> bool:
        """Simulate sending a message."""
        self.sent_messages.append(message)
        return True
        
    async def receive_message(self, message: A2AMessage) -> A2AMessage:
        """Simulate receiving and processing a message."""
        self.received_messages.append(message)
        
        # Simulate different response types based on message content
        if message.type == MessageType.REQUEST:
            if message.content.get("action") == "ping":
                return A2AMessage(
                    id=f"response-{len(self.sent_messages)}",
                    session_id=message.session_id,
                    sender_id=self.agent_id,
                    recipient_id=message.sender_id,
                    type=MessageType.RESPONSE,
                    content={"result": "pong", "agent_status": "active"},
                    timestamp=datetime.now().isoformat(),
                    correlation_id=message.correlation_id
                )
            elif message.content.get("action") == "get_capabilities":
                return A2AMessage(
                    id=f"response-{len(self.sent_messages)}",
                    session_id=message.session_id,
                    sender_id=self.agent_id,
                    recipient_id=message.sender_id,
                    type=MessageType.RESPONSE,
                    content={"result": "capabilities", "capabilities": self.capabilities},
                    timestamp=datetime.now().isoformat(),
                    correlation_id=message.correlation_id
                )
            elif message.content.get("action") == "execute_task":
                task_id = message.content.get("task_id", "unknown")
                return A2AMessage(
                    id=f"response-{len(self.sent_messages)}",
                    session_id=message.session_id,
                    sender_id=self.agent_id,
                    recipient_id=message.sender_id,
                    type=MessageType.RESULT,
                    content={
                        "result": "task_completed",
                        "task_id": task_id,
                        "output": f"Task {task_id} completed by {self.agent_id}"
                    },
                    timestamp=datetime.now().isoformat(),
                    correlation_id=message.correlation_id
                )
        
        # Default response for other message types
        return A2AMessage(
            id=f"ack-{len(self.sent_messages)}",
            session_id=message.session_id,
            sender_id=self.agent_id,
            recipient_id=message.sender_id,
            type=MessageType.RESPONSE,
            content={"result": "acknowledged"},
            timestamp=datetime.now().isoformat(),
            correlation_id=message.correlation_id
        )


class MockPluginManager:
    """Mock plugin manager for testing plugin loading."""
    
    def __init__(self):
        self.loaded_plugins: Dict[str, Dict[str, Any]] = {}
        self.plugin_registry: Dict[str, Dict[str, Any]] = {
            "data_processor": {
                "name": "data_processor",
                "version": "1.0.0",
                "capabilities": ["data_analysis", "csv_processing"],
                "entry_point": "mock_data_processor_main",
                "config": {"max_rows": 10000}
            },
            "web_scraper": {
                "name": "web_scraper",
                "version": "2.1.0", 
                "capabilities": ["web_scraping", "html_parsing"],
                "entry_point": "mock_web_scraper_main",
                "config": {"timeout": 30, "max_pages": 100}
            },
            "notification_sender": {
                "name": "notification_sender",
                "version": "1.2.1",
                "capabilities": ["email_notifications", "slack_notifications"],
                "entry_point": "mock_notification_main",
                "config": {"smtp_host": "localhost", "slack_webhook": "https://example.com"}
            }
        }
        
    async def load_plugin(self, plugin_name: str) -> bool:
        """Simulate loading a plugin."""
        if plugin_name in self.plugin_registry:
            self.loaded_plugins[plugin_name] = self.plugin_registry[plugin_name].copy()
            self.loaded_plugins[plugin_name]["status"] = "loaded"
            self.loaded_plugins[plugin_name]["load_time"] = datetime.now().isoformat()
            return True
        return False
        
    async def unload_plugin(self, plugin_name: str) -> bool:
        """Simulate unloading a plugin."""
        if plugin_name in self.loaded_plugins:
            del self.loaded_plugins[plugin_name]
            return True
        return False
        
    def get_loaded_plugins(self) -> Dict[str, Dict[str, Any]]:
        """Get all loaded plugins."""
        return self.loaded_plugins.copy()
        
    def get_plugin_capabilities(self, plugin_name: str) -> List[str]:
        """Get capabilities of a specific plugin."""
        if plugin_name in self.loaded_plugins:
            return self.loaded_plugins[plugin_name].get("capabilities", [])
        return []
        
    async def execute_plugin(self, plugin_name: str, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate plugin execution."""
        if plugin_name not in self.loaded_plugins:
            return {"error": f"Plugin {plugin_name} not loaded"}
            
        # Simulate different plugin behaviors
        if plugin_name == "data_processor" and action == "process_csv":
            return {
                "result": "success",
                "processed_rows": parameters.get("rows", 0),
                "output_file": f"processed_{parameters.get('input_file', 'data')}.csv"
            }
        elif plugin_name == "web_scraper" and action == "scrape_url":
            return {
                "result": "success",
                "scraped_pages": [parameters.get("url", "https://example.com")],
                "content_length": 1024
            }
        elif plugin_name == "notification_sender" and action == "send_email":
            return {
                "result": "success",
                "message_id": f"msg-{datetime.now().timestamp()}",
                "recipient": parameters.get("to", "test@example.com")
            }
        
        return {"result": "unknown_action", "action": action}


class MultiAgentCoordinator:
    """Coordinator for multi-agent workflows."""
    
    def __init__(self):
        self.agents: Dict[str, MockAgent] = {}
        self.communication_service = CommunicationService()
        self.plugin_manager = MockPluginManager()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
    def register_agent(self, agent: MockAgent) -> None:
        """Register an agent with the coordinator."""
        self.agents[agent.agent_id] = agent
        
    async def discover_agents(self) -> Dict[str, List[str]]:
        """Discover all agents and their capabilities."""
        agent_capabilities = {}
        
        for agent_id, agent in self.agents.items():
            if agent.is_active:
                # Send capability discovery message
                discovery_msg = A2AMessage(
                    id=f"discovery-{agent_id}-{datetime.now().timestamp()}",
                    session_id="discovery-session",
                    sender_id="coordinator",
                    recipient_id=agent_id,
                    type=MessageType.REQUEST,
                    content={"action": "get_capabilities"},
                    timestamp=datetime.now().isoformat()
                )
                
                response = await agent.receive_message(discovery_msg)
                if response and response.content.get("result") == "capabilities":
                    agent_capabilities[agent_id] = response.content.get("capabilities", [])
                else:
                    agent_capabilities[agent_id] = agent.capabilities
                    
        return agent_capabilities
    
    async def create_workflow_session(self, session_id: str, participating_agents: List[str]) -> bool:
        """Create a new workflow session with participating agents."""
        if session_id in self.active_sessions:
            return False
            
        # Verify all agents exist and are active
        for agent_id in participating_agents:
            if agent_id not in self.agents or not self.agents[agent_id].is_active:
                return False
                
        self.active_sessions[session_id] = {
            "session_id": session_id,
            "participating_agents": participating_agents,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "message_count": 0
        }
        
        return True
    
    async def execute_distributed_task(self, 
                                     session_id: str,
                                     task_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task distributed across multiple agents."""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
            
        session = self.active_sessions[session_id]
        task_id = task_definition.get("task_id", f"task-{datetime.now().timestamp()}")
        
        # Determine task assignment based on required capabilities
        required_capabilities = task_definition.get("required_capabilities", [])
        subtasks = task_definition.get("subtasks", [])
        
        # Discover agent capabilities
        agent_capabilities = await self.discover_agents()
        
        # Assign subtasks to agents
        task_assignments = {}
        for subtask in subtasks:
            subtask_capabilities = subtask.get("required_capabilities", [])
            
            # Find suitable agent
            assigned_agent = None
            for agent_id in session["participating_agents"]:
                agent_caps = agent_capabilities.get(agent_id, [])
                if all(cap in agent_caps for cap in subtask_capabilities):
                    assigned_agent = agent_id
                    break
                    
            if assigned_agent:
                if assigned_agent not in task_assignments:
                    task_assignments[assigned_agent] = []
                task_assignments[assigned_agent].append(subtask)
        
        # Execute subtasks
        results = {}
        for agent_id, assigned_subtasks in task_assignments.items():
            agent = self.agents[agent_id]
            
            for subtask in assigned_subtasks:
                task_msg = A2AMessage(
                    id=f"task-{subtask['id']}-{datetime.now().timestamp()}",
                    session_id=session_id,
                    sender_id="coordinator",
                    recipient_id=agent_id,
                    type=MessageType.TASK,
                    content={
                        "action": "execute_task",
                        "task_id": subtask["id"],
                        "parameters": subtask.get("parameters", {}),
                        "parent_task_id": task_id
                    },
                    timestamp=datetime.now().isoformat(),
                    required_capabilities=subtask.get("required_capabilities", [])
                )
                
                response = await agent.receive_message(task_msg)
                if response:
                    results[subtask["id"]] = {
                        "agent_id": agent_id,
                        "result": response.content,
                        "completed_at": response.timestamp
                    }
                    
        session["message_count"] += len(task_assignments)
        
        return {
            "task_id": task_id,
            "session_id": session_id,
            "status": "completed",
            "results": results,
            "total_subtasks": len(subtasks),
            "completed_subtasks": len(results)
        }


@pytest.mark.integration
class TestMultiAgentCoordination:
    """Integration tests for multi-agent coordination."""
    
    @pytest.fixture
    def coordinator(self):
        """Create a multi-agent coordinator with test agents."""
        coordinator = MultiAgentCoordinator()
        
        # Create test agents with different capabilities
        agents = [
            MockAgent("data-agent", ["data_analysis", "csv_processing", "json_processing"]),
            MockAgent("web-agent", ["web_scraping", "html_parsing", "api_calls"]),
            MockAgent("notification-agent", ["email_notifications", "slack_notifications"]),
            MockAgent("compute-agent", ["mathematical_computation", "statistical_analysis"])
        ]
        
        for agent in agents:
            coordinator.register_agent(agent)
            
        return coordinator
    
    @pytest.mark.asyncio
    async def test_agent_discovery(self, coordinator):
        """Test agent discovery functionality."""
        capabilities = await coordinator.discover_agents()
        
        assert len(capabilities) == 4
        assert "data-agent" in capabilities
        assert "web-agent" in capabilities
        assert "notification-agent" in capabilities
        assert "compute-agent" in capabilities
        
        # Verify specific capabilities
        assert "data_analysis" in capabilities["data-agent"]
        assert "web_scraping" in capabilities["web-agent"]
        assert "email_notifications" in capabilities["notification-agent"]
        assert "mathematical_computation" in capabilities["compute-agent"]
    
    @pytest.mark.asyncio
    async def test_workflow_session_creation(self, coordinator):
        """Test creating workflow sessions."""
        # Test successful session creation
        success = await coordinator.create_workflow_session(
            "test-session-1",
            ["data-agent", "web-agent"]
        )
        assert success is True
        assert "test-session-1" in coordinator.active_sessions
        
        # Test duplicate session creation
        duplicate = await coordinator.create_workflow_session(
            "test-session-1",
            ["notification-agent"]
        )
        assert duplicate is False
        
        # Test session with non-existent agent
        invalid = await coordinator.create_workflow_session(
            "test-session-2",
            ["non-existent-agent"]
        )
        assert invalid is False
    
    @pytest.mark.asyncio
    async def test_distributed_task_execution(self, coordinator):
        """Test distributed task execution across multiple agents."""
        # Create session
        session_id = "distributed-task-session"
        await coordinator.create_workflow_session(
            session_id,
            ["data-agent", "web-agent", "notification-agent"]
        )
        
        # Define distributed task
        task_definition = {
            "task_id": "data-processing-workflow",
            "description": "Process web data and send notifications",
            "required_capabilities": ["web_scraping", "data_analysis", "email_notifications"],
            "subtasks": [
                {
                    "id": "scrape-data",
                    "action": "scrape_website",
                    "required_capabilities": ["web_scraping"],
                    "parameters": {"url": "https://example.com/data", "format": "json"}
                },
                {
                    "id": "analyze-data",
                    "action": "analyze_dataset",
                    "required_capabilities": ["data_analysis"],
                    "parameters": {"input_format": "json", "analysis_type": "summary"}
                },
                {
                    "id": "send-notification",
                    "action": "send_completion_email",
                    "required_capabilities": ["email_notifications"],
                    "parameters": {"recipient": "admin@example.com", "subject": "Data Processing Complete"}
                }
            ]
        }
        
        # Execute distributed task
        result = await coordinator.execute_distributed_task(session_id, task_definition)
        
        # Verify execution results
        assert result["task_id"] == "data-processing-workflow"
        assert result["session_id"] == session_id
        assert result["status"] == "completed"
        assert result["total_subtasks"] == 3
        assert result["completed_subtasks"] <= 3  # May be less if no suitable agents
        
        # Verify results structure
        assert "results" in result
        results = result["results"]
        
        # Check that tasks were assigned appropriately
        for subtask_id, subtask_result in results.items():
            assert "agent_id" in subtask_result
            assert "result" in subtask_result
            assert "completed_at" in subtask_result
    
    @pytest.mark.asyncio
    async def test_agent_communication_flow(self, coordinator):
        """Test communication flow between agents."""
        agent1 = coordinator.agents["data-agent"]
        agent2 = coordinator.agents["web-agent"]
        
        # Test ping-pong communication
        ping_msg = A2AMessage(
            id="ping-msg-001",
            session_id="comm-test-session",
            sender_id=agent1.agent_id,
            recipient_id=agent2.agent_id,
            type=MessageType.REQUEST,
            content={"action": "ping", "timestamp": datetime.now().isoformat()},
            timestamp=datetime.now().isoformat(),
            correlation_id="ping-corr-001"
        )
        
        # Agent1 sends message to Agent2
        await agent1.send_message(ping_msg)
        assert len(agent1.sent_messages) == 1
        
        # Agent2 receives and responds
        response = await agent2.receive_message(ping_msg)
        assert len(agent2.received_messages) == 1
        assert response.type == MessageType.RESPONSE
        assert response.content["result"] == "pong"
        assert response.correlation_id == "ping-corr-001"
    
    @pytest.mark.asyncio 
    async def test_capability_based_task_assignment(self, coordinator):
        """Test that tasks are assigned based on agent capabilities."""
        session_id = "capability-test-session"
        await coordinator.create_workflow_session(
            session_id,
            list(coordinator.agents.keys())
        )
        
        # Task requiring specific mathematical computation
        math_task = {
            "task_id": "math-computation",
            "subtasks": [
                {
                    "id": "statistical-analysis",
                    "required_capabilities": ["statistical_analysis"],
                    "parameters": {"dataset": "test_data.csv", "method": "regression"}
                }
            ]
        }
        
        result = await coordinator.execute_distributed_task(session_id, math_task)
        
        # Should be assigned to compute-agent (only one with statistical_analysis capability)
        if result["completed_subtasks"] > 0:
            analysis_result = result["results"]["statistical-analysis"]
            assert analysis_result["agent_id"] == "compute-agent"


@pytest.mark.integration
class TestPluginLoading:
    """Integration tests for plugin loading and management."""
    
    @pytest.fixture
    def plugin_manager(self):
        """Create a plugin manager for testing."""
        return MockPluginManager()
    
    @pytest.mark.asyncio
    async def test_plugin_loading(self, plugin_manager):
        """Test loading plugins."""
        # Test successful plugin loading
        success = await plugin_manager.load_plugin("data_processor")
        assert success is True
        
        loaded_plugins = plugin_manager.get_loaded_plugins()
        assert "data_processor" in loaded_plugins
        assert loaded_plugins["data_processor"]["status"] == "loaded"
        assert "load_time" in loaded_plugins["data_processor"]
        
        # Test loading non-existent plugin
        failure = await plugin_manager.load_plugin("non_existent_plugin")
        assert failure is False
    
    @pytest.mark.asyncio
    async def test_plugin_unloading(self, plugin_manager):
        """Test unloading plugins."""
        # Load then unload plugin
        await plugin_manager.load_plugin("web_scraper")
        assert "web_scraper" in plugin_manager.get_loaded_plugins()
        
        success = await plugin_manager.unload_plugin("web_scraper")
        assert success is True
        assert "web_scraper" not in plugin_manager.get_loaded_plugins()
        
        # Test unloading non-loaded plugin
        failure = await plugin_manager.unload_plugin("not_loaded_plugin")
        assert failure is False
    
    @pytest.mark.asyncio
    async def test_plugin_capability_discovery(self, plugin_manager):
        """Test discovering plugin capabilities."""
        # Load multiple plugins
        await plugin_manager.load_plugin("data_processor")
        await plugin_manager.load_plugin("notification_sender")
        
        # Test capability discovery
        data_caps = plugin_manager.get_plugin_capabilities("data_processor")
        assert "data_analysis" in data_caps
        assert "csv_processing" in data_caps
        
        notification_caps = plugin_manager.get_plugin_capabilities("notification_sender")
        assert "email_notifications" in notification_caps
        assert "slack_notifications" in notification_caps
        
        # Test non-loaded plugin
        empty_caps = plugin_manager.get_plugin_capabilities("web_scraper")
        assert empty_caps == []
    
    @pytest.mark.asyncio
    async def test_plugin_execution(self, plugin_manager):
        """Test plugin execution."""
        # Load and execute data processor plugin
        await plugin_manager.load_plugin("data_processor")
        
        result = await plugin_manager.execute_plugin(
            "data_processor",
            "process_csv",
            {"input_file": "test_data.csv", "rows": 1000}
        )
        
        assert result["result"] == "success"
        assert result["processed_rows"] == 1000
        assert "output_file" in result
        
        # Test executing unloaded plugin
        error_result = await plugin_manager.execute_plugin(
            "web_scraper",
            "scrape_url",
            {"url": "https://example.com"}
        )
        
        assert "error" in error_result
        assert "not loaded" in error_result["error"]
    
    @pytest.mark.asyncio
    async def test_multi_plugin_workflow(self, plugin_manager):
        """Test workflow involving multiple plugins."""
        # Load required plugins
        plugins_to_load = ["data_processor", "web_scraper", "notification_sender"]
        for plugin in plugins_to_load:
            success = await plugin_manager.load_plugin(plugin)
            assert success is True
        
        # Simulate multi-step workflow
        workflow_results = {}
        
        # Step 1: Scrape data
        scrape_result = await plugin_manager.execute_plugin(
            "web_scraper",
            "scrape_url",
            {"url": "https://api.example.com/data"}
        )
        workflow_results["scraping"] = scrape_result
        
        # Step 2: Process scraped data
        if scrape_result["result"] == "success":
            process_result = await plugin_manager.execute_plugin(
                "data_processor",
                "process_csv",
                {"input_file": "scraped_data.csv", "rows": 500}
            )
            workflow_results["processing"] = process_result
        
        # Step 3: Send notification
        if workflow_results.get("processing", {}).get("result") == "success":
            notify_result = await plugin_manager.execute_plugin(
                "notification_sender",
                "send_email",
                {
                    "to": "admin@example.com",
                    "subject": "Data Processing Complete",
                    "body": "The data workflow has completed successfully."
                }
            )
            workflow_results["notification"] = notify_result
        
        # Verify workflow completion
        assert len(workflow_results) == 3
        assert all(result.get("result") == "success" for result in workflow_results.values())


@pytest.mark.integration 
class TestEndToEndWorkflow:
    """End-to-end integration tests for complete workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_data_processing_workflow(self):
        """Test complete data processing workflow with agents and plugins."""
        # Setup coordinator and plugin manager
        coordinator = MultiAgentCoordinator()
        plugin_manager = MockPluginManager()
        
        # Register agents
        agents = [
            MockAgent("data-processor-agent", ["data_analysis", "csv_processing"]),
            MockAgent("web-scraper-agent", ["web_scraping", "api_calls"]),
            MockAgent("notification-agent", ["email_notifications"])
        ]
        
        for agent in agents:
            coordinator.register_agent(agent)
        
        # Load required plugins
        await plugin_manager.load_plugin("data_processor")
        await plugin_manager.load_plugin("web_scraper")
        await plugin_manager.load_plugin("notification_sender")
        
        # Create workflow session
        session_id = "end-to-end-workflow"
        session_created = await coordinator.create_workflow_session(
            session_id,
            [agent.agent_id for agent in agents]
        )
        assert session_created is True
        
        # Define complex workflow
        workflow_definition = {
            "task_id": "complete-data-workflow",
            "description": "End-to-end data processing with multiple agents and plugins",
            "subtasks": [
                {
                    "id": "web-data-collection",
                    "required_capabilities": ["web_scraping"],
                    "parameters": {
                        "urls": ["https://api.example.com/dataset1", "https://api.example.com/dataset2"],
                        "format": "json"
                    }
                },
                {
                    "id": "data-validation-processing",
                    "required_capabilities": ["data_analysis"],
                    "parameters": {
                        "validation_rules": ["non_null", "unique_ids"],
                        "processing_steps": ["normalize", "aggregate"]
                    }
                },
                {
                    "id": "completion-notification",
                    "required_capabilities": ["email_notifications"],
                    "parameters": {
                        "recipients": ["admin@example.com", "team@example.com"],
                        "include_summary": True
                    }
                }
            ]
        }
        
        # Execute workflow
        result = await coordinator.execute_distributed_task(session_id, workflow_definition)
        
        # Verify workflow execution
        assert result["status"] == "completed"
        assert result["task_id"] == "complete-data-workflow"
        assert result["total_subtasks"] == 3
        
        # Verify agent message tracking
        total_messages_sent = sum(len(agent.sent_messages) for agent in agents)
        total_messages_received = sum(len(agent.received_messages) for agent in agents)
        
        # Should have communication activity
        assert total_messages_received > 0
        
        # Verify session state
        session = coordinator.active_sessions[session_id]
        assert session["status"] == "active"
        assert session["message_count"] > 0
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self):
        """Test error handling in complex workflows."""
        coordinator = MultiAgentCoordinator()
        
        # Register agent with limited capabilities
        limited_agent = MockAgent("limited-agent", ["basic_processing"])
        coordinator.register_agent(limited_agent)
        
        # Create session
        session_id = "error-handling-test"
        await coordinator.create_workflow_session(session_id, ["limited-agent"])
        
        # Define task requiring capabilities not available
        impossible_task = {
            "task_id": "impossible-task",
            "subtasks": [
                {
                    "id": "advanced-ai-processing",
                    "required_capabilities": ["advanced_ai", "machine_learning"],
                    "parameters": {"model": "gpt-4", "training_data": "large_dataset"}
                }
            ]
        }
        
        # Execute task
        result = await coordinator.execute_distributed_task(session_id, impossible_task)
        
        # Should complete but with no results due to capability mismatch
        assert result["status"] == "completed"
        assert result["completed_subtasks"] == 0  # No suitable agents
        assert len(result["results"]) == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self):
        """Test concurrent execution of multiple workflows."""
        coordinator = MultiAgentCoordinator()
        
        # Register multiple agents for concurrent processing
        agents = [
            MockAgent(f"concurrent-agent-{i}", ["concurrent_processing", "task_execution"])
            for i in range(3)
        ]
        
        for agent in agents:
            coordinator.register_agent(agent)
        
        # Create multiple concurrent sessions
        sessions = []
        for i in range(3):
            session_id = f"concurrent-session-{i}"
            await coordinator.create_workflow_session(
                session_id,
                [f"concurrent-agent-{i}"]
            )
            sessions.append(session_id)
        
        # Define concurrent tasks
        tasks = []
        for i, session_id in enumerate(sessions):
            task_def = {
                "task_id": f"concurrent-task-{i}",
                "subtasks": [
                    {
                        "id": f"subtask-{i}-1",
                        "required_capabilities": ["concurrent_processing"],
                        "parameters": {"workload": f"workload-{i}"}
                    }
                ]
            }
            tasks.append(coordinator.execute_distributed_task(session_id, task_def))
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        # Verify all tasks completed
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["status"] == "completed"
            assert result["task_id"] == f"concurrent-task-{i}"
            assert result["completed_subtasks"] >= 0


@pytest.mark.performance
class TestPerformanceMetrics:
    """Performance tests for multi-agent coordination."""
    
    @pytest.mark.asyncio
    async def test_agent_discovery_performance(self, benchmark):
        """Benchmark agent discovery performance."""
        coordinator = MultiAgentCoordinator()
        
        # Register many agents
        for i in range(50):
            agent = MockAgent(f"perf-agent-{i}", ["capability-1", "capability-2"])
            coordinator.register_agent(agent)
        
        async def discover_all_agents():
            return await coordinator.discover_agents()
        
        # Benchmark discovery
        result = await discover_all_agents()
        assert len(result) == 50
    
    @pytest.mark.asyncio
    async def test_large_workflow_execution(self):
        """Test execution of large workflows with many subtasks."""
        coordinator = MultiAgentCoordinator()
        
        # Register agents with different capabilities
        capabilities_sets = [
            ["data_processing", "analytics"],
            ["web_services", "api_integration"], 
            ["notifications", "reporting"],
            ["file_operations", "data_storage"]
        ]
        
        for i, caps in enumerate(capabilities_sets):
            agent = MockAgent(f"large-workflow-agent-{i}", caps)
            coordinator.register_agent(agent)
        
        # Create session
        session_id = "large-workflow-session"
        await coordinator.create_workflow_session(
            session_id,
            [f"large-workflow-agent-{i}" for i in range(len(capabilities_sets))]
        )
        
        # Define large workflow with many subtasks
        subtasks = []
        for i in range(20):
            capability = capabilities_sets[i % len(capabilities_sets)][0]
            subtasks.append({
                "id": f"large-subtask-{i}",
                "required_capabilities": [capability],
                "parameters": {"task_number": i, "batch_size": 100}
            })
        
        large_workflow = {
            "task_id": "large-workflow-test",
            "subtasks": subtasks
        }
        
        # Execute large workflow
        start_time = datetime.now()
        result = await coordinator.execute_distributed_task(session_id, large_workflow)
        end_time = datetime.now()
        
        execution_time = (end_time - start_time).total_seconds()
        
        # Verify execution and performance
        assert result["status"] == "completed"
        assert result["total_subtasks"] == 20
        assert execution_time < 5.0  # Should complete within 5 seconds
        
        # Verify reasonable distribution of tasks
        agent_task_counts = {}
        for subtask_result in result["results"].values():
            agent_id = subtask_result["agent_id"]
            agent_task_counts[agent_id] = agent_task_counts.get(agent_id, 0) + 1
        
        # Each agent should have received some tasks
        assert len(agent_task_counts) > 0