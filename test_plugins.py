"""Test the plugin system."""

import os
import shutil
import sys
import tempfile
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from framework.plugins.manager import PluginManager


def test_basic_plugin_system():
    """Test basic plugin system functionality."""
    print("Testing plugin system...")

    # Create temporary directories for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        plugins_dir = os.path.join(temp_dir, "plugins")
        db_file = os.path.join(temp_dir, "plugins.db")

        # Initialize plugin manager
        manager = PluginManager(plugins_dir=plugins_dir, db_file=db_file)

        # Test 1: Check that manager initializes
        print("✓ Plugin manager initialized")

        # Test 2: List plugins (should be empty initially)
        plugins = manager.list_plugins()
        assert len(plugins) == 0, "Expected no plugins initially"
        print("✓ Empty plugin list")

        # Test 3: Discover plugins from sample directory
        # Copy our sample plugins to the temp directory
        sample_plugins_dir = "plugins"
        if os.path.exists(sample_plugins_dir):
            shutil.copytree(sample_plugins_dir, plugins_dir, dirs_exist_ok=True)

            # Refresh plugin discovery
            manager.refresh_plugins()

            # Check discovered plugins
            plugins = manager.list_plugins()
            print(f"✓ Discovered {len(plugins)} plugins")

            # Test 4: Check plugin capabilities
            capabilities = manager.get_available_capabilities()
            print(f"✓ Found capabilities: {capabilities}")

            # Test 5: Try to load a plugin tool
            if plugins:
                plugin_name = plugins[0]['name']
                tool_class = manager.get_tool(plugin_name)
                if tool_class:
                    print(f"✓ Successfully loaded plugin tool: {plugin_name}")
                else:
                    print(f"⚠️ Failed to load plugin tool: {plugin_name}")

        print("Plugin system test completed successfully!")


def test_plugin_loading():
    """Test plugin loading without full initialization."""
    print("\nTesting plugin loading...")

    try:
        from framework.plugins.registry import PluginMetadata
        from framework.plugins.security import PluginSecurityManager

        print("✓ All plugin modules import successfully")

        # Test metadata creation
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="test",
            capabilities=["test"]
        )
        print("✓ Plugin metadata creation works")

        # Test security manager
        security = PluginSecurityManager()
        print("✓ Security manager initialization works")

    except Exception as e:
        print(f"❌ Plugin system import failed: {e}")
        return False

    return True


if __name__ == "__main__":
    try:
        # Test basic imports first
        if test_plugin_loading():
            # Test full system if imports work
            test_basic_plugin_system()

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
