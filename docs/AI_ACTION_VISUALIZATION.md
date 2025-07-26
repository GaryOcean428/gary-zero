# AI Action Visualization System

The AI Action Visualization System provides comprehensive real-time transparency for all AI provider actions including Claude Computer Use, OpenAI Operator, Google AI models, browser automation, desktop interactions, and visual computer tasks.

## Architecture Overview

The system consists of several integrated components:

### 1. Action Interceptor Middleware (`ai_action_interceptor.py`)

- **Purpose**: Captures actions from all major AI providers
- **Providers Supported**:
  - Anthropic Claude Computer Use
  - OpenAI Operator
  - Google AI models
  - Browser automation tools
  - Kali shell commands
  - Gary-Zero native tools

### 2. Real-time Streaming Service (`ai_action_streaming.py`)

- **Purpose**: WebSocket-based real-time action broadcasting
- **Features**:
  - Multi-client support
  - Action filtering and subscriptions
  - Message history and replay
  - Connection management

### 3. Multi-Modal Visualization Manager (`ai-action-visualization.js`)

- **Purpose**: Frontend visualization with morphism effects
- **Visualization Types**:
  - Terminal/shell interfaces
  - Browser automation previews
  - Desktop mirroring
  - Screenshot galleries
  - Code execution displays

### 4. Tool Integration Layer (`ai_action_visualization.py`)

- **Purpose**: Gary-Zero tool framework integration
- **Tools Provided**:
  - `ai_action_visualize` - Create visualizations
  - `ai_action_update` - Update existing visualizations
  - `ai_action_streaming` - Control streaming service
  - `ai_action_interception` - Control action interception

## Getting Started

### 1. System Initialization

The system automatically initializes when Gary-Zero starts:

```python
from framework.helpers.ai_visualization_init import initialize_ai_visualization

# Initialize during application startup
await initialize_ai_visualization()
```

### 2. Manual Control

Control the system programmatically:

```python
from framework.helpers.ai_action_interceptor import start_ai_action_interception
from framework.helpers.ai_action_streaming import start_action_streaming

# Start interception
start_ai_action_interception()

# Start streaming service
await start_action_streaming(host="localhost", port=8765)
```

### 3. Using Visualization Tools

In agent code:

```python
# Create a computer use visualization
result = await ai_action_visualize(
    provider="anthropic_claude",
    action_type="computer_use",
    description="Taking screenshot for analysis",
    parameters={"action": "screenshot"},
    session_id="claude_session_1"
)

# Update when completed
await ai_action_update(
    session_id="claude_session_1",
    status="completed",
    execution_time=1.2,
    screenshot_path="/tmp/screenshot.png"
)
```

## Configuration

Configure via environment variables:

```bash
# Auto-start features
AI_VISUALIZATION_AUTO_START=true
AI_STREAMING_AUTO_START=true

# Streaming configuration
AI_STREAMING_HOST=localhost
AI_STREAMING_PORT=8765

# System settings
AI_MAX_ACTION_HISTORY=1000
AI_WEBSOCKET_ENABLED=true
AI_VISUALIZATION_DEBUG=false
```

## Action Types

### Computer Use Actions

- **Screenshots**: Capturing screen state
- **Mouse Actions**: Clicks, drags, movements
- **Keyboard Actions**: Text input, key combinations
- **Window Operations**: Management and control

### Browser Automation

- **Navigation**: URL changes, page loads
- **Form Interactions**: Input filling, submissions
- **Element Interactions**: Clicks, hovers, selections
- **Data Extraction**: Scraping, content analysis

### Desktop Interactions

- **File Operations**: Create, move, delete, organize
- **Application Control**: Launch, manage, terminate
- **System Operations**: Settings, configurations

### Shell Commands

- **Security Tools**: nmap, nikto, sqlmap scans
- **System Commands**: File operations, network tools
- **Development Tools**: Compilation, testing, deployment

### Visual Computer Tasks

- **Image Analysis**: Screenshot interpretation
- **UI Component Detection**: Element recognition
- **Accessibility Auditing**: Compliance checking

## Visualization Features

### Real-time Display

- **Instant Updates**: Actions appear immediately
- **Live Streaming**: WebSocket-based real-time data
- **Status Updates**: Progress and completion indicators

### Multi-Modal Support

- **Terminal Interfaces**: Live terminal sessions
- **Browser Previews**: Real-time page views
- **Desktop Mirroring**: Screen sharing capabilities
- **Screenshot Galleries**: Image collections with zoom

### Interactive Controls

- **Minimize/Maximize**: Space management
- **Pop-out Windows**: Dedicated viewing
- **Session Management**: Start/stop controls
- **Filtering**: Provider and action type filters

### Morphism Design

- **Glass Effect**: Translucent containers with blur
- **Smooth Animations**: Enter/exit transitions
- **Provider Colors**: Distinct visual identities
- **Responsive Layout**: Mobile and desktop optimized

## WebSocket API

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8765');
```

### Message Format

```json
{
  "message_id": "uuid",
  "message_type": "ai_action",
  "data": {
    "action_id": "uuid",
    "provider": "anthropic_claude",
    "action_type": "computer_use",
    "description": "Action description",
    "status": "started|completed|failed|error",
    "ui_url": "https://...",
    "timestamp": "ISO8601"
  },
  "timestamp": "ISO8601"
}
```

### Subscriptions

```javascript
// Subscribe to specific providers
ws.send(JSON.stringify({
  type: 'subscribe',
  subscriptions: ['anthropic_claude', 'browser_use']
}));

// Subscribe to action types
ws.send(JSON.stringify({
  type: 'subscribe',
  subscriptions: ['computer_use', 'shell_command']
}));

