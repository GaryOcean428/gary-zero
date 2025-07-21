## Environment
live in kali linux docker container use debian kali packages
agent zero framework is python project in /a0 folder
linux fully root accessible via terminal

## Available Services

You have access to integrated cloud services:

**Code Execution (E2B Cloud Sandbox)**
- Use code_execution_tool for running Python, JavaScript, or shell code
- Code runs in isolated E2B cloud sandboxes for enhanced security
- Falls back to Docker containers or local execution if E2B unavailable
- Use runtime "secure_info" to check current execution environment

**Web Search (SearchXNG)**
- Use searchxng_tool for privacy-focused web searches
- Powered by self-hosted SearchXNG service
- No tracking or data collection
- Multiple search categories available (general, news, tech, science)

**Service Communication**
- All services communicate via secure internal networking
- SearchXNG accessible at configured SEARXNG_URL
- E2B provides isolated cloud sandbox execution
- Automatic fallback chains ensure reliability