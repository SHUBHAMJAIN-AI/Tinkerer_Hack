"""
LangChain LLM Cache Integration with Redis
Caches LLM responses to reduce API costs and improve response times
"""

import logging
from typing import Optional
from langchain_core.globals import set_llm_cache, get_llm_cache
from langchain_community.cache import RedisCache
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redis_config import REDIS_URL, ENABLE_LLM_CACHE, CACHE_TTL_LLM
from utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)


def initialize_llm_cache() -> bool:
    """
    Initialize LangChain LLM cache with Redis

    This will cache all LLM responses automatically, reducing costs
    and improving response times for repeated queries.

    Returns:
        True if cache initialized successfully, False otherwise
    """
    if not ENABLE_LLM_CACHE:
        logger.info("LLM caching is disabled via configuration")
        return False

    try:
        # Check if Redis is available
        client = get_redis_client()
        if not client:
            logger.warning("Redis client not available, LLM caching disabled")
            return False

        # Initialize Redis cache for LangChain
        redis_cache = RedisCache(
            redis_url=REDIS_URL,
            ttl=CACHE_TTL_LLM
        )

        # Set global LLM cache
        set_llm_cache(redis_cache)

        logger.info(f"✅ LangChain LLM cache initialized with Redis (TTL: {CACHE_TTL_LLM}s)")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to initialize LLM cache: {str(e)}")
        return False


def clear_llm_cache() -> bool:
    """
    Clear the LLM cache

    Returns:
        True if cleared successfully
    """
    try:
        cache = get_llm_cache()
        if cache and hasattr(cache, 'clear'):
            cache.clear()
            logger.info("✅ LLM cache cleared")
            return True
        return False
    except Exception as e:
        logger.error(f"Error clearing LLM cache: {str(e)}")
        return False


def get_llm_cache_stats() -> dict:
    """
    Get LLM cache statistics

    Returns:
        Dictionary with cache statistics
    """
    try:
        cache = get_llm_cache()
        if cache:
            return {
                "enabled": True,
                "type": type(cache).__name__,
                "ttl": CACHE_TTL_LLM
            }
        return {"enabled": False}
    except Exception as e:
        logger.error(f"Error getting LLM cache stats: {str(e)}")
        return {"enabled": False, "error": str(e)}


# Auto-initialize on module import if enabled
if ENABLE_LLM_CACHE:
    initialize_llm_cache()
