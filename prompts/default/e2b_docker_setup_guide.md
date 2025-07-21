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

## Docker Hub Access for Enhanced Sandboxes

### Why Give Gary-Zero Docker Hub Access?

Providing Docker Hub credentials allows Gary-Zero to:
1. **Pull specialized Docker images** for enhanced execution environments
2. **Access private images** with custom tools and libraries
3. **Use pre-configured environments** for specific tasks (ML, data science, etc.)
4. **Create more powerful sandboxes** beyond standard E2B environments

### Setting Up Docker Hub Access

Add these environment variables to your Railway service:

```bash
# Required for Docker Hub access
DOCKER_USERNAME=your_dockerhub_username
DOCKER_PASSWORD=your_dockerhub_password_or_token

# Optional - for private registries
DOCKER_REGISTRY=docker.io  # Default is Docker Hub
```

**Security Note**: Use a Docker Hub access token instead of your password:
1. Go to Docker Hub → Account Settings → Security
2. Create a new Access Token
3. Use this token as DOCKER_PASSWORD

### How Gary-Zero Uses Docker Hub

With Docker Hub access configured, Gary-Zero can:

1. **Pull and run specialized containers**:
```python
# Example: Using a data science image
import os
os.system("docker pull jupyter/datascience-notebook:latest")
# Gary-Zero can now create sandboxes with this image
```

2. **Access private tool images**:
```python
# If you have private images with custom tools
os.system("docker pull yourusername/custom-ml-tools:latest")
```

3. **Create enhanced E2B sandboxes**:
```python
# E2B can use custom Docker images as base
os.environ['E2B_DOCKER_IMAGE'] = 'tensorflow/tensorflow:latest-gpu'
```

### Use Cases for Docker Hub Integration

1. **Machine Learning Workloads**
   - Pull GPU-enabled TensorFlow/PyTorch images
   - Access pre-trained model containers
   - Use specialized ML tool images

2. **Data Science Tasks**
   - Jupyter notebook environments
   - R statistical computing images
   - Big data processing tools (Spark, etc.)

3. **Development Environments**
   - Language-specific images (Ruby, Go, Rust)
   - Database client tools
   - Testing frameworks

4. **Security Tools**
   - Penetration testing images
   - Security scanning tools
   - Network analysis containers

### Example: Enhanced Sandbox Usage

Once Docker Hub is configured, you can request specialized environments:

```json
{
  "thoughts": [
    "User needs GPU-accelerated ML environment",
    "I'll create a sandbox with TensorFlow GPU support"
  ],
  "tool": "code_execution_tool",
  "runtime": "python",
  "code": "# First ensure we have the right image\nimport subprocess\nsubprocess.run(['docker', 'pull', 'tensorflow/tensorflow:latest-gpu'])\n\n# Now run code in GPU-enabled environment\nimport tensorflow as tf\nprint(f'TensorFlow version: {tf.__version__}')\nprint(f'GPU available: {tf.config.list_physical_devices(\"GPU\")}')"
}
```

## E2B Sandbox Capabilities

### Standard Runtimes
1. **Python 3.11+**
   - Pre-installed: numpy, pandas, requests, matplotlib
   - Can install more with pip

2. **Node.js 20+**
   - Pre-installed: common npm packages
   - Can install more with npm

3. **Bash/Terminal**
   - Full Linux environment
   - apt-get available for system packages

### Enhanced with Docker Hub
- **Any Docker image** from Docker Hub
- **Custom environments** for specific tasks
- **Private images** with proprietary tools
- **Layered caching** for faster starts

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

### 1. Checking Available Resources
```python
# Check if Docker is available
import subprocess
try:
    result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
    print(f"Docker available: {result.stdout}")
except:
    print("Docker not available in this sandbox")
```

### 2. Using Custom Images
```python
# Pull a specific image for the task
import os

# For data science
os.system("docker pull jupyter/scipy-notebook:latest")

# For web scraping
os.system("docker pull scrapinghub/splash:latest")

# For API testing
os.system("docker pull postman/newman:latest")
```

### 3. Resource Management
```python
# Clean up unused images to save space
os.system("docker image prune -f")

# List available images
os.system("docker images")
```

## Troubleshooting

### Docker Hub Access Issues
1. **Authentication failed**
   - Verify DOCKER_USERNAME and DOCKER_PASSWORD
   - Use access token instead of password
   - Check for typos in credentials

2. **Rate limiting**
   - Docker Hub has pull rate limits
   - Authenticated users get higher limits
   - Consider Docker Hub subscription for more pulls

3. **Private image access**
   - Ensure credentials have access to the repository
   - Check image name format: `username/image:tag`

### Common Errors

**"unauthorized: authentication required"**
- Docker Hub credentials not set or incorrect
- Image is private and requires authentication

**"pull access denied"**
- No access to private repository
- Image name is incorrect

**"toomanyrequests: Rate limit exceeded"**
- Docker Hub rate limit hit
- Wait or upgrade Docker Hub account

## Advanced Configuration

### Using Docker Cloud
If you have Docker Cloud (enterprise):
```bash
DOCKER_REGISTRY=your-registry.docker.com
DOCKER_USERNAME=your-username
DOCKER_PASSWORD=your-token
```

### Custom Registry Support
For private registries:
```bash
DOCKER_REGISTRY=gcr.io  # Google Container Registry
DOCKER_REGISTRY=your-company.azurecr.io  # Azure
```

### Caching Strategy
Railway persists Docker layers between deployments, so frequently used images will be cached for faster access.

Remember: E2B provides security and isolation, Docker Hub provides specialized environments, and Railway provides the platform!