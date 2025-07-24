# Redis Service Specification

## Purpose & Capabilities
- **Session storage**: Fast session management and user state
- **Caching layer**: Improve performance with in-memory data storage
- **Rate limiting**: Control API usage and prevent abuse
- **Real-time features**: Support WebSocket connections and live updates
- **Queue management**: Background job processing with Redis queues

## Reference Variable Schemas
```toml
# Railway Environment Variables
REDIS_URL="redis://:${{REDIS_PASSWORD}}@redis.railway.internal:6379"
REDIS_PUBLIC_URL="redis://:${{REDIS_PASSWORD}}@${{REDIS_HOST}}:${{REDIS_PORT}}"
REDIS_HOST="${{REDIS_HOST}}"
REDIS_PORT="${{REDIS_PORT}}"
REDIS_PASSWORD="${{REDIS_PASSWORD}}"

# Connection settings
REDIS_POOL_SIZE="10"
REDIS_TIMEOUT="5"
REDIS_RETRY_ATTEMPTS="3"
```

## Connection Lifecycle & Error Handling Contracts
- **Connection Pooling**: Maintain persistent connection pool for efficiency
- **Automatic Reconnection**: Handle network interruptions gracefully
- **Failover Support**: Redis Sentinel or Cluster support for high availability
- **Circuit Breaker**: Prevent cascade failures when Redis is unavailable

## Sample SDK Snippets
### Python
```python
import redis
from redis.connection import ConnectionPool

# Redis client setup
redis_pool = ConnectionPool.from_url(
    os.getenv("REDIS_URL"),
    max_connections=10,
    socket_timeout=5,
    retry_on_timeout=True
)
redis_client = redis.Redis(connection_pool=redis_pool)

# Session storage
def store_session(session_id: str, data: dict, ttl: int = 3600):
    redis_client.setex(
        f"session:{session_id}", 
        ttl, 
        json.dumps(data)
    )

# Cache operations
def cache_get(key: str):
    value = redis_client.get(key)
    return json.loads(value) if value else None

def cache_set(key: str, value: any, ttl: int = 300):
    redis_client.setex(key, ttl, json.dumps(value))
```

### TypeScript
```typescript
import Redis from 'ioredis';

// Redis client configuration
const redis = new Redis(process.env.REDIS_URL!, {
  retryDelayOnFailover: 100,
  maxRetriesPerRequest: 3,
  lazyConnect: true,
});

// Session management
class SessionManager {
  async storeSession(sessionId: string, data: object, ttl = 3600): Promise<void> {
    await redis.setex(`session:${sessionId}`, ttl, JSON.stringify(data));
  }
  
  async getSession(sessionId: string): Promise<object | null> {
    const data = await redis.get(`session:${sessionId}`);
    return data ? JSON.parse(data) : null;
  }
  
  async deleteSession(sessionId: string): Promise<void> {
    await redis.del(`session:${sessionId}`);
  }
}

// Rate limiting
class RateLimiter {
  async checkLimit(key: string, limit: number, window: number): Promise<boolean> {
    const current = await redis.incr(key);
    if (current === 1) {
      await redis.expire(key, window);
    }
    return current <= limit;
  }
}
```

## Security Boundaries & Timeouts
- **Connection Security**: Password authentication and SSL/TLS support
- **Data Encryption**: Optional encryption for sensitive cached data  
- **Access Control**: Redis ACL for user-based permissions
- **Connection Timeouts**: 5-second default with configurable limits
- **Memory Limits**: Configurable max memory with eviction policies
- **Network Security**: Private network access within Railway infrastructure
- **TTL Management**: Automatic expiration for temporary data
