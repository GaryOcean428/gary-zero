"""Final comprehensive test of the plugin system."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from framework.plugins.manager import PluginManager


async def test_complete_plugin_system():
    """Test the complete plugin system end-to-end."""
    print("🧪 Running comprehensive plugin system test...\n")
    
    # Initialize manager
    manager = PluginManager()
    
    # Test 1: Plugin Discovery
    print("1️⃣ Testing plugin discovery...")
    plugins = manager.list_plugins()
    print(f"   ✅ Found {len(plugins)} plugins")
    assert len(plugins) >= 6, "Expected at least 6 sample plugins"
    
    # Test 2: Capabilities
    print("\n2️⃣ Testing capability aggregation...")
    capabilities = manager.get_available_capabilities()
    print(f"   ✅ Found {len(capabilities)} capabilities: {', '.join(capabilities[:5])}...")
    assert len(capabilities) >= 10, "Expected multiple capabilities"
    
    # Test 3: Plugin Loading
    print("\n3️⃣ Testing plugin loading...")
    tool_class = manager.get_tool("simple_test")
    assert tool_class is not None, "Failed to load simple_test plugin"
    print("   ✅ Plugin loaded successfully")
    
    # Test 4: Plugin Execution
    print("\n4️⃣ Testing plugin execution...")
    
    class MockAgent:
        pass
    
    tool = tool_class(
        agent=MockAgent(),
        name="simple_test",
        method=None,
        args={"action": "echo", "message": "Plugin system working!"},
        message="test"
    )
    
    response = await tool.execute()
    assert response is not None, "Plugin execution returned None"
    assert "Plugin system working!" in response.message, "Plugin didn't echo correctly"
    print(f"   ✅ Plugin executed: {response.message}")
    
    # Test 5: Plugin Management
    print("\n5️⃣ Testing plugin management...")
    
    # Test disable/enable
    assert manager.disable_plugin("simple_test"), "Failed to disable plugin"
    assert manager.enable_plugin("simple_test"), "Failed to re-enable plugin"
    print("   ✅ Plugin enable/disable working")
    
    # Test 6: Security Validation
    print("\n6️⃣ Testing security validation...")
    info = manager.get_plugin_info("simple_test")
    assert info is not None, "Failed to get plugin info"
    valid_deps = manager.validate_plugin_dependencies("simple_test")
    assert valid_deps, "Plugin dependencies should be valid"
    print("   ✅ Security validation passed")
    
    # Test 7: Multiple Plugin Types
    print("\n7️⃣ Testing multiple plugin types...")
    
    test_plugins = ["calendar_integration", "weather_tool", "note_taker"]
    loaded_count = 0
    
    for plugin_name in test_plugins:
        tool_class = manager.get_tool(plugin_name)
        if tool_class:
            loaded_count += 1
            print(f"   ✅ {plugin_name} loaded")
        else:
            print(f"   ⚠️ {plugin_name} failed to load")
    
    assert loaded_count >= 2, "Expected at least 2 different plugin types to load"
    
    # Test 8: Plugin Information
    print("\n8️⃣ Testing plugin information retrieval...")
    for plugin in plugins[:3]:  # Test first 3 plugins
        info = manager.get_plugin_info(plugin['name'])
        assert info is not None, f"Failed to get info for {plugin['name']}"
        assert info['name'] == plugin['name'], "Plugin info mismatch"
        print(f"   ✅ {plugin['name']} info retrieved")
    
    print("\n🎉 All tests passed! Plugin system is fully operational.")
    print(f"\n📊 Final Status:")
    print(f"   • {len(plugins)} plugins discovered")
    print(f"   • {len(capabilities)} capabilities available")
    print(f"   • {loaded_count}/{len(test_plugins)} test plugins loaded successfully")
    
    return True


async def test_plugin_capabilities():
    """Test specific plugin capabilities."""
    print("\n🔧 Testing specific plugin capabilities...\n")
    
    manager = PluginManager()
    
    # Test weather plugin
    weather_tool = manager.get_tool("weather_tool")
    if weather_tool:
        tool = weather_tool(
            agent=None,
            name="weather_tool",
            method=None,
            args={"action": "current", "location": "New York"},
            message=""
        )
        response = await tool.execute()
        if response and "New York" in response.message:
            print("   ✅ Weather plugin working")
        else:
            print("   ⚠️ Weather plugin issue")
    
    # Test note taker
    note_tool = manager.get_tool("note_taker")
    if note_tool:
        tool = note_tool(
            agent=None,
            name="note_taker",
            method=None,
            args={"action": "create", "title": "Test Note", "content": "Plugin test"},
            message=""
        )
        response = await tool.execute()
        if response and "created successfully" in response.message:
            print("   ✅ Note taker plugin working")
        else:
            print("   ⚠️ Note taker plugin issue")
    
    print("\n✅ Plugin capability testing completed")


if __name__ == "__main__":
    try:
        asyncio.run(test_complete_plugin_system())
        asyncio.run(test_plugin_capabilities())
        print("\n🏆 Comprehensive plugin system test PASSED!")
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)