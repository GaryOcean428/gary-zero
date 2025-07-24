# Morphism Browser Service Specification

## Purpose & Capabilities
- **Browser automation**: Headless Chrome/Chromium control
- **Web scraping**: Extract data from dynamic web pages
- **Form interaction**: Automated form filling and submission
- **JavaScript execution**: Run custom scripts in browser context
- **Screenshot generation**: Capture web page images

## Reference Variable Schemas
```toml
# Railway Environment Variables
MORPHISM_BROWSER_URL="https://${{morphism-browser.RAILWAY_PUBLIC_DOMAIN}}"
MORPHISM_API_KEY="your_morphism_api_key"  # If authentication required  # pragma: allowlist secret
MORPHISM_TIMEOUT="30"  # Default request timeout
MORPHISM_USER_AGENT="Gary-Zero-Agent/1.0"
```

## Connection Lifecycle & Error Handling Contracts
- **Browser Session Management**: Create, maintain, and clean up browser instances
- **Page Navigation**: Handle redirects, timeouts, and loading states
- **Element Interaction**: Wait for elements, handle dynamic content
- **Error Recovery**: Retry failed operations with exponential backoff

## Sample SDK Snippets
### Python
```python
import requests

# Browser automation via Morphism API
morphism_url = os.getenv("MORPHISM_BROWSER_URL")

# Navigate to page
response = requests.post(f"{morphism_url}/navigate", json={
    "url": "https://example.com",
    "wait_for": "networkidle"
})

# Take screenshot
screenshot = requests.post(f"{morphism_url}/screenshot", json={
    "format": "png",
    "full_page": True
})

# Execute JavaScript
js_result = requests.post(f"{morphism_url}/execute", json={
    "script": "document.title",
    "return_value": True
})
```

### TypeScript
```typescript
interface MorphismConfig {
  baseUrl: string;
  timeout: number;
  userAgent: string;
}

class MorphismClient {
  constructor(private config: MorphismConfig) {}

  async navigate(url: string): Promise<any> {
    const response = await fetch(`${this.config.baseUrl}/navigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, wait_for: 'networkidle' })
    });
    return response.json();
  }

  async screenshot(options = {}): Promise<Blob> {
    const response = await fetch(`${this.config.baseUrl}/screenshot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ format: 'png', ...options })
    });
    return response.blob();
  }
}
```

## Security Boundaries & Timeouts
- **Request Timeouts**: 30-second default with configurable overrides
- **URL Validation**: Restrict access to approved domains if needed
- **Resource Limits**: Control memory and CPU usage per browser session
- **Session Isolation**: Each automation task uses isolated browser context
- **HTTPS Enforcement**: Prefer secure connections for sensitive operations
- **Rate Limiting**: Respect target site rate limits and robots.txt
