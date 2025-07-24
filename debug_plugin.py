"""Debug plugin loading."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import asyncio

from framework.plugins.manager import PluginManager


async def debug_plugin():
    manager = PluginManager()

    # Get tool class
    tool_class = manager.get_tool("simple_test")
    print(f"Tool class: {tool_class}")
    print(f"Tool class name: {tool_class.__name__ if tool_class else 'None'}")

    if tool_class:
        # Check methods
        print(f"Has execute method: {hasattr(tool_class, 'execute')}")

        # Create instance
        class MockAgent:
            pass

        tool = tool_class(
            agent=MockAgent(),
            name="simple_test",
            method=None,
            args={"action": "info"},
            message="test",
        )

        print(f"Tool instance: {tool}")
        print(f"Tool args: {tool.args}")

        # Try execute
        try:
            print("Calling execute...")
            result = await tool.execute()
            print(f"Execute result: {result}")
            print(f"Result type: {type(result)}")
            if result:
                print(f"Result message: {result.message}")
        except Exception as e:
            print(f"Execute error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_plugin())
