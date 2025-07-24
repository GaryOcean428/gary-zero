# Railway Volume Setup and Migration Guide


## Overview

Gary-Zero now supports persistent data storage using Railway volumes to prevent data loss during deployments. This setup includes:

- **SearXNG as primary search** with DuckDuckGo fallback
- **Persistent volume storage** for agent memory, logs, knowledge base, and work files
- **Automatic migration** from existing installations


## Search Engine Configuration

### Primary: SearXNG (Railway Service)

- Uses Railway's internal service communication
- Configured via `SEARXNG_URL` environment variable
- Format: `http://${{searchxng.RAILWAY_PRIVATE_DOMAIN}}:${{searchxng.PORT}}`

### Fallback: DuckDuckGo

- Activates automatically if SearXNG fails
- No configuration required
- Works in any network environment


## Volume Configuration

### Railway Setup

1. **Create Volume** (via Railway Dashboard or CLI):

   ```bash
   railway volumes create gary-zero-data --size 10
   ```

2. **Deploy with Volume**: The `railway.toml` is already configured with:

   ```toml
   [[volumes]]
   name = "gary-zero-data"
   mountPath = "/app/data"
   size = 10
   ```

### Directory Structure

```
/app/data/
├── memory/        # Agent persistent memory
├── logs/          # Chat logs and session history
├── knowledge/     # Knowledge base and RAG data
├── work_dir/      # Agent working directory
├── reports/       # Generated analysis reports
├── scheduler/     # Task scheduling data
└── tmp/           # Temporary files
```


## Environment Variables

### Required for Railway Deployment

```bash
# SearXNG service URL (set automatically by Railway)
SEARXNG_URL=http://${{searchxng.RAILWAY_PRIVATE_DOMAIN}}:${{searchxng.PORT}}

# Data directory for persistent storage
DATA_DIR=/app/data

# Search provider configuration
SEARCH_PROVIDER=searxng
```

### Local Development

```bash
# For local development without Railway SearXNG service
SEARXNG_URL=http://localhost:55510
DATA_DIR=/app/data
```


## Migration Process

### New Installations

No action required - volume structure is created automatically on first deployment.

### Existing Installations

1. **Automatic Migration**: Run the migration script during deployment:

   ```bash
   python scripts/migrate_to_volumes.py
   ```

2. **Manual Migration**: If needed:

   ```bash
   # Backup existing data
   tar -czf gary-zero-backup.tar.gz memory logs knowledge work_dir reports

   # Run migration
   python scripts/migrate_to_volumes.py

   # Verify migration
   python scripts/migrate_to_volumes.py verify
   ```

3. **Rollback** (if needed):

   ```bash
   python scripts/migrate_to_volumes.py rollback
   ```


## Volume Initialization

### Automatic Initialization

The volume structure is created automatically via:

```bash
python scripts/init_volumes.py
```

This script:
- Creates all required directories
- Sets up symlinks from `/app/[dir]` to `/app/data/[dir]`
- Initializes empty scheduler tasks file
- Handles existing data migration

### Manual Initialization

For custom setups or troubleshooting:

```bash
# Set custom data directory
DATA_DIR=/custom/path python scripts/init_volumes.py

# Initialize without symlinks (for testing)
python -c "from scripts.init_volumes import initialize_volume_structure; initialize_volume_structure()"
```


## Verification Commands

### Check Volume Status

```bash
# Verify volume mount
railway logs --tail | grep "Volume structure"

# Check directory structure
ls -la /app/data/

# Verify symlinks
ls -la /app/ | grep -E "(memory|logs|knowledge|work_dir|reports)"
```

### Test Search Functionality

```bash
# Test SearXNG connectivity
curl -I "$SEARXNG_URL/search?q=test"

# Test search engine in application
railway run python -c "
from framework.tools.search_engine import SearchEngine
import asyncio
tool = SearchEngine()
result = asyncio.run(tool.execute(query='test'))
print('Search test:', 'PASS' if result else 'FAIL')
"
```


## Troubleshooting

### SearXNG Connection Issues

1. **Check service status**: Verify SearXNG service is running in Railway
2. **Environment variables**: Ensure `SEARXNG_URL` is correctly set
3. **Fallback verification**: DuckDuckGo should activate automatically

### Volume Issues

1. **Mount verification**: Check if `/app/data` exists and is writable
2. **Symlink issues**: Run `python scripts/init_volumes.py` to recreate
3. **Migration problems**: Use rollback and retry migration

### Search Failures

1. **SearXNG + DuckDuckGo both fail**: Check network connectivity
2. **Rate limiting**: DuckDuckGo may rate-limit requests - this is normal
3. **Empty results**: Verify search query format and provider status


## Benefits

### Persistence

- ✅ Agent memory survives deployments
- ✅ Chat history preserved across restarts
- ✅ Knowledge base accumulates over time
- ✅ Work files and reports retained

### Reliability

- ✅ Dual search providers (SearXNG + DuckDuckGo)
- ✅ Automatic fallback on failure
- ✅ Graceful error handling
- ✅ Zero configuration required

### Scalability

- ✅ Railway volume auto-scaling
- ✅ Internal service communication
- ✅ No external API dependencies
- ✅ Container-optimized storage


## File Structure Changes

### Modified Files

- `framework/tools/search_engine.py` - Dual search provider support
- `framework/helpers/searxng.py` - Railway service integration
- `framework/helpers/duckduckgo_search.py` - Async compatibility
- `railway.toml` - Volume and service configuration
- `Dockerfile` - Volume mount point creation
- `.env.example` - New environment variables

### New Files

- `scripts/init_volumes.py` - Volume initialization
- `scripts/migrate_to_volumes.py` - Data migration utility
- `VOLUME_SETUP.md` - This documentation

The setup ensures Gary-Zero maintains full functionality while gaining persistent storage and reliable search capabilities in Railway's containerized environment.
