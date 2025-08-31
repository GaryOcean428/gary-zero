"""Service configuration for Railway connection management."""

import logging
import os
import re
import time
from functools import lru_cache
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def mask_sensitive_url(url: str) -> str:
    """Mask sensitive information in URLs for safe logging."""
    if not url:
        return url

    try:
        # Use regex to mask credentials in URLs
        # Matches patterns like: scheme://user:pass@host:port/path
        masked = re.sub(r"://([^:/@]+):[^@]+@", r"://\1:***@", url)
        return masked
    except Exception:
        # If masking fails, return a generic placeholder
        return "[URL_MASKED_FOR_SECURITY]"


def parse_redis_host(redis_url: str) -> str:
    """Parse Redis URL to extract host, handling credentials safely."""
    if not redis_url:
        return "redis-j-ux.railway.internal"

    try:
        parsed = urlparse(redis_url)
        if parsed.hostname:
            return parsed.hostname
        else:
            # Fallback to original parsing if urlparse fails
            fallback = (
                redis_url.replace("redis://", "")
                .replace("rediss://", "")
                .split("/")[0]
                .split("@")[-1]
            )
            # If the fallback doesn't look like a valid host, use default
            # Valid hosts typically have dots (FQDN), end with .internal, or are localhost
            if not fallback or (
                fallback not in ["localhost"]
                and not fallback.endswith(".internal")
                and "." not in fallback
            ):
                return "redis-j-ux.railway.internal"
            return fallback or "redis-j-ux.railway.internal"
    except Exception:
        return "redis-j-ux.railway.internal"


@lru_cache(maxsize=1)
def get_service_urls() -> dict[str, str]:
    """Get all Railway service URLs from environment."""
    redis_url = os.getenv("REDIS_URL", "")
    return {
        "redis": parse_redis_host(redis_url),
        "postgres": os.getenv("PGHOST", "postgres-jurp.railway.internal"),
        "searxng": os.getenv("SEARCHXNG_PRIVATE_DOMAIN", "searxng.railway.internal"),
        "kali": os.getenv("KALI_SHELL_HOST", "kali-linux-docker.railway.internal"),
    }


def get_redis_connection(retry_count: int = 5):
    """Get Redis connection with retry logic."""
    try:
        import redis
    except ImportError:
        logger.warning("Redis not installed, skipping Redis connection")
        return None

    urls = get_service_urls()
    redis_url = os.getenv("REDIS_URL")

    for attempt in range(retry_count):
        try:
            if redis_url:
                # Use full Redis URL if available
                client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
            else:
                # Fallback to host-based connection
                client = redis.Redis(
                    host=urls["redis"],
                    port=int(os.getenv("REDIS_PORT", 6379)),
                    password=os.getenv("REDIS_PASSWORD", ""),
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )

            client.ping()
            logger.info(f"Redis connection successful on attempt {attempt + 1}")
            return client

        except Exception:
            if attempt < retry_count - 1:
                wait_time = 2**attempt
                # Mask Redis URL for safe logging
                safe_url = (
                    mask_sensitive_url(redis_url)
                    if redis_url
                    else "host-based connection"
                )
                logger.warning(
                    f"Redis connection failed (attempt {attempt + 1}/{retry_count}) for {safe_url}. Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                safe_url = (
                    mask_sensitive_url(redis_url)
                    if redis_url
                    else "host-based connection"
                )
                logger.error(
                    f"Failed to connect to Redis after {retry_count} attempts for {safe_url}"
                )
                return None


def get_postgres_connection():
    """Get PostgreSQL connection."""
    try:
        import psycopg2
    except ImportError:
        logger.warning("psycopg2 not installed, skipping Postgres connection")
        return None

    try:
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return psycopg2.connect(database_url)
        else:
            return psycopg2.connect(
                host=os.getenv("PGHOST"),
                database=os.getenv("PGDATABASE"),
                user=os.getenv("PGUSER"),
                password=os.getenv("PGPASSWORD"),
                port=int(os.getenv("PGPORT", 5432)),
            )
    except Exception:
        # Mask database URL for safe logging
        safe_url = (
            mask_sensitive_url(database_url)
            if database_url
            else "host-based connection"
        )
        logger.error(f"Failed to connect to PostgreSQL using {safe_url}")
        return None


def validate_service_connections():
    """Validate all service connections."""
    logger.info("Validating service connections...")

    connections = {
        "redis": get_redis_connection() is not None,
        "postgres": get_postgres_connection() is not None,
    }

    for service, status in connections.items():
        if status:
            logger.info(f"✅ {service.capitalize()} connection: OK")
        else:
            logger.warning(f"⚠️ {service.capitalize()} connection: FAILED")

    return connections
