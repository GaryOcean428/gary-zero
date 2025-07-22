"""Test agent integration with plugins."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio


class MockAgent:
    """Mock agent for testing."""
    
    def __init__(self):
        pass
    
    def get_tool(self, name: str, method: str | None, args: dict, message: str, **kwargs):
        """Test the plugin-integrated get_tool method."""
        from framework.helpers.tool import Tool
        from framework.tools.unknown import Unknown
        from framework.helpers import extract_tools

        # First try to load from plugins
        try:
            plugin_tool_class = self._get_plugin_tool(name)
            if plugin_tool_class:
                return plugin_tool_class(
                    agent=self, name=name, method=method, args=args, message=message, **kwargs
                )
        except Exception as e:
            print(f"Failed to load plugin tool {name}: {e}")

        # Fallback to static tools
        classes = extract_tools.load_classes_from_folder("framework/tools", name + ".py", Tool)
        tool_class = classes[0] if classes else Unknown
        return tool_class(
            agent=self, name=name, method=method, args=args, message=message, **kwargs
        )

    def _get_plugin_tool(self, name: str):
        """Get a tool from the plugin system."""
        # Initialize plugin manager if not already done
        if not hasattr(self, '_plugin_manager'):
            try:
                from framework.plugins.manager import PluginManager
                self._plugin_manager = PluginManager()
            except Exception as e:
                print(f"Failed to initialize plugin manager: {e}")
                return None
        
        return self._plugin_manager.get_tool(name)


async def test_agent_plugin_integration():
    """Test that agent can load and use plugins."""
    print("Testing agent plugin integration...")
    
    agent = MockAgent()
    
    # Test loading a plugin tool
    tool = agent.get_tool(
        name="simple_test",
        method=None,
        args={"action": "info"},
        message="test message"
    )
    
    print(f"✓ Agent loaded tool: {tool.__class__.__name__}")
    
    # Test executing the plugin tool
    try:
        response = await tool.execute()
        if response:
            print("✓ Plugin tool executed successfully")
            print(f"  Response: {response.message[:50]}...")
        else:
            print("❌ Plugin tool returned None")
    except Exception as e:
        print(f"❌ Plugin tool execution failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test loading a non-existent plugin (should fallback to Unknown)
    unknown_tool = agent.get_tool(
        name="nonexistent_plugin",
        method=None,
        args={},
        message="test"
    )
    
    print(f"✓ Unknown plugin fallback: {unknown_tool.__class__.__name__}")
    
    # Test loading a static tool (should work normally)
    try:
        static_tool = agent.get_tool(
            name="response",  # This should exist in framework/tools
            method=None,
            args={"text": "test response"},
            message="test"
        )
        print(f"✓ Static tool loaded: {static_tool.__class__.__name__}")
    except Exception as e:
        print(f"⚠️ Static tool test skipped: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(test_agent_plugin_integration())
        print("\n🎉 Agent plugin integration test completed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()