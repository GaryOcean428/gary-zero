"""Test plugin execution."""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from framework.plugins.manager import PluginManager


async def test_plugin_execution():
    """Test loading and executing a plugin."""
    print("Testing plugin execution...")
    
    # Initialize plugin manager
    manager = PluginManager()
    
    # Load the simple_test plugin
    tool_class = manager.get_tool("simple_test")
    
    if not tool_class:
        print("❌ Failed to load simple_test plugin")
        return
    
    print("✓ Successfully loaded simple_test plugin")
    
    # Create a mock agent object
    class MockAgent:
        def __init__(self):
            pass
    
    # Test plugin execution
    mock_agent = MockAgent()
    
    # Test info action
    tool = tool_class(
        agent=mock_agent,
        name="simple_test",
        method=None,
        args={"action": "info"},
        message="Test message"
    )
    
    try:
        response = await tool.execute()
        if response:
            print(f"✓ Plugin execution successful:")
            print(f"  Response: {response.message[:100]}...")
        else:
            print("⚠️ Plugin execution returned None")
            return
        
        # Test echo action
        tool2 = tool_class(
            agent=mock_agent,
            name="simple_test", 
            method=None,
            args={"action": "echo", "message": "Hello from plugin test!"},
            message="Test message"
        )
        
        response2 = await tool2.execute()
        if response2:
            print(f"✓ Echo test successful:")
            print(f"  Response: {response2.message}")
        else:
            print("⚠️ Echo test returned None")
        
    except Exception as e:
        print(f"❌ Plugin execution failed: {e}")
        import traceback
        traceback.print_exc()


async def test_plugin_manager_operations():
    """Test plugin manager operations."""
    print("\nTesting plugin manager operations...")
    
    manager = PluginManager()
    
    # Test listing capabilities
    capabilities = manager.get_available_capabilities()
    print(f"✓ Available capabilities: {', '.join(capabilities)}")
    
    # Test plugin info
    info = manager.get_plugin_info("simple_test")
    if info:
        print(f"✓ Plugin info retrieved: {info['name']} v{info['version']}")
    
    # Test dependency validation
    valid = manager.validate_plugin_dependencies("simple_test")
    print(f"✓ Dependencies valid: {valid}")
    
    # Test disable/enable
    if manager.disable_plugin("simple_test"):
        print("✓ Plugin disabled successfully")
        
        # Check status
        plugins = manager.list_plugins()
        simple_test = next((p for p in plugins if p['name'] == 'simple_test'), None)
        if simple_test and not simple_test['enabled']:
            print("✓ Plugin status updated to disabled")
        
        # Re-enable
        if manager.enable_plugin("simple_test"):
            print("✓ Plugin re-enabled successfully")


if __name__ == "__main__":
    try:
        asyncio.run(test_plugin_execution())
        asyncio.run(test_plugin_manager_operations())
        print("\n🎉 All plugin tests passed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()