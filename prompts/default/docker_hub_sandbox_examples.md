# Docker Hub Sandbox Usage Examples for Gary-Zero

Now that you've configured Docker Hub credentials in Railway, Gary-Zero can pull and use Docker images to enhance its execution capabilities. Here are practical examples of how to leverage this.

## Available Docker Hub Features

With Docker Hub credentials configured, Gary-Zero can:

1. **Pull public Docker images** for specialized environments
2. **Access your private Docker images** for proprietary tools
3. **Use official images** from verified publishers
4. **Create custom execution environments** on-demand

## Usage Examples

### 1. Data Science Environment

```python
# Gary-Zero can now pull and use specialized data science images
# Example: Using a Jupyter/scipy notebook image for analysis

{
  "tool": "code_execution_tool",
  "runtime": "docker",
  "docker_image": "jupyter/scipy-notebook:latest",
  "code": """
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# Now you have access to the full scipy stack!
data = pd.DataFrame(np.random.randn(100, 4), columns=['A', 'B', 'C', 'D'])
print(data.describe())
"""
}
```

### 2. Database Tools

```python
# Use official database client images
{
  "tool": "code_execution_tool", 
  "runtime": "docker",
  "docker_image": "postgres:16-alpine",
  "code": """
# PostgreSQL client tools are available
psql --version
# Can connect to databases, run migrations, etc.
"""
}
```

### 3. Custom Development Environments

```python
# Use language-specific environments
{
  "tool": "code_execution_tool",
  "runtime": "docker", 
  "docker_image": "rust:latest",
  "code": """
// Write and compile Rust code
fn main() {
    println!("Hello from Rust in Docker!");
}
"""
}
```

### 4. Private Image Access

```python
# Access your private images
{
  "tool": "code_execution_tool",
  "runtime": "docker",
  "docker_image": "yourdockerhub/private-ml-tools:v2.0",
  "code": """
# Your proprietary tools are now available
import company_ml_toolkit
model = company_ml_toolkit.load_model('production')
"""
}
```

## Best Practices

### 1. Image Selection
- Use official images when possible (verified publishers)
- Specify tags for reproducibility (`:latest` can change)
- Use Alpine variants for smaller footprint
- Cache commonly used images

### 2. Security Considerations
- Docker images run in E2B's secure sandbox
- Network access is controlled by E2B
- Credentials are never exposed to containers
- Images are pulled fresh (no local cache)

### 3. Performance Tips
- Smaller images pull faster
- Pre-built images are faster than building on-demand
- Consider creating custom images for repeated tasks
- Use multi-stage builds for optimization

## Common Use Cases

### Machine Learning Workflows
```python
# TensorFlow environment
{
  "tool": "code_execution_tool",
  "runtime": "docker",
  "docker_image": "tensorflow/tensorflow:latest-gpu",
  "code": "import tensorflow as tf; print(tf.__version__)"
}
```

### Web Scraping
```python
# Playwright/Puppeteer environment
{
  "tool": "code_execution_tool",
  "runtime": "docker",
  "docker_image": "mcr.microsoft.com/playwright:focal",
  "code": """
# Browser automation tools pre-installed
playwright install chromium
# Ready for web automation
"""
}
```

### API Development
```python
# Node.js API environment
{
  "tool": "code_execution_tool",
  "runtime": "docker",
  "docker_image": "node:20-alpine",
  "code": """
// Full Node.js environment
const express = require('express');
console.log('Express available:', !!express);
"""
}
```

## Integration with E2B

Docker images work alongside E2B:
1. E2B provides the secure sandbox
2. Docker provides the specialized environment
3. Railway provides the platform and credentials

The execution flow:
1. Gary-Zero receives execution request
2. E2B creates secure sandbox
3. Docker image is pulled using your credentials
4. Code runs in Docker container within E2B sandbox
5. Results returned to Gary-Zero

## Troubleshooting

### Image Pull Failures
- Verify Docker Hub credentials in Railway env
- Check image name spelling and tag
- Ensure image exists (public or in your account)
- Check Docker Hub rate limits

### Performance Issues
- Use smaller images (Alpine variants)
- Pre-pull common images
- Consider image layer caching
- Monitor pull times in logs

### Access Errors
- Verify DOCKER_USERNAME and DOCKER_PASSWORD
- Check private repository access
- Ensure credentials have pull permissions
- Test with public images first

## Next Steps

1. **Test Basic Access**: Try pulling a public image
2. **Create Custom Images**: Build specialized tools
3. **Optimize Workflows**: Identify common patterns
4. **Monitor Usage**: Track which images are most useful

With Docker Hub access, Gary-Zero now has virtually unlimited execution environments at its disposal!
