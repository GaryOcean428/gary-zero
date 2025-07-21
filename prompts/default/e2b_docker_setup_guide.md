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

## Docker Hub Access for Enhanced Sandbox Capabilities

### Purpose
Giving Gary-Zero access to Docker Hub allows the agent to:
1. **Pull Specialized Images**: Access pre-built tool containers during execution
2. **Use Custom Environments**: Run code in specialized Docker images
3. **Access Private Images**: Use your proprietary or custom tools
4. **Enhance Execution**: Go beyond standard E2B capabilities

### Setup Docker Hub Credentials

Add these environment variables to your Railway service:
```
DOCKER_USERNAME=your_dockerhub_username
DOCKER_PASSWORD=your_dockerhub_password
DOCKER_REGISTRY=docker.io (optional, defaults to Docker Hub)
```

**Note**: This is NOT for deploying Gary-Zero itself. This gives the deployed Gary-Zero service the ability to pull and use Docker images to enhance its code execution capabilities.

### How Gary-Zero Uses Docker Hub

With Docker Hub access, Gary-Zero can:

1. **Pull and Run Specialized Containers**
   ```python
   # Gary-Zero can now execute code like this internally:
   import docker
   client = docker.from_env()
   
   # Pull a specialized data science image
   client.images.pull('jupyter/datascience-notebook:latest')
   
   # Run code in that container
   container = client.containers.run(
       'jupyter/datascience-notebook:latest',
       'python -c "import tensorflow as tf; print(tf.__version__)"',
       remove=True
   )
   ```

2. **Access Tool-Specific Images**
   - Machine Learning: `tensorflow/tensorflow`, `pytorch/pytorch`
   - Data Science: `jupyter/datascience-notebook`
   - Web Scraping: `scrapinghub/splash`
   - Database Tools: `postgres`, `mysql`, `mongodb`
   - Custom Tools: Your private images

3. **Enhanced Code Execution**
   When E2B doesn't have the right environment, Gary-Zero can:
   - Pull a Docker image with required tools
   - Execute code in that specialized environment
   - Return results to the user

### Security Considerations

1. **Credentials are Encrypted**: Railway encrypts environment variables
2. **Sandboxed Execution**: Docker containers provide isolation
3. **Resource Limits**: Gary-Zero respects Railway's resource constraints
4. **Image Verification**: Only pulls from trusted sources

## E2B + Docker Hub Synergy

### Primary Execution Path
1. **E2B First**: Fast, secure, pre-configured sandboxes
2. **Docker Fallback**: When specialized tools are needed
3. **Local Last Resort**: Only if both are unavailable

### Use Cases

**E2B is Best For:**
- Quick Python/Node.js execution
- Standard data processing
- Web requests and API calls
- General purpose computing

**Docker Hub Extends With:**
- Specialized ML frameworks
- Database-specific tools
- Legacy software environments
- Custom proprietary tools

### Example Workflow

User asks Gary-Zero to: "Analyze this image using specialized computer vision tools"

1. Gary-Zero checks if E2B has required libraries
2. If not, pulls `opencv/opencv-python` from Docker Hub
3. Runs analysis in the Docker container
4. Returns results to user

## Best Practices

### 1. Image Selection
Gary-Zero will intelligently select images based on task:
```python
task_images = {
    "machine_learning": "tensorflow/tensorflow:latest-gpu",
    "data_science": "jupyter/datascience-notebook",
    "web_scraping": "scrapinghub/splash",
    "nlp": "huggingface/transformers-pytorch-cpu"
}
```

### 2. Private Images
For proprietary tools, use private Docker Hub repos:
```
your-company/private-ml-tools:v2.0
your-username/custom-agent-tools:latest
```

### 3. Resource Management
Gary-Zero automatically:
- Cleans up containers after use
- Manages image cache
- Respects memory limits
- Handles timeouts gracefully

## Troubleshooting

### Docker Hub Access Issues

**"Cannot pull image"**
- Verify DOCKER_USERNAME and DOCKER_PASSWORD are set
- Check if image name is correct
- Ensure image exists and you have access

**"Rate limit exceeded"**
- Docker Hub has pull limits
- Consider Docker Hub Pro for higher limits
- Use image caching strategies

**"Out of memory"**
- Some images are large
- Railway has memory limits
- Use lighter alternatives when possible

### Testing Docker Access

Ask Gary-Zero to verify Docker access:
```
"Check if you can access Docker Hub and list available images"
```

Gary-Zero will:
1. Test authentication
2. List accessible images
3. Report any issues

## Advanced Configuration

### Custom Registry
Use private registries beyond Docker Hub:
```
DOCKER_REGISTRY=your-registry.com
DOCKER_USERNAME=your-username
DOCKER_PASSWORD=your-token
```

### Image Caching
Gary-Zero caches frequently used images:
- Faster subsequent executions
- Reduced bandwidth usage
- Automatic cleanup of old images

### Multi-Stage Execution
Gary-Zero can chain containers:
1. Data prep in one container
2. Analysis in another
3. Visualization in a third

## Summary

With Docker Hub access, Gary-Zero becomes significantly more powerful:
- ✅ Access to thousands of specialized tools
- ✅ Custom execution environments
- ✅ Private tool integration
- ✅ Enhanced capabilities beyond E2B

Remember: 
- E2B for speed and security
- Docker for specialization and flexibility
- This is about giving Gary-Zero access to Docker images, not deploying Gary-Zero from Docker!