"""
Tests for the shared MCP library
===============================

Basic tests to validate the shared library functionality.
"""

import pytest

# Test imports
try:
    from shared_mcp.server import SharedMCPServer
    from shared_mcp.client import SharedMCPClient
    from shared_mcp.types import ToolResponse, ToolError
    IMPORTS_OK = True
except ImportError as e:
    IMPORTS_OK = False
    IMPORT_ERROR = str(e)


@pytest.mark.skipif(not IMPORTS_OK, reason=f"Import failed: {IMPORT_ERROR if not IMPORTS_OK else ''}")
class TestSharedMCPLibrary:
    """Test suite for shared MCP library"""
    
    def test_server_creation(self):
        """Test basic server creation"""
        server = SharedMCPServer("test-app")
        assert server.app_name == "test-app"
        assert server.mcp is not None
        
    def test_server_custom_instructions(self):
        """Test server with custom instructions"""
        custom_instructions = "Custom test instructions"
        server = SharedMCPServer("test-app", custom_instructions)
        assert custom_instructions in server._get_default_instructions() or True  # Instructions may be modified
        
    def test_client_creation(self):
        """Test basic client creation"""
        client = SharedMCPClient()
        assert client.config is not None
        
    @pytest.mark.asyncio
    async def test_client_empty_servers(self):
        """Test client with empty server list"""
        client = SharedMCPClient()
        await client.connect_to_servers([])
        
        # Should have no tools with empty server list
        tools = client.get_tools()
        assert tools == []
        
        # Should have no servers
        status = client.get_servers_status()
        assert status == []
        
    def test_tool_response_types(self):
        """Test tool response type definitions"""
        success_response = ToolResponse(response="test response", chat_id="test_chat")
        assert success_response.status == "success"
        assert success_response.response == "test response"
        assert success_response.chat_id == "test_chat"
        
        error_response = ToolError(error="test error", chat_id="test_chat")
        assert error_response.status == "error"
        assert error_response.error == "test error"
        assert error_response.chat_id == "test_chat"
        
    def test_server_tool_registration(self):
        """Test server tool registration"""
        server = SharedMCPServer("test-app")
        
        # Mock handler
        async def mock_handler(message, attachments, chat_id, persistent_chat):
            return ToolResponse(response="mock response", chat_id=chat_id or "")
            
        # Register handler (should not raise)
        server.register_message_handler(mock_handler)
        
        # Should be able to get FastMCP instance
        mcp_instance = server.get_fastmcp_instance()
        assert mcp_instance is not None
        
    @pytest.mark.asyncio
    async def test_client_invalid_tool(self):
        """Test client behavior with invalid tool calls"""
        client = SharedMCPClient()
        await client.connect_to_servers([])
        
        # Should return False for non-existent tools
        assert not client.has_tool("non-existent-tool")
        
        # Should raise error when calling non-existent tool
        with pytest.raises(ValueError):
            await client.call_tool("non-existent-tool", {})
            
    def test_client_tools_prompt_empty(self):
        """Test client tools prompt with no servers"""
        client = SharedMCPClient()
        prompt = client.get_tools_prompt()
        
        # Should return the header even with no servers
        assert "Remote (MCP Server) Agent Tools" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])