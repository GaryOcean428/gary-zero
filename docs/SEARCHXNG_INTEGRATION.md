# SearchXNG Integration Guide

This guide helps you set up and troubleshoot SearchXNG integration with Gary-Zero on Railway.


## Quick Setup

### 1. Deploy SearchXNG Service on Railway

1. In your Railway project, deploy a SearchXNG service
2. Use the official SearchXNG Docker image or template
3. Note the service name (must be `searchxng` for automatic linking)

### 2. Configure SearchXNG Service

Add these environment variables to your SearchXNG service:

```bash
PORT=8080  # Required for Railway reference variables to work
```

### 3. Configure Gary-Zero Service

The following should be automatically set via railway.toml, but verify:

```bash
SEARXNG_URL=http://${{searchxng.RAILWAY_PRIVATE_DOMAIN}}:${{searchxng.PORT}}
SEARCH_PROVIDER=searxng
```


## Troubleshooting

### Check SearchXNG Connectivity

Run the test script:

```bash
python scripts/test_searchxng.py
```

### Validate All Integrations

```bash
python scripts/validate_integrations.py
```

### Use Diagnostics Endpoint

After deployment, visit:

```
https://your-gary-zero-url/diagnostics
```

### Common Issues

#### 1. Unresolved Reference Variables

**Error:** `SEARXNG_URL contains unresolved reference variables: http://${{searchxng...}}`

**Fix:** Add `PORT=8080` to your SearchXNG service environment variables

#### 2. Connection Failed

**Error:** `SearchXNG connection failed`

**Fixes:**
- Ensure SearchXNG service is running
- Check service name is exactly `searchxng`
- Both services must be in same Railway environment
- Try manual URL: `SEARXNG_URL=http://searchxng.railway.internal:8080`

#### 3. 405 Method Not Allowed

**Error:** Health check errors in logs

**Fix:** Already fixed in latest code - pull latest changes


## Manual Configuration

If automatic configuration fails, set these manually in Gary-Zero:

```bash
# Option 1: Direct internal URL
SEARXNG_URL=http://searchxng.railway.internal:8080

# Option 2: Use public URL (less efficient, costs egress)
SEARXNG_URL=https://searchxng-production-xxxx.up.railway.app
```


## Fallback Behavior

If SearchXNG is unavailable, Gary-Zero will:
1. Try `http://searchxng.railway.internal:8080` on Railway
2. Fall back to `http://localhost:55510` for local development
3. You can switch to DuckDuckGo: `SEARCH_PROVIDER=duckduckgo`


## Railway Service Communication

Gary-Zero uses Railway's private networking:
- Internal domain: `*.railway.internal`
- No egress fees for internal communication
- IPv6 support enabled by default
- Uses HTTP (not HTTPS) for internal communication


## Verification Steps

1. **Check Environment Variables:**

   ```bash
   # In Railway dashboard, verify these are set:
   SEARXNG_URL  # Should not contain ${{ }}
   SEARCH_PROVIDER=searxng
   ```

2. **Test from Gary-Zero:**
   Use the chat interface to search:

   ```
   Search for "Railway deployment best practices"
   ```

3. **Check Logs:**
   Look for SearchXNG URL being used:

   ```
   🔍 SearchXNG URL: http://searchxng.railway.internal:8080
   ```


## Support

If issues persist:
1. Check Railway service logs for both services
2. Ensure both services are in the same Railway project
3. Verify private networking is enabled (default)
4. Use diagnostics endpoint for detailed status