// Subscribe to all
ws.send(JSON.stringify({
  type: 'subscribe',
  subscriptions: ['all']
}));
```

### Filtering

```javascript
// Set provider filter
ws.send(JSON.stringify({
  type: 'set_filter',
  filters: {
    provider: ['anthropic_claude', 'openai_operator'],
    action_type: ['computer_use', 'browser_automation']
  }
}));
```

## Provider Integration

### Anthropic Claude Computer Use

- **Automatic Detection**: Hooks into computer use tool calls
- **Action Mapping**: Screenshots, clicks, typing, scrolling
- **UI Integration**: Real-time desktop visualization

### OpenAI Operator

- **Ready for Integration**: Hooks prepared for operator calls
- **Action Support**: Desktop operations, file management
- **Extensible**: Easy to add when operator becomes available

### Google AI Models

- **Integration Ready**: Framework supports Google AI actions
- **Visual Tasks**: Computer vision and UI analysis
- **Flexible**: Adaptable to Google's AI capabilities

### Browser Automation

- **Multi-Tool Support**: Various browser automation libraries
- **Live Preview**: Real-time browser state visualization
- **Action Tracking**: Navigation, interactions, data extraction

### Kali Shell Integration

- **Security Focus**: Specialized for penetration testing tools
- **Terminal Visualization**: Live terminal session display
- **Tool Integration**: nmap, nikto, sqlmap, metasploit support

## Agent Prompt Integration

The system automatically enhances agent prompts with visualization awareness:

```
## AI Action Visualization System

You now have access to comprehensive AI action visualization that provides real-time
transparency for all AI provider actions...

### When to Use Visualizations:
- Computer Use Actions: Screenshots, clicks, keyboard input
- Browser Automation: Web navigation, form filling, scraping
- Desktop Interactions: File operations, window management
- Shell Commands: Terminal operations, security tools
- Visual Tasks: Image analysis, screenshot comparisons
```

## Demo and Testing

### Run the Demo

```bash
python demo_ai_visualization.py
```

### Test Components

```bash
# Test interception
python -c "from framework.helpers.ai_action_interceptor import get_ai_action_manager; m = get_ai_action_manager(); m.start_interception(); print('Interception active:', m.active)"

# Test streaming
python -c "import asyncio; from framework.helpers.ai_action_streaming import start_action_streaming; asyncio.run(start_action_streaming())"
```

### Validation Script

```bash
python validate_ai_visualization.py
```

## Security Considerations

### Action Isolation

- **Sandboxed Execution**: Actions run in isolated environments
- **Permission Controls**: User approval for sensitive operations
- **Audit Trail**: Complete action history and logging

### Data Privacy

- **Local Processing**: No external data transmission
- **Secure Channels**: Encrypted WebSocket connections
- **Access Control**: Authentication and authorization

### Network Security

- **Internal Communication**: Railway private network usage
- **Firewall Integration**: Proper port and access controls
- **SSL/TLS Support**: Encrypted connections in production

## Troubleshooting

### Common Issues

**WebSocket Connection Failed**

```bash
# Check if streaming service is running
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" ws://localhost:8765
```

**Actions Not Appearing**

```python
# Check interception status
from framework.helpers.ai_action_interceptor import get_ai_action_manager
manager = get_ai_action_manager()
print("Active:", manager.active)
print("Providers:", list(manager.interceptors.keys()))
```

**UI Not Loading**
- Verify `ai-action-visualization.js` is included in HTML
- Check browser console for JavaScript errors
- Ensure WebSocket URL is correct

### Debug Mode

Enable debug logging:

```bash
export AI_VISUALIZATION_DEBUG=true
```

### Log Analysis

Check logs for system status:

```bash
grep "AI.*Visualization\|Action.*Streaming\|Interception" logs/application.log
```

## Performance Optimization

### Memory Management

- **Action History Limits**: Configurable history size
- **Client Cleanup**: Automatic disconnection handling
- **Resource Monitoring**: Memory and CPU usage tracking

### Network Optimization

- **Message Batching**: Efficient data transmission
- **Compression**: GZip compression for large payloads
- **Connection Pooling**: Optimized WebSocket management

### UI Performance

- **Animation Throttling**: Performance-aware animations
- **Lazy Loading**: On-demand component initialization
- **Responsive Design**: Mobile-optimized interfaces

## Extensibility

### Adding New Providers

1. Create provider interceptor class
2. Implement action mapping
3. Register with action manager
4. Add UI visualization support

### Custom Action Types

1. Extend `AIActionType` enum
2. Add visualization mapping
3. Implement UI components
4. Update documentation

### Integration Hooks

- **Tool Integration**: Easy framework integration
- **Event System**: Extensible event handling
- **Plugin Architecture**: Modular component system

## Deployment

### Railway Configuration

The system is optimized for Railway deployment:
- **Auto-scaling**: WebSocket service scaling
- **Environment Variables**: Proper configuration management
- **Health Checks**: System status monitoring

### Production Settings

```bash
# Production environment variables
AI_STREAMING_HOST=0.0.0.0
AI_STREAMING_PORT=${PORT:-8765}
AI_WEBSOCKET_ENABLED=true
AI_VISUALIZATION_AUTO_START=true
```

### Monitoring

- **System Status**: Health check endpoints
- **Performance Metrics**: Action processing statistics
- **Error Tracking**: Comprehensive error logging

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review system logs
3. Run the validation script
4. Open a GitHub issue with system status output

## Version History

- **v1.0.0**: Initial implementation with multi-provider support
- **v1.1.0**: Enhanced WebSocket streaming and UI improvements
- **v1.2.0**: Railway deployment optimization and security enhancements
