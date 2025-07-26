# Computer Use Guide

This guide explains how to enable and use computer control capabilities with AI models in Gary-Zero.

## Overview

Computer use is a powerful capability that allows AI models to interact with desktop applications, browsers, and
system functions through screenshot analysis and simulated user inputs. This is NOT a separate model, but a tool
capability available with specific models.

## Supported Models

### Primary Support
- **Claude Sonnet 4** (`claude-sonnet-4-0`)
  - Native support via Anthropic's Computer Use API
  - Most advanced implementation
  - Full desktop control capabilities

### Secondary Support
- **GPT-4o** (`gpt-4o`, `gpt-4o-mini`)
  - Via tool integrations
  - Best for browser automation
  - Limited desktop control

## Capabilities

### What Computer Use Can Do
- **Screenshot Analysis**: Capture and understand screen content
- **Mouse Control**: Move cursor, click, drag, scroll
- **Keyboard Input**: Type text, use shortcuts, navigate
- **Window Management**: Switch between windows, minimize/maximize
- **Application Control**: Open apps, navigate menus, use features
- **Browser Automation**: Navigate websites, fill forms, extract data
- **File Operations**: Open files, save documents, organize folders

### Current Limitations
- Cannot access password-protected areas without credentials
- Limited by screen resolution and visibility
- Cannot interact with system-level security dialogs
- Performance depends on screenshot quality

## Configuration

### Basic Setup

In `framework/helpers/settings/types.py`:

```python
# Enable computer use
"computer_use_enabled": True,

# Require approval for each action (recommended initially)
"computer_use_require_approval": True,

# Screenshot capture interval (seconds)
"computer_use_screenshot_interval": 1.0,

# Maximum actions per session
"computer_use_max_actions_per_session": 50
```

### Model Configuration

Ensure you're using a supported model:

```python
# For browser automation tasks
"browser_model_provider": "ANTHROPIC",
"browser_model_name": "claude-sonnet-4-0",
```

## Usage Examples

### Basic Desktop Automation

```python
# Example: Open a text editor and write a document
1. Take screenshot to see desktop
2. Click on text editor icon
3. Wait for application to open
4. Type document content
5. Use Ctrl+S to save
6. Type filename in save dialog
7. Click Save button
```

### Web Browser Automation

```python
# Example: Search for information online
1. Open web browser
2. Navigate to search engine
3. Type search query
4. Click search button
5. Analyze results
6. Click on relevant link
7. Extract information from page
```

### Form Filling

```python
# Example: Fill out an online form
1. Navigate to form URL
2. Identify form fields from screenshot
3. Click first field
4. Type appropriate content
5. Tab to next field or click
6. Continue until form complete
7. Submit form
```

## Best Practices

### 1. Start with Approval Mode

Always start with `computer_use_require_approval: true` to:
- Understand what actions the AI plans
- Prevent unintended actions
- Learn the AI's approach

### 2. Clear Instructions

Provide specific, step-by-step instructions:

✅ Good:

```text
"Open Chrome, go to example.com, click the login button in the top right"
```

❌ Poor:

```text
"Login to the website"
```

### 3. Handle Errors Gracefully

The AI should:
- Take screenshots frequently
- Verify actions completed successfully
- Have fallback strategies
- Report issues clearly

### 4. Security Considerations

- Never share passwords in prompts
- Use environment variables for credentials
- Be cautious with sensitive data
- Monitor AI actions in secure environments

### 5. Performance Optimization

- Adjust screenshot interval based on task
- Batch related actions together
- Use keyboard shortcuts when possible
- Minimize unnecessary waiting

## Advanced Usage

### Coordinated Multi-Tool Use

Combine computer use with other capabilities:

```python
# Example: Research and document creation
1. Use web search (Perplexity) to find information
2. Use computer use to open document editor
3. Use code generation to create formatted content
4. Use computer use to save and organize files
```

### Workflow Automation

Create complex workflows:

```python
# Example: Data collection and analysis
1. Open spreadsheet application
2. Navigate to data source website
3. Extract data from multiple pages
4. Input data into spreadsheet
5. Create charts and analysis
6. Export results
```

### Testing and QA

Use for automated testing:

```python
# Example: UI testing
1. Open application under test
2. Navigate through user flows
3. Verify UI elements appear correctly
4. Test form validation
5. Check error handling
6. Generate test report
```

## Troubleshooting

### Common Issues

#### Screenshot not clear
- Increase resolution if possible
- Ensure good contrast
- Minimize overlapping windows

#### Actions not registering
- Add delays between actions
- Verify element is clickable
- Check if page fully loaded

#### Wrong element clicked
- Provide more specific descriptions
- Use unique identifiers
- Reference position on screen

### Debug Mode

Enable detailed logging:

```python
# In your agent configuration
"computer_use_debug": True,
"computer_use_save_screenshots": True,
"computer_use_log_actions": True
```

## Safety Guidelines

### Do's
- ✅ Test in safe environments first
- ✅ Use approval mode for new tasks
- ✅ Set reasonable action limits
- ✅ Monitor AI activities
- ✅ Have manual override ready

### Don'ts
- ❌ Give access to financial accounts
- ❌ Allow system-level changes without review
- ❌ Run in production without testing
- ❌ Share sensitive credentials
- ❌ Leave unattended for long periods

## Integration with Gary-Zero

### Using in Workflows

```python
from framework.tools import ComputerUseTool

# Initialize with settings
computer_tool = ComputerUseTool(
    require_approval=True,
    screenshot_interval=1.0,
    max_actions=50
)

# Use in agent workflow
agent.add_tool(computer_tool)
```

### Combining with MCP

Computer use can be exposed as an MCP tool:

```python
# In MCP server configuration
{
    "tools": [
        {
            "name": "computer_control",
            "description": "Control computer via screenshots and inputs",
            "capabilities": ["screenshot", "mouse", "keyboard"]
        }
    ]
}
```

## Examples and Templates

### Template: Web Data Extraction

```python
"""
Task: Extract product information from e-commerce site

Steps:
1. Open browser to [URL]
2. Wait for page load
3. Identify product grid/list
4. For each product:
   - Extract name
   - Extract price
   - Extract image URL
   - Extract ratings
5. Navigate to next page if exists
6. Save data to CSV file
"""
```

### Template: Document Creation

```python
"""
Task: Create formatted report

Steps:
1. Open word processor
2. Create new document
3. Add title with formatting
4. Insert table of contents
5. Add sections with headers
6. Insert data and charts
7. Format consistently
8. Save as PDF
"""
```

### Template: System Monitoring

```python
"""
Task: Check system status

Steps:
1. Open system monitor
2. Check CPU usage
3. Check memory usage
4. Check disk space
5. Open network monitor
6. Check bandwidth usage
7. Generate status report
8. Send notification if issues
"""
```

## Future Enhancements

### Planned Features
- Multi-monitor support
- Video analysis (not just screenshots)
- Gesture recognition
- Voice command integration
- Mobile device control

### API Roadmap
- Standardized computer use protocol
- Cross-platform compatibility
- Enhanced security features
- Performance optimizations
- Batch action support

## Related Documentation

- [Model Capabilities](./model-capabilities.md) - Overview of all model capabilities
- [MCP Integration](./mcp-integration.md) - Using computer use via MCP
- [Security Best Practices](./SECURE_EXECUTION.md) - Security considerations
- [API Reference](./api/) - Detailed API documentation

---

**Last Updated**: January 2025
**Version**: 1.0
