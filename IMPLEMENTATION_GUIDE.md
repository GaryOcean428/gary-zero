# Gary-Zero UI & Infrastructure Improvements

## Overview

This update addresses critical issues with subdirectory mounting, authentication loops, and agent message visibility in the Gary-Zero deployment. The changes implement proper volume management, authentication rate limiting, dynamic prompt loading, and enhanced message visibility controls.

## 🔧 Key Features Implemented

### 1. Volume Directory Management
- **Enhanced Volume Initialization**: `scripts/init_volumes.py` now creates complete directory structure
- **Subdirectories**: settings, memory, knowledge, prompts, logs, work_dir, reports, scheduler, tmp
- **Auto-initialization**: Automatic creation of config files and directory structure
- **Health Monitoring**: `/health/directories` endpoint validates volume mount status

### 2. Authentication Rate Limiting
- **Rate Limiter**: Maximum 10 authentication attempts per IP per minute
- **Log Throttling**: Maximum 5 success log messages per IP per minute  
- **IP Isolation**: Each IP address has independent rate limiting
- **Statistics**: Real-time monitoring of authentication attempts and logging

### 3. Dynamic Prompt System
- **File Watcher**: Monitors `/app/data/prompts/` for changes using watchdog
- **Auto-reload**: Supports JSON, YAML, and text prompt files
- **Agent Registry**: Automatically indexes agent capabilities and metadata
- **API Access**: RESTful endpoints for accessing prompts and agent data

### 4. Enhanced Message Visibility
- **Granular Controls**: Separate toggles for utility messages, agent messages, and JSON data
- **Persistent Settings**: Uses localStorage to remember user preferences
- **Alpine.js Integration**: Smooth integration with existing Alpine.js framework
- **Real-time Toggle**: Instant visibility changes without page reload

## 📁 Directory Structure

```
/app/data/
├── settings/
│   └── config.json          # Application settings
├── memory/
│   └── context.json         # Agent memory context
├── knowledge/
│   └── index.json           # Knowledge base index
├── prompts/
│   ├── system/              # System prompts
│   ├── tools/               # Tool prompts  
│   ├── agents/              # Agent-specific prompts
│   └── dynamic/             # Dynamic/user prompts
├── logs/                    # HTML chat logs
├── work_dir/                # Agent working directory
├── reports/                 # Generated reports
├── scheduler/
│   └── tasks.json           # Scheduled tasks
└── tmp/                     # Temporary files
```

## 🚀 API Endpoints

### Health Check
```http
GET /health/directories
```
Returns status of all required directories and files.

### Dynamic Prompts
```http
GET /api/prompts
```
Returns prompt statistics and agent registry.

```http
GET /api/agents/{agent_id}/prompt
```
Returns specific agent's prompt configuration.

## 🎛️ Message Visibility Controls

![Message Visibility Controls](https://github.com/user-attachments/assets/c94f3464-cd74-4b43-afb7-38db8c68c43a)

The enhanced UI provides three independent toggle controls:

1. **Show utility messages** - System and utility operations
2. **Show agent messages** - Agent communications and responses  
3. **Show JSON data** - Raw JSON data structures

Each toggle:
- Persists setting in localStorage
- Updates display in real-time
- Works independently of other toggles
- Maintains state across page reloads

## 🔐 Authentication Improvements

### Rate Limiting Features
- **Request Throttling**: Prevents brute force attacks
- **Log Spam Prevention**: Reduces repetitive authentication success messages
- **IP-based Tracking**: Independent limits per client IP
- **Graceful Degradation**: Returns 429 status for rate-limited requests

### Configuration
```python
# Default settings
MAX_AUTH_PER_MINUTE = 10
MAX_LOGS_PER_MINUTE = 5
```

## 📝 Dynamic Prompt Loading

### Supported Formats
- **JSON**: Structured prompt definitions with metadata
- **YAML**: Configuration-style prompts  
- **Text/Markdown**: Simple text-based prompts

### Example Agent Prompt (JSON)
```json
{
  "name": "Research Agent",
  "description": "Specialized agent for research tasks",
  "capabilities": ["web_search", "document_analysis"],
  "required_env_vars": ["OPENAI_API_KEY"],
  "prompt_template": "You are a research agent...",
  "model_preferences": {
    "primary": "gpt-4",
    "fallback": "gpt-3.5-turbo"
  }
}
```

## 🧪 Testing

### Running Tests
```bash
# Authentication rate limiter tests
python -m unittest tests.test_auth_rate_limiter -v

# Health check validation tests  
python -m unittest tests.test_health_check -v

# Volume initialization
DATA_DIR=/tmp/test-data python scripts/init_volumes.py
```

### Test Coverage
- ✅ Authentication rate limiting logic
- ✅ Directory structure validation
- ✅ File creation and permissions
- ✅ Health check endpoint logic
- ✅ Message visibility toggling

## 🐛 Issues Resolved

1. **Authentication Loop**: Fixed repetitive auth success messages with rate limiting
2. **Missing Directories**: Added automatic creation of settings and prompts directories  
3. **Agent Message Visibility**: Implemented granular control over message display
4. **Volume Mount Issues**: Added health check validation for persistent storage
5. **Static Prompts**: Enabled dynamic loading and file watching for prompts

## 📦 Dependencies Added

```txt
watchdog==5.0.3  # File system monitoring for dynamic prompts
```

## 🚀 Deployment Notes

### Railway Environment Variables
```bash
DATA_DIR=/app/data
PROMPT_DIR=/app/data/prompts  
MEMORY_DIR=/app/data/memory
KNOWLEDGE_DIR=/app/data/knowledge
SETTINGS_DIR=/app/data/settings
```

### Initialization Steps
1. Run volume initialization: `python scripts/init_volumes.py`
2. Verify health check: `curl http://localhost:3000/health/directories`
3. Check authentication rate limiting in logs
4. Test message visibility toggles in UI

### Production Checklist
- [ ] Volume mount configured at `/app/data`
- [ ] All subdirectories created and writable
- [ ] Authentication rate limiting active
- [ ] Dynamic prompt loader watching filesystem
- [ ] Message visibility controls functional
- [ ] Health check endpoint responding

## 🎯 Impact

- **Security**: Authentication rate limiting prevents spam and brute force attacks
- **Reliability**: Proper volume management ensures data persistence
- **User Experience**: Enhanced message filtering improves UI usability
- **Flexibility**: Dynamic prompt loading enables runtime configuration changes
- **Monitoring**: Health checks provide visibility into system status

The implementation successfully addresses all issues identified in the problem statement while maintaining minimal, surgical changes to the existing codebase.