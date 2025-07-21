# E2B and Docker Hub Configuration Guide

## E2B Setup (Required for Secure Code Execution)

### 1. Get E2B API Key
1. Visit https://e2b.dev
2. Sign up for an account
3. Go to Dashboard → API Keys
4. Create a new API key
5. Copy the key (starts with `e2b_`)

### 2. Configure in Railway
1. Go to your Railway project
2. Navigate to service → Variables
3. Add: `E2B_API_KEY=e2b_your_key_here`
4. Railway will restart the service automatically

### 3. Verify E2B is Working
Run this in the agent:
```json
{
  "tool": "code_execution_tool",
  "runtime": "secure_info",
  "code": ""
}
```

Should return: `Execution environment: E2B Cloud Sandbox`

## Docker Hub Integration (Recommended)

### Benefits of Connecting Docker Hub
1. **Custom Images**: Deploy specialized tool containers
2. **Private Registry**: Keep proprietary tools secure
3. **Faster Deployments**: Utilize Docker layer caching
4. **Version Control**: Tag and manage image versions

### Setup Steps

#### Option 1: Railway Dashboard
1. Go to Railway project settings
2. Click "Integrations"
3. Select "Docker Hub"
4. Authorize with your Docker Hub account
5. Railway can now pull private images

#### Option 2: Environment Variables
Add these to your Railway service:
```
DOCKER_USERNAME=your_dockerhub_username
DOCKER_PASSWORD=your_dockerhub_password
DOCKER_REGISTRY=docker.io (optional, this is default)
```

### Using Custom Images

In `railway.toml`:
```toml
[build]
image = "yourdockerhub/custom-agent:latest"

[deploy]
startCommand = "python app.py"
```

Or for specific services:
```toml
[[services]]
name = "special-tool"
image = "yourdockerhub/special-tool:v1.0"
```

## E2B Sandbox Capabilities

### Available Runtimes
1. **Python 3.11+**
   - Pre-installed: numpy, pandas, requests, matplotlib
   - Can install more with pip

2. **Node.js 20+**
   - Pre-installed: common npm packages
   - Can install more with npm

3. **Bash/Terminal**
   - Full Linux environment
   - apt-get available for system packages

### Resource Limits
- CPU: 2 cores (configurable)
- Memory: 2GB (configurable)
- Execution time: 5 minutes default
- Network: Full internet access

### Security Features
- Complete isolation between sandboxes
- No access to Railway host system
- Automatic cleanup after execution
- Encrypted environment variables

## Best Practices

### 1. Code Execution Pattern
```python
# Always check environment first
import os
import json

# Verify E2B sandbox
sandbox_id = os.getenv('E2B_SANDBOX_ID', 'Not in E2B')
print(f"Running in sandbox: {sandbox_id}")

# Access Railway variables
railway_env = os.getenv('RAILWAY_ENVIRONMENT', 'local')
print(f"Railway environment: {railway_env}")

# Your code here
result = process_data()
print(json.dumps(result, indent=2))
```

### 2. Package Installation
```bash
# Python packages
pip install scikit-learn torch transformers

# Node packages
npm install axios cheerio puppeteer

# System packages
apt-get update && apt-get install -y imagemagick ffmpeg
```

### 3. File Handling
```python
# Files are temporary in sandbox
with open('/tmp/data.json', 'w') as f:
    json.dump(data, f)

# Read and process
with open('/tmp/data.json', 'r') as f:
    processed = json.load(f)

# IMPORTANT: Save output before sandbox closes
print(f"Results: {processed}")
```

## Troubleshooting

### E2B Not Working?
1. Check E2B_API_KEY is set correctly
2. Verify key starts with `e2b_`
3. Check E2B service status: https://status.e2b.dev
4. Falls back to Docker/local automatically

### Docker Hub Issues?
1. Verify credentials are correct
2. Check image name format: `user/image:tag`
3. Ensure image is public or credentials provided
4. Check Railway build logs for pull errors

### Common Errors

**"E2B API key not found"**
- Set E2B_API_KEY in Railway variables

**"Cannot pull Docker image"**
- Check Docker Hub credentials
- Verify image exists and is accessible

**"Sandbox timeout"**
- Break long tasks into smaller chunks
- Use session management for long processes

## Advanced Configuration

### Custom E2B Templates
Create specialized sandboxes:
```python
# In your code
os.environ['E2B_TEMPLATE'] = 'data-science'  # Uses GPU-enabled template
```

### Persistence Between Executions
Use Railway volumes for persistent storage:
```toml
[[volumes]]
mountPath = "/data"
```

Then in code:
```python
# Save to persistent volume
with open('/data/results.json', 'w') as f:
    json.dump(results, f)
```

Remember: E2B provides security, Docker Hub provides flexibility, and Railway provides the platform!