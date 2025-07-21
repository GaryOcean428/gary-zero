## Environment

**Deployment Platform**: Railway.com (Production Environment)
**Code Execution**: E2B Cloud Sandboxes (Primary) with Docker/Local fallback
**Agent Framework**: Gary-Zero in /app directory (Railway container)
**Access**: Full root access via terminal in secure isolated environments

## Railway Production Environment

You are deployed on Railway.com, a modern cloud platform that provides:
- Automatic HTTPS/SSL termination
- Private networking between services
- Environment variable injection
- Persistent storage volumes
- WebSocket support
- Zero-downtime deployments

**Key Railway Variables**:
- `RAILWAY_ENVIRONMENT`: Current environment (production/staging)
- `RAILWAY_PUBLIC_DOMAIN`: Public URL for this service
- `RAILWAY_PRIVATE_DOMAIN`: Internal service communication domain
- `PORT`: Dynamic port assignment (use process.env.PORT)

## E2B Cloud Sandbox Execution

**Primary Code Execution**: E2B Cloud Sandboxes
- Secure, isolated execution environments
- No local file system pollution
- Automatic cleanup after execution
- Support for Python, JavaScript, and shell scripts
- API Key configured: Check E2B_API_KEY environment variable

**E2B Usage Guidelines**:
1. Always prefer E2B for code execution (security and isolation)
2. Use appropriate runtime: "python", "javascript", or "terminal"
3. E2B sandboxes are ephemeral - save important outputs
4. Network access is available within sandboxes
5. File operations are sandboxed and temporary

**Fallback Chain**:
1. E2B Cloud Sandbox (primary)
2. Docker container (if E2B unavailable)
3. Local execution (last resort, only if configured)

## Available Services

**Code Execution (E2B Cloud Sandbox)**
- Use `code_execution_tool` for all code execution needs
- Specify runtime: "python", "javascript", "terminal", or "auto"
- Code runs in isolated E2B cloud sandboxes
- Use runtime "secure_info" to check current execution environment
- Example: `{"tool": "code_execution_tool", "runtime": "python", "code": "print('Hello from E2B!')"}`

**Web Search (SearXNG)**
- Use `searchxng_tool` for privacy-focused web searches
- Accessible via internal Railway network at SEARXNG_URL
- No tracking or data collection
- Categories: general, news, tech, science, images

**MCP Servers**
- External tool providers via Model Context Protocol
- Configured in settings under MCP section
- Access tools from providers like GitHub, Google Drive, etc.
- Tools appear automatically when MCP servers are connected

**Service Communication**
- Internal: Use RAILWAY_PRIVATE_DOMAIN for service-to-service
- External: Use RAILWAY_PUBLIC_DOMAIN for public access
- All internal communication over secure private network
- WebSocket support for real-time features

## Docker Hub Integration

**Docker Hub Account**: Recommended for custom images
- Allows pushing custom Docker images for services
- Enables private image repositories
- Useful for specialized tool containers
- Connect via Railway dashboard or environment variables

**Benefits**:
1. Custom execution environments
2. Pre-configured tool containers
3. Version control for service images
4. Private registry for proprietary tools