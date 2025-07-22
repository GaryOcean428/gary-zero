"""
Test Backward Compatibility
===========================

Test the backward compatibility layer to ensure gary-zero can use the shared library
without breaking existing functionality.
"""

import pytest
import sys
import os

# Add the framework to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from framework.helpers.mcp_server_compat import shared_mcp_server, DynamicMcpProxy
    from framework.helpers.mcp_handler_compat import MCPConfig, MCPTool, initialize_mcp
    FRAMEWORK_IMPORTS_OK = True
except ImportError as e:
    FRAMEWORK_IMPORTS_OK = False
    FRAMEWORK_IMPORT_ERROR = str(e)


@pytest.mark.skipif(not FRAMEWORK_IMPORTS_OK, reason=f"Framework import failed: {FRAMEWORK_IMPORT_ERROR if not FRAMEWORK_IMPORTS_OK else ''}")
class TestBackwardCompatibility:
    """Test backward compatibility layer"""
    
    def test_shared_server_instance(self):
        """Test that shared server instance is created"""
        assert shared_mcp_server is not None
        assert shared_mcp_server.app_name == "Gary-Zero"
        
    def test_dynamic_proxy_creation(self):
        """Test dynamic proxy can be created"""
        # Mock settings to avoid dependency issues
        import unittest.mock
        with unittest.mock.patch('framework.helpers.mcp_server_compat.settings.get_settings') as mock_settings:
            mock_settings.return_value = {"mcp_server_token": "test-token"}
            proxy = DynamicMcpProxy()
            assert proxy is not None
            
    def test_mcp_config_compatibility(self):
        """Test MCPConfig compatibility layer"""
        config = MCPConfig.get_instance()
        assert config is not None
        assert hasattr(config, 'get_shared_client')
        
    def test_mcp_config_update(self):
        """Test MCPConfig update with empty config"""
        # Test with empty config string
        config = MCPConfig.update("")
        assert config is not None
        assert config.is_initialized()
        
    def test_initialize_mcp_function(self):
        """Test initialize_mcp function"""
        # Should not raise with empty config
        initialize_mcp("")
        
        # Should not raise with invalid JSON (should handle gracefully)
        initialize_mcp("invalid json")
        
    def test_mcp_tool_creation(self):
        """Test MCPTool can be created"""
        # Mock agent object
        import unittest.mock
        mock_agent = unittest.mock.Mock()
        mock_agent.agent_name = "test-agent"
        mock_agent.context = unittest.mock.Mock()
        mock_agent.context.log = unittest.mock.Mock()
        mock_agent.context.log.log = unittest.mock.Mock()
        
        tool = MCPTool(agent=mock_agent, name="test.tool", method=None, args={}, message="")
        assert tool is not None
        assert tool.name == "test.tool"
        assert tool.agent == mock_agent


if __name__ == "__main__":
    pytest.main([__file__, "-v"])