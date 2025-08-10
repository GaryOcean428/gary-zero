"""Service configuration for Railway connection management."""

import os
import time
import logging
from typing import Dict, Optional
from functools import lru_cache

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_service_urls() -> Dict[str, str]:
    """Get all Railway service URLs from environment."""
    return {
        'redis': os.getenv('REDIS_URL', '').replace('redis://', '').split('/')[0] or 'redis-j-ux.railway.internal',
        'postgres': os.getenv('PGHOST', 'postgres-jurp.railway.internal'),
        'searxng': os.getenv('SEARCHXNG_PRIVATE_DOMAIN', 'searxng.railway.internal'),
        'kali': os.getenv('KALI_SHELL_HOST', 'kali-linux-docker.railway.internal')
    }

def get_redis_connection(retry_count: int = 5):
    """Get Redis connection with retry logic."""
    try:
        import redis
    except ImportError:
        logger.warning("Redis not installed, skipping Redis connection")
        return None
    
    urls = get_service_urls()
    redis_url = os.getenv('REDIS_URL')
    
    for attempt in range(retry_count):
        try:
            if redis_url:
                # Use full Redis URL if available
                client = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=5, socket_timeout=5)
            else:
                # Fallback to host-based connection
                client = redis.Redis(
                    host=urls['redis'],
                    port=int(os.getenv('REDIS_PORT', 6379)),
                    password=os.getenv('REDIS_PASSWORD', ''),
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
            
            client.ping()
            logger.info(f"Redis connection successful on attempt {attempt + 1}")
            return client
            
        except Exception as e:
            if attempt < retry_count - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Redis connection failed (attempt {attempt + 1}/{retry_count}): {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to connect to Redis after {retry_count} attempts: {e}")
                return None

def get_postgres_connection():
    """Get PostgreSQL connection."""
    try:
        import psycopg2
    except ImportError:
        logger.warning("psycopg2 not installed, skipping Postgres connection")
        return None
    
    try:
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            return psycopg2.connect(database_url)
        else:
            return psycopg2.connect(
                host=os.getenv('PGHOST'),
                database=os.getenv('PGDATABASE'),
                user=os.getenv('PGUSER'),
                password=os.getenv('PGPASSWORD'),
                port=int(os.getenv('PGPORT', 5432))
            )
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        return None

def validate_service_connections():
    """Validate all service connections."""
    logger.info("Validating service connections...")
    
    connections = {
        'redis': get_redis_connection() is not None,
        'postgres': get_postgres_connection() is not None
    }
    
    for service, status in connections.items():
        if status:
            logger.info(f"✅ {service.capitalize()} connection: OK")
        else:
            logger.warning(f"⚠️ {service.capitalize()} connection: FAILED")
    
    return connections