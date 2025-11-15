"""
Redis Client Manager with Connection Pooling
Provides singleton access to Redis client with retry logic
"""

import redis
from redis import Redis, ConnectionPool
from typing import Optional
from functools import wraps
import logging
import sys
import os

# Add parent directory to path to import redis_config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from redis_config import (
    REDIS_URL,
    ENABLE_CACHING,
    get_redis_connection_kwargs
)

logger = logging.getLogger(__name__)


class RedisClientManager:
    """
    Singleton Redis client manager with connection pooling
    """
    _instance: Optional['RedisClientManager'] = None
    _client: Optional[Redis] = None
    _pool: Optional[ConnectionPool] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None and ENABLE_CACHING:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize Redis client with connection pool"""
        try:
            kwargs = get_redis_connection_kwargs()

            # Create connection pool
            self._pool = ConnectionPool.from_url(
                REDIS_URL,
                **kwargs
            )

            # Create client from pool
            self._client = Redis(connection_pool=self._pool)

            # Test connection
            self._client.ping()
            logger.info(f"✅ Redis connected successfully to {REDIS_URL}")

        except redis.ConnectionError as e:
            logger.warning(f"⚠️  Redis connection failed: {str(e)}. Caching disabled.")
            self._client = None
            self._pool = None
        except Exception as e:
            logger.error(f"❌ Redis initialization error: {str(e)}")
            self._client = None
            self._pool = None

    def get_client(self) -> Optional[Redis]:
        """Get Redis client instance"""
        if not ENABLE_CACHING:
            return None

        if self._client is None:
            self._initialize_client()

        return self._client

    def is_available(self) -> bool:
        """Check if Redis is available"""
        if not ENABLE_CACHING or self._client is None:
            return False

        try:
            self._client.ping()
            return True
        except:
            return False

    def close(self):
        """Close Redis connection"""
        if self._client:
            self._client.close()
            self._client = None
        if self._pool:
            self._pool.disconnect()
            self._pool = None


# Singleton instance
_redis_manager = RedisClientManager()


def get_redis_client() -> Optional[Redis]:
    """
    Get Redis client instance (singleton)

    Returns:
        Redis client or None if Redis is unavailable
    """
    return _redis_manager.get_client()


def with_redis_retry(max_retries: int = 3, default_return=None):
    """
    Decorator to add retry logic to Redis operations

    Args:
        max_retries: Maximum number of retry attempts
        default_return: Value to return if all retries fail

    Example:
        @with_redis_retry(max_retries=3, default_return=[])
        def get_cached_results(key):
            client = get_redis_client()
            return client.get(key)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except redis.ConnectionError as e:
                    last_error = e
                    logger.warning(f"Redis connection error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        continue
                except redis.TimeoutError as e:
                    last_error = e
                    logger.warning(f"Redis timeout (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        continue
                except Exception as e:
                    # For other errors, don't retry
                    logger.error(f"Redis operation error: {str(e)}")
                    return default_return

            # All retries failed
            logger.error(f"All Redis retries failed: {str(last_error)}")
            return default_return

        return wrapper
    return decorator


def redis_health_check() -> dict:
    """
    Check Redis health and return status

    Returns:
        dict with health status information
    """
    status = {
        "available": False,
        "caching_enabled": ENABLE_CACHING,
        "url": REDIS_URL,
        "error": None
    }

    if not ENABLE_CACHING:
        status["error"] = "Caching disabled via configuration"
        return status

    client = get_redis_client()
    if client is None:
        status["error"] = "Redis client not initialized"
        return status

    try:
        client.ping()
        status["available"] = True
        status["info"] = {
            "used_memory": client.info("memory").get("used_memory_human"),
            "connected_clients": client.info("clients").get("connected_clients"),
            "uptime_in_days": client.info("server").get("uptime_in_days"),
        }
    except Exception as e:
        status["error"] = str(e)

    return status


if __name__ == "__main__":
    # Test Redis connection
    print("Testing Redis connection...")
    health = redis_health_check()

    if health["available"]:
        print("✅ Redis connection successful!")
        print(f"Info: {health.get('info')}")
    else:
        print(f"❌ Redis connection failed: {health.get('error')}")
