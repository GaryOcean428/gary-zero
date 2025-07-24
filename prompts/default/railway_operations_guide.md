# Railway Platform Operations Guide


## Overview

This guide helps AI agents understand how to operate effectively in the Railway cloud environment with E2B integration.


## Key Differences from Local Development

### 1. **Environment Variables**

- Railway injects environment variables automatically
- Access via `process.env` (Node.js) or `os.getenv()` (Python)
- Key Railway variables:
  - `PORT` - Dynamic port assignment (MUST use this)
  - `RAILWAY_ENVIRONMENT` - Current environment name
  - `RAILWAY_PUBLIC_DOMAIN` - Public URL for your service
  - `RAILWAY_PRIVATE_DOMAIN` - Internal service communication
  - `RAILWAY_PROJECT_ID` - Current project identifier
  - `RAILWAY_SERVICE_ID` - Current service identifier

### 2. **Service Communication**

- **Internal**: Use `http://$RAILWAY_PRIVATE_DOMAIN:$PORT`
- **External**: Use `https://$RAILWAY_PUBLIC_DOMAIN`
- All internal traffic stays within Railway's private network
- No egress fees for internal communication

### 3. **File System**

- `/app` - Application root directory (not /a0)
- Ephemeral by default - use volumes for persistence
- No direct host access - use E2B sandboxes for code execution

### 4. **Code Execution via E2B**

- ALL code execution happens in E2B cloud sandboxes
- Sandboxes are isolated and temporary
- Files created in sandbox don't persist
- Network access is available from sandboxes
- Railway env vars are accessible in sandboxes


## Working with MCP Servers

MCP (Model Context Protocol) servers extend agent capabilities:

1. **Configuration**: Settings → MCP → Configure Servers
2. **Available Servers**: Check MCP marketplace for providers
3. **Common MCP Tools**:
   - GitHub integration for code management
   - Google Drive for document access
   - Slack for team communication
   - Database connectors


## Best Practices for Railway

### 1. **Port Configuration**

```javascript
// CORRECT - Railway
const port = process.env.PORT || 8080;
app.listen(port, '0.0.0.0');

// WRONG - Hardcoded
app.listen(3000, 'localhost');
```

### 2. **Service Discovery**

```python
# CORRECT - Using Railway private domain
api_url = f"http://{os.getenv('BACKEND_RAILWAY_PRIVATE_DOMAIN')}:{os.getenv('BACKEND_PORT')}"

# WRONG - Hardcoded URL
api_url = "http://localhost:3001"
```

### 3. **Database Connections**

- Use Railway's database templates
- Connection strings provided via env vars
- Always use connection pooling
- Handle connection failures gracefully

### 4. **Static Assets**

- Serve via CDN when possible
- Use Railway's static file serving for small assets
- Consider object storage for large files


## Security Considerations

1. **Secrets Management**
   - Never hardcode secrets
   - Use Railway's environment variables
   - Secrets are encrypted at rest
   - Available in E2B sandboxes securely

2. **Network Security**
   - Internal traffic is isolated
   - HTTPS enforced on public domains
   - Use RAILWAY_PRIVATE_DOMAIN for internal APIs

3. **Code Execution Security**
   - E2B provides complete isolation
   - No access to Railway host system
   - Resource limits enforced
   - Automatic cleanup after execution


## Debugging in Railway

1. **Logs**: Available in Railway dashboard
2. **Metrics**: CPU, Memory, Network monitored
3. **Health Checks**: Configure in railway.toml
4. **Deployment Status**: Check build and deploy logs


## Common Patterns

### API Service Pattern

```javascript
// Express API on Railway
const app = express();

// CORS for frontend
app.use(cors({
  origin: process.env.FRONTEND_URL || 'https://app.railway.app'
}));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', env: process.env.RAILWAY_ENVIRONMENT });
});

// Start server
const port = process.env.PORT || 8080;
app.listen(port, '0.0.0.0', () => {
  console.log(`Server running on port ${port}`);
});
```

### Worker Service Pattern

```python
import os
from celery import Celery

# Redis connection from Railway
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

app = Celery('tasks', broker=redis_url)

@app.task
def process_task(data):
    # Task runs in Railway container
    return {'processed': data, 'env': os.getenv('RAILWAY_ENVIRONMENT')}
```


## Docker Hub Integration

Connecting Docker Hub provides:
1. **Custom Images**: Deploy specialized containers
2. **Private Registry**: Keep proprietary tools private
3. **Version Control**: Tag and version your images
4. **Build Caching**: Faster deployments

To connect:
1. Go to Railway Settings
2. Add Docker Hub integration
3. Use in railway.toml:

   ```toml
   [build]
   image = "yourdockerhub/image:tag"
   ```


## Troubleshooting

### Common Issues

1. **Port Binding**: Always use `0.0.0.0` and `$PORT`
2. **Memory Limits**: Check Railway plan limits
3. **Build Failures**: Check Dockerfile and dependencies
4. **Network Issues**: Verify RAILWAY_PRIVATE_DOMAIN usage
5. **E2B Failures**: Check E2B_API_KEY configuration

### Debug Commands

```bash
# Check environment
echo $RAILWAY_ENVIRONMENT

# List all Railway env vars
env | grep RAILWAY

# Test internal connectivity
curl http://$OTHER_SERVICE_RAILWAY_PRIVATE_DOMAIN:$OTHER_SERVICE_PORT/health
```

Remember: Railway handles infrastructure, E2B handles code execution, and you focus on building!
