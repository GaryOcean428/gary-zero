# Migration Guide: Shared MCP Library

This guide helps repositories migrate to using the shared MCP library extracted from gary-zero.

## Overview

The shared MCP library provides:
- **Backward Compatibility**: Existing gary-zero code continues to work
- **Shared Implementation**: Gold standard MCP implementation for all repos
- **Flexibility**: Can be used directly or through compatibility layer
- **Extensibility**: Easy to customize for specific repository needs

## Migration Strategy

### Phase 1: Immediate (No Changes Required)
- **Status**: ✅ Complete
- **Action**: None required - backward compatibility maintained
- **Benefit**: Existing code continues to work unchanged

### Phase 2: Gradual Adoption (Optional)
- **Timeline**: Next 2-4 weeks
- **Action**: Start using shared library for new features
- **Benefit**: Cleaner architecture and shared improvements

### Phase 3: Full Migration (Future)
- **Timeline**: 1-3 months
- **Action**: Migrate existing code to shared library
- **Benefit**: Simplified codebase and better maintainability

## For Repository Owners

### Gary-Zero (Current Repository)
**Status**: ✅ Already integrated with backward compatibility

**What Changed**:
- MCP implementation moved to `shared_mcp/` library
- Original files now import from compatibility layer
- All existing imports continue to work

**What to Do**:
- Nothing required immediately
- Consider migrating new features to use shared library directly
- Existing code continues to work unchanged

### Monkey1 Repository
**Installation**:
```bash
# Option 1: Copy shared_mcp directory
cp -r gary-zero/shared_mcp/ monkey1/

# Option 2: Install as package (future)
pip install shared-mcp
```

**Basic Integration**:
```python
# In monkey1/mcp_server.py
from shared_mcp.server import SharedMCPServer

server = SharedMCPServer("monkey1", "Monkey1 data analysis agent")

async def handle_analysis(message, attachments, chat_id, persistent_chat):
    # Your analysis logic here
    result = analyze_data(message)
    return {"status": "success", "response": result, "chat_id": chat_id or ""}

server.register_message_handler(handle_analysis)
```

### Gary8D Repository
**Installation**: Same as Monkey1

**Basic Integration**:
```python
# In gary8d/mcp_server.py
from shared_mcp.server import SharedMCPServer

server = SharedMCPServer("gary8d", "Gary8D planning and reasoning agent")

async def handle_planning(message, attachments, chat_id, persistent_chat):
    # Your planning logic here
    plan = create_plan(message)
    return {"status": "success", "response": plan, "chat_id": chat_id or ""}

server.register_message_handler(handle_planning)
```

## Migration Patterns

### Pattern 1: Server-Side Integration

**Before (Repository-Specific)**:
```python
# Custom MCP implementation in each repo
class CustomMCPServer:
    def __init__(self):
        # Custom implementation
        pass
```

**After (Shared Library)**:
```python
from shared_mcp.server import SharedMCPServer

class MyAppServer:
    def __init__(self):
        self.mcp_server = SharedMCPServer("my-app")
        self._setup_handlers()
    
    def _setup_handlers(self):
        async def my_handler(message, attachments, chat_id, persistent_chat):
            # App-specific logic
            return process_message(message)
        
        self.mcp_server.register_message_handler(my_handler)
```

### Pattern 2: Client-Side Integration

**Before (Repository-Specific)**:
```python
# Custom client implementation
class CustomMCPClient:
    def __init__(self):
        # Custom implementation
        pass
```

**After (Shared Library)**:
```python
from shared_mcp.client import SharedMCPClient

class MyAppClient:
    def __init__(self):
        self.mcp_client = SharedMCPClient()
    
    async def connect_to_services(self):
        configs = [
            {"name": "gary-zero", "url": "http://gary-zero:8000/sse"},
            {"name": "monkey1", "url": "http://monkey1:8001/sse"}
        ]
        await self.mcp_client.connect_to_servers(configs)
```

### Pattern 3: Cross-Repository Communication

**New Capability**: Repositories can easily communicate with each other

```python
# In any repository
from shared_mcp.client import SharedMCPClient

async def get_analysis_from_monkey1(data):
    client = SharedMCPClient()
    await client.connect_to_servers([{
        "name": "monkey1",
        "url": "http://monkey1.local:8001/sse"
    }])
    
    result = await client.call_tool("monkey1.analyze", {"data": data})
    return result

async def get_plan_from_gary8d(goal):
    client = SharedMCPClient()
    await client.connect_to_servers([{
        "name": "gary8d", 
        "url": "http://gary8d.local:8002/sse"
    }])
    
    result = await client.call_tool("gary8d.plan", {"goal": goal})
    return result
```

## Testing Your Migration

### 1. Unit Tests
```python
import pytest
from shared_mcp.server import SharedMCPServer
from shared_mcp.client import SharedMCPClient

def test_server_creation():
    server = SharedMCPServer("test-app")
    assert server.app_name == "test-app"

@pytest.mark.asyncio
async def test_client_functionality():
    client = SharedMCPClient()
    await client.connect_to_servers([])
    assert client.get_servers_status() == []
```

