### code_execution_tool

Execute code securely using E2B cloud sandbox, Docker, or local execution
Primary method: E2B Cloud Sandboxes for maximum security and isolation

**Arguments**:
- `code`: The code to execute (properly escaped and indented)
- `runtime`: Execution environment
  - `"python"` - Python 3.11+ with common libraries
  - `"javascript"` or `"nodejs"` - Node.js environment
  - `"terminal"` - Shell commands (bash)
  - `"output"` - Get output from long-running process
  - `"reset"` - Kill process in session
  - `"secure_info"` - Check current execution environment
- `session`: Session number (0 default, use others for multitasking)

**E2B Cloud Sandbox Features**:
- Isolated execution environment per session
- No local file system access outside sandbox
- Automatic cleanup after execution
- Network access available
- Pre-installed common libraries
- Package installation via pip/npm/apt-get

**Railway Production Environment**:
- Access to Railway environment variables
- Can interact with other Railway services via private network
- Use RAILWAY_PRIVATE_DOMAIN for internal service communication
- All code runs in secure, isolated E2B sandboxes by default

**Best Practices**:
1. Always check code for placeholders before running
2. Install dependencies in terminal runtime first if needed
3. Save important outputs - sandboxes are ephemeral
4. Use print() or console.log() for output
5. Don't assume file persistence between executions
6. Wait for response before using other tools

**Example Usage**:

1. Python code execution:

~~~json
{
    "thoughts": [
        "Need to analyze data",
        "Will use pandas for processing",
        "Output results as JSON"
    ],
    "tool_name": "code_execution_tool",
    "tool_args": {
        "runtime": "python",
        "session": 0,
        "code": "import os\nimport json\n\n# Check environment\nprint(f'Environment: {os.getenv(\"RAILWAY_ENVIRONMENT\", \"local\")}')\nprint(f'E2B Sandbox: {os.getenv(\"E2B_SANDBOX_ID\", \"Not in E2B\")}')\n\n# Your code here\nresult = {'status': 'success', 'env': 'E2B'}\nprint(json.dumps(result, indent=2))"
    }
}
~~~

2. Install packages and run:

~~~json
{
    "thoughts": [
        "Need to install requests library",
        "Then make API call"
    ],
    "tool_name": "code_execution_tool",
    "tool_args": {
        "runtime": "terminal",
        "session": 0,
        "code": "pip install requests"
    }
}
~~~

3. Check execution environment:

~~~json
{
    "thoughts": [
        "Need to verify we're in secure environment",
        "Check E2B status"
    ],
    "tool_name": "code_execution_tool",
    "tool_args": {
        "runtime": "secure_info",
        "session": 0,
        "code": ""
    }
}
~~~

**Security Notes**:
- E2B sandboxes are completely isolated
- No access to host file system
- Network requests are allowed but monitored
- Execution time limits apply (configurable)
- Resource usage is constrained
- All Railway secrets/env vars available in sandbox

**Fallback Behavior**:
1. Primary: E2B Cloud Sandbox (when E2B_API_KEY configured)
2. Fallback 1: Docker container (if E2B unavailable)
3. Fallback 2: Local execution (only if explicitly enabled)

**Output Format**:
- Tool returns execution output as text
- May include [SYSTEM: ...] messages from framework
- Error messages help debug issues
- Use knowledge_tool to research error solutions
