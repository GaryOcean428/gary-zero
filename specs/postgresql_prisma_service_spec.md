# PostgreSQL/Prisma Service Specification

## Purpose & Capabilities
- **Relational database**: Persistent data storage for Gary-Zero
- **User authentication**: Secure credential management and session handling
- **Configuration storage**: System settings and preferences
- **Audit logging**: Track user actions and system events
- **ORM integration**: Type-safe database operations via Prisma

## Reference Variable Schemas
```toml
# Railway Environment Variables
DATABASE_URL="postgresql://postgres:${{POSTGRES_PASSWORD}}@postgres.railway.internal:5432/railway"
DATABASE_PUBLIC_URL="postgresql://postgres:${{POSTGRES_PASSWORD}}@${{POSTGRES_HOST}}:${{POSTGRES_PORT}}/railway"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="${{POSTGRES_PASSWORD}}"  
POSTGRES_DB="railway"
POSTGRES_HOST="${{POSTGRES_HOST}}"
POSTGRES_PORT="${{POSTGRES_PORT}}"

# Connection pooling
DATABASE_POOL_SIZE="20"
DATABASE_TIMEOUT="30"
```

## Connection Lifecycle & Error Handling Contracts
- **Connection Pooling**: Efficient database connection management
- **Transaction Support**: ACID compliance for data integrity
- **Migration Management**: Schema versioning and updates via Prisma
- **Error Recovery**: Automatic reconnection and circuit breaker patterns

## Sample SDK Snippets
### Python
```python
import psycopg2
from psycopg2.extras import RealDictCursor

# Direct PostgreSQL connection
def get_db_connection():
    return psycopg2.connect(
        os.getenv("DATABASE_URL"),
        cursor_factory=RealDictCursor
    )

# Example query
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM auth_users WHERE username = %s", (username,))
    user = cursor.fetchone()
```

### TypeScript
```typescript
import { PrismaClient } from '@prisma/client';

// Prisma client setup
const prisma = new PrismaClient({
  datasources: {
    db: {
      url: process.env.DATABASE_URL
    }
  }
});

// Type-safe operations
const user = await prisma.user.findUnique({
  where: { username: 'gary' }
});

// Transaction example
await prisma.$transaction(async (tx) => {
  await tx.user.create({ data: userData });
  await tx.session.create({ data: sessionData });
});
```

## Security Boundaries & Timeouts
- **Connection Encryption**: SSL/TLS for data in transit
- **Password Hashing**: Secure credential storage using bcrypt/scrypt
- **SQL Injection Protection**: Parameterized queries and ORM safeguards
- **Connection Timeouts**: 30-second default with configurable limits
- **Access Control**: Row-level security and user permissions
- **Connection Pool Limits**: Maximum 20 concurrent connections (configurable)
- **Backup Strategy**: Automated backups via Railway's managed PostgreSQL