### 2. Integration Tests
```python
@pytest.mark.asyncio
async def test_server_client_integration():
    # Test that your server and client work together
    server = SharedMCPServer("test-app")
    
    async def test_handler(message, attachments, chat_id, persistent_chat):
        return {"status": "success", "response": f"Echo: {message}", "chat_id": chat_id or ""}
    
    server.register_message_handler(test_handler)
    
    # Test with actual FastMCP instance
    mcp_instance = server.get_fastmcp_instance()
    assert mcp_instance is not None
```

### 3. Compatibility Tests
```python
def test_backward_compatibility():
    """Test that existing gary-zero imports still work"""
    try:
        from framework.helpers.mcp_server import mcp_server
        from framework.helpers.mcp_handler import MCPConfig
        assert mcp_server is not None
        assert MCPConfig is not None
    except ImportError:
        pytest.fail("Backward compatibility broken")
```

## Troubleshooting

### Common Issues

**Issue 1: Import Errors**
```
ModuleNotFoundError: No module named 'shared_mcp'
```
**Solution**: Ensure shared_mcp directory is in your Python path or install as package

**Issue 2: Dependency Conflicts**
```
ImportError: cannot import name 'FastMCP' from 'fastmcp'
```
**Solution**: Install required dependencies: `pip install fastmcp mcp pydantic starlette`

**Issue 3: Configuration Errors**
```
ValueError: "MCPConfig" object has no field "settings_provider"
```
**Solution**: Use proper settings provider function instead of direct attribute assignment

### Validation Steps

1. **Check Imports**:
   ```python
   from shared_mcp.server import SharedMCPServer
   from shared_mcp.client import SharedMCPClient
   print("✅ Imports successful")
   ```

2. **Test Basic Functionality**:
   ```python
   server = SharedMCPServer("test")
   client = SharedMCPClient()
   print("✅ Basic functionality works")
   ```

3. **Verify Backward Compatibility** (Gary-Zero only):
   ```python
   from framework.helpers.mcp_server import mcp_server
   from framework.helpers.mcp_handler import MCPConfig
   print("✅ Backward compatibility maintained")
   ```

## Best Practices

### 1. Configuration Management
```python
# Good: Use environment-specific settings
def get_settings():
    if os.getenv("ENVIRONMENT") == "production":
        return {"mcp_client_init_timeout": 30}
    return {"mcp_client_init_timeout": 60}

client = SharedMCPClient(get_settings)
```

### 2. Error Handling
```python
# Good: Proper error handling in handlers
async def safe_handler(message, attachments, chat_id, persistent_chat):
    try:
        result = process_message(message)
        return ToolResponse(response=result, chat_id=chat_id or "")
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return ToolError(error=str(e), chat_id=chat_id or "")
```

### 3. Resource Cleanup
```python
# Good: Proper async context management
async def use_client():
    client = SharedMCPClient()
    try:
        await client.connect_to_servers(configs)
        # Use client
    finally:
        # Cleanup if needed
        pass
```

## Timeline and Rollout

### Week 1-2: Assessment
- [ ] Review current MCP usage in your repository
- [ ] Identify integration points
- [ ] Plan migration approach

### Week 3-4: Implementation  
- [ ] Copy/install shared library
- [ ] Implement basic server integration
- [ ] Add client functionality if needed

### Week 5-6: Testing
- [ ] Run integration tests
- [ ] Validate cross-repository communication
- [ ] Performance testing

### Week 7-8: Deployment
- [ ] Deploy to staging environment
- [ ] Monitor and fix issues
- [ ] Deploy to production

## Support and Resources

### Documentation
- `shared_mcp/README.md`: Library overview
- `shared_mcp/EXAMPLES.md`: Usage examples
- `shared_mcp/tests/`: Test examples

### Code Examples
- `test_integration_simple.py`: Basic integration test
- `shared_mcp/tests/test_shared_mcp.py`: Unit tests
- `shared_mcp/tests/test_backward_compatibility.py`: Compatibility tests

### Getting Help
1. Check existing tests for usage patterns
2. Review example implementations in EXAMPLES.md
3. Test with simple integration first before complex features
4. Validate that existing functionality still works

## Success Criteria

### Phase 1 (Immediate)
- [x] Existing gary-zero functionality unchanged
- [x] No breaking changes for current users
- [x] Shared library available for use

### Phase 2 (2-4 weeks)
- [ ] At least one other repository using shared library
- [ ] Cross-repository communication working
- [ ] Performance comparable to original implementation

### Phase 3 (1-3 months)
- [ ] All repositories using shared library
- [ ] Simplified maintenance across ecosystem
- [ ] Enhanced cross-repository capabilities

The migration is designed to be low-risk with immediate benefits and long-term architectural improvements.