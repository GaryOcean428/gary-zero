"""
Tests for Remote Session Management System.
"""

import asyncio
import pytest
import uuid
from unittest.mock import Mock, AsyncMock, patch

from framework.session import (
    SessionType, SessionState, SessionMessage, SessionResponse,
    RemoteSessionManager, SessionConfig, ConnectionPool
)
from framework.session.integration import create_session_manager


class TestSessionManager:
    """Test cases for RemoteSessionManager."""
    
    @pytest.fixture
    async def session_manager(self):
        """Create a test session manager."""
        config = SessionConfig()
        config.enable_connection_pooling = False  # Disable for simpler testing
        manager = RemoteSessionManager(config)
        
        # Register mock session factory
        async def mock_session_factory(**kwargs):
            session = Mock()
            session.session_id = str(uuid.uuid4())
            session.session_type = SessionType.CLI
            session.connect = AsyncMock(return_value=SessionResponse(success=True, message="Connected"))
            session.disconnect = AsyncMock(return_value=SessionResponse(success=True, message="Disconnected"))
            session.execute = AsyncMock(return_value=SessionResponse(success=True, message="Executed"))
            session.health_check = AsyncMock(return_value=SessionResponse(success=True, message="Healthy"))
            session.is_connected = AsyncMock(return_value=True)
            session.get_metadata = AsyncMock(return_value=Mock())
            session.update_state = AsyncMock()
            return session
        
        manager.register_session_factory(SessionType.CLI, mock_session_factory)
        
        await manager.start()
        yield manager
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_session_creation(self, session_manager):
        """Test session creation."""
        session = await session_manager.create_session(SessionType.CLI)
        
        assert session is not None
        assert session.session_id is not None
        session.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_with_session(self, session_manager):
        """Test executing messages with sessions."""
        message = session_manager.create_message(
            message_type="test",
            payload={"action": "test"}
        )
        
        response = await session_manager.execute_with_session(
            SessionType.CLI, message
        )
        
        assert response.success
        assert response.message == "Executed"
    
    @pytest.mark.asyncio
    async def test_session_stats(self, session_manager):
        """Test getting session manager statistics."""
        stats = await session_manager.get_manager_stats()
        
        assert 'running' in stats
        assert 'config' in stats
        assert 'registered_factories' in stats
        assert stats['running'] is True


class TestConnectionPool:
    """Test cases for ConnectionPool."""
    
    @pytest.fixture
    def connection_pool(self):
        """Create a test connection pool."""
        config = SessionConfig()
        config.pool_size_per_type = 2
        config.max_idle_time = 1  # Short timeout for testing
        return ConnectionPool(config)
    
    @pytest.mark.asyncio
    async def test_pool_start_stop(self, connection_pool):
        """Test pool lifecycle."""
        await connection_pool.start()
        assert connection_pool._running
        
        await connection_pool.stop()
        assert not connection_pool._running
    
    @pytest.mark.asyncio
    async def test_session_pooling(self, connection_pool):
        """Test session pooling and reuse."""
        await connection_pool.start()
        
        # Mock session factory
        async def mock_factory(**kwargs):
            session = Mock()
            session.session_id = str(uuid.uuid4())
            session.session_type = SessionType.CLI
            session.connect = AsyncMock(return_value=SessionResponse(success=True, message="Connected"))
            session.disconnect = AsyncMock(return_value=SessionResponse(success=True, message="Disconnected"))
            session.health_check = AsyncMock(return_value=SessionResponse(success=True, message="Healthy"))
            session.is_connected = AsyncMock(return_value=True)
            session.update_state = AsyncMock()
            return session
        
        try:
            # Get first session
            session1 = await connection_pool.get_session(SessionType.CLI, mock_factory)
            assert session1 is not None
            
            # Return to pool
            await connection_pool.return_session(session1)
            
            # Get second session (should reuse)
            session2 = await connection_pool.get_session(SessionType.CLI, mock_factory)
            assert session2.session_id == session1.session_id  # Same session reused
            
        finally:
            await connection_pool.stop()


class TestSessionConfig:
    """Test cases for SessionConfig."""
    
    def test_config_from_environment(self):
        """Test configuration loading from environment."""
        with patch.dict('os.environ', {
            'SESSION_MAX_PER_TYPE': '15',
            'SESSION_TIMEOUT': '600',
            'GEMINI_CLI_ENABLED': 'true',
            'KALI_SERVICE_ENABLED': 'true'
        }):
            config = SessionConfig.from_environment()
            
            assert config.max_sessions_per_type == 15
            assert config.session_timeout == 600
            assert config.is_tool_enabled('gemini_cli')
            assert config.is_tool_enabled('kali_service')
    
    def test_tool_configuration(self):
        """Test tool-specific configuration."""
        config = SessionConfig.from_environment()
        
        gemini_config = config.get_tool_config('gemini_cli')
        assert 'enabled' in gemini_config
        assert 'cli_path' in gemini_config
        
        kali_config = config.get_tool_config('kali_service')
        assert 'enabled' in kali_config
        assert 'base_url' in kali_config
    
    def test_approval_requirements(self):
        """Test approval requirement logic."""
        config = SessionConfig()
        
        assert config.requires_approval(SessionType.GUI)
        assert config.requires_approval(SessionType.TERMINAL)
        assert config.requires_approval(SessionType.HTTP)


class TestSessionIntegration:
    """Test cases for session integration."""
    
    @pytest.mark.asyncio
    async def test_create_session_manager(self):
        """Test session manager creation with integration."""
        manager = create_session_manager()
        
        assert manager is not None
        assert len(manager._session_factories) > 0
        
        await manager.stop()
    
    def test_session_factories(self):
        """Test session factory functions."""
        from framework.session.integration import (
            create_gemini_session, create_kali_session,
            create_anthropic_session, create_claude_code_session
        )
        
        # Test that factories are callable (they are now async functions)
        import inspect
        
        assert inspect.iscoroutinefunction(create_gemini_session)
        assert inspect.iscoroutinefunction(create_kali_session)
        assert inspect.iscoroutinefunction(create_anthropic_session)
        assert inspect.iscoroutinefunction(create_claude_code_session)


class TestWorkflows:
    """Test cases for example workflows."""
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self):
        """Test that workflows can be instantiated and configured."""
        from examples.session_workflows import CodeGenerationWorkflow, SecurityAuditWorkflow
        
        # Create mock session manager
        mock_manager = Mock()
        mock_manager.create_message = Mock(return_value=Mock())
        mock_manager.execute_with_session = AsyncMock(return_value=SessionResponse(
            success=True, 
            message="Mock response",
            data={'result': 'mock result'}
        ))
        
        # Test code generation workflow
        code_workflow = CodeGenerationWorkflow(mock_manager)
        assert code_workflow is not None
        
        # Test security audit workflow
        audit_workflow = SecurityAuditWorkflow(mock_manager)
        assert audit_workflow is not None
        
        # Test workflow execution (mocked)
        results = await code_workflow.run()
        assert 'workflow' in results
        assert 'steps' in results


# Integration test for the complete system
@pytest.mark.integration
class TestSystemIntegration:
    """Integration tests for the complete session management system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_session_flow(self):
        """Test complete end-to-end session flow."""
        # This test would require actual services to be available
        # For now, we'll test the configuration and setup
        
        config = SessionConfig.from_environment()
        manager = RemoteSessionManager(config)
        
        # Register mock factories
        async def mock_factory(**kwargs):
            session = Mock()
            session.session_id = str(uuid.uuid4())
            session.session_type = SessionType.CLI
            session.connect = AsyncMock(return_value=SessionResponse(success=True, message="Connected"))
            session.disconnect = AsyncMock(return_value=SessionResponse(success=True, message="Disconnected"))
            session.execute = AsyncMock(return_value=SessionResponse(
                success=True, 
                message="Executed",
                data={'result': 'test output'}
            ))
            session.health_check = AsyncMock(return_value=SessionResponse(success=True, message="Healthy"))
            session.is_connected = AsyncMock(return_value=True)
            session.get_metadata = AsyncMock(return_value=Mock())
            session.update_state = AsyncMock()
            return session
        
        manager.register_session_factory(SessionType.CLI, mock_factory)
        
        try:
            await manager.start()
            
            # Create a test message
            message = manager.create_message(
                message_type="test",
                payload={"action": "test", "data": "test_data"}
            )
            
            # Execute with session
            response = await manager.execute_with_session(SessionType.CLI, message)
            
            assert response.success
            assert response.data is not None
            
            # Get stats
            stats = await manager.get_manager_stats()
            assert stats['running']
            
        finally:
            await manager.stop()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])