"""
Cache Manager for Multi-Agent System
Handles caching of search results, crawl data, and sessions
"""

import json
import hashlib
from typing import Any, Optional, List, Dict
from datetime import datetime
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.redis_client import get_redis_client, with_redis_retry
from redis_config import (
    CACHE_TTL_SEARCH,
    CACHE_TTL_CRAWL,
    CACHE_TTL_SESSIONS,
    CACHE_TTL_USER_PREFS,
    format_key,
    KEY_PATTERN_SEARCH,
    KEY_PATTERN_CRAWL,
    KEY_PATTERN_SESSION_STATE,
    KEY_PATTERN_SESSION_MESSAGES,
    KEY_PATTERN_USER_PREFS,
    KEY_PATTERN_RANKED,
)

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages caching operations for the multi-agent system
    """

    @staticmethod
    def _generate_hash(data: str) -> str:
        """Generate SHA256 hash for cache keys"""
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    @staticmethod
    def _serialize(data: Any) -> str:
        """Serialize data to JSON string"""
        return json.dumps(data, default=str)

    @staticmethod
    def _deserialize(data: str) -> Any:
        """Deserialize JSON string to data"""
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    # ========== Search Results Caching ==========

    @staticmethod
    @with_redis_retry(max_retries=3, default_return=None)
    def cache_search_results(query: str, results: List[Dict[str, Any]], ttl: int = CACHE_TTL_SEARCH) -> bool:
        """
        Cache search results

        Args:
            query: Search query string
            results: Search results to cache
            ttl: Time to live in seconds

        Returns:
            True if cached successfully, False otherwise
        """
        client = get_redis_client()
        if not client:
            return False

        try:
            query_hash = CacheManager._generate_hash(query.lower().strip())
            key = format_key(KEY_PATTERN_SEARCH, query_hash=query_hash)

            cache_data = {
                "query": query,
                "results": results,
                "cached_at": datetime.utcnow().isoformat(),
                "result_count": len(results)
            }

            client.setex(key, ttl, CacheManager._serialize(cache_data))
            logger.info(f"✅ Cached search results for query: '{query}' (key: {key})")
            return True

        except Exception as e:
            logger.error(f"Error caching search results: {str(e)}")
            return False

    @staticmethod
    @with_redis_retry(max_retries=3, default_return=None)
    def get_cached_search(query: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached search results

        Args:
            query: Search query string

        Returns:
            Cached search results or None if not found
        """
        client = get_redis_client()
        if not client:
            return None

        try:
            query_hash = CacheManager._generate_hash(query.lower().strip())
            key = format_key(KEY_PATTERN_SEARCH, query_hash=query_hash)

            cached_data = client.get(key)
            if cached_data:
                data = CacheManager._deserialize(cached_data)
                if data and "results" in data:
                    logger.info(f"✅ Cache hit for query: '{query}' ({data.get('result_count', 0)} results)")
                    return data["results"]

            logger.info(f"❌ Cache miss for query: '{query}'")
            return None

        except Exception as e:
            logger.error(f"Error retrieving cached search: {str(e)}")
            return None

    # ========== Crawl Data Caching ==========

    @staticmethod
    @with_redis_retry(max_retries=3, default_return=False)
    def cache_crawl_data(url: str, crawl_data: Dict[str, Any], ttl: int = CACHE_TTL_CRAWL) -> bool:
        """
        Cache web crawl data

        Args:
            url: URL that was crawled
            crawl_data: Crawl results
            ttl: Time to live in seconds

        Returns:
            True if cached successfully
        """
        client = get_redis_client()
        if not client:
            return False

        try:
            url_hash = CacheManager._generate_hash(url)
            key = format_key(KEY_PATTERN_CRAWL, url_hash=url_hash)

            cache_data = {
                "url": url,
                "data": crawl_data,
                "cached_at": datetime.utcnow().isoformat()
            }

            client.setex(key, ttl, CacheManager._serialize(cache_data))
            logger.info(f"✅ Cached crawl data for URL: {url}")
            return True

        except Exception as e:
            logger.error(f"Error caching crawl data: {str(e)}")
            return False

    @staticmethod
    @with_redis_retry(max_retries=3, default_return=None)
    def get_cached_crawl(url: str) -> Optional[Dict[str, Any]]:
        """
        Get cached crawl data

        Args:
            url: URL to look up

        Returns:
            Cached crawl data or None
        """
        client = get_redis_client()
        if not client:
            return None

        try:
            url_hash = CacheManager._generate_hash(url)
            key = format_key(KEY_PATTERN_CRAWL, url_hash=url_hash)

            cached_data = client.get(key)
            if cached_data:
                data = CacheManager._deserialize(cached_data)
                if data and "data" in data:
                    logger.info(f"✅ Cache hit for crawl URL: {url}")
                    return data["data"]

            logger.info(f"❌ Cache miss for crawl URL: {url}")
            return None

        except Exception as e:
            logger.error(f"Error retrieving cached crawl: {str(e)}")
            return None

    # ========== Session State Management ==========

    @staticmethod
    @with_redis_retry(max_retries=3, default_return=False)
    def save_session_state(session_id: str, state: Dict[str, Any], ttl: int = CACHE_TTL_SESSIONS) -> bool:
        """
        Save session state to Redis

        Args:
            session_id: Session identifier
            state: Session state dictionary
            ttl: Time to live in seconds

        Returns:
            True if saved successfully
        """
        client = get_redis_client()
        if not client:
            return False

        try:
            key = format_key(KEY_PATTERN_SESSION_STATE, session_id=session_id)
            client.setex(key, ttl, CacheManager._serialize(state))
            logger.info(f"✅ Saved session state: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving session state: {str(e)}")
            return False

    @staticmethod
    @with_redis_retry(max_retries=3, default_return=None)
    def get_session_state(session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session state from Redis

        Args:
            session_id: Session identifier

        Returns:
            Session state or None
        """
        client = get_redis_client()
        if not client:
            return None

        try:
            key = format_key(KEY_PATTERN_SESSION_STATE, session_id=session_id)
            cached_data = client.get(key)

            if cached_data:
                state = CacheManager._deserialize(cached_data)
                logger.info(f"✅ Retrieved session state: {session_id}")
                return state

            return None

        except Exception as e:
            logger.error(f"Error retrieving session state: {str(e)}")
            return None

    # ========== User Preferences ==========

    @staticmethod
    @with_redis_retry(max_retries=3, default_return=False)
    def save_user_preferences(session_id: str, preferences: Dict[str, Any], ttl: int = CACHE_TTL_USER_PREFS) -> bool:
        """
        Save user preferences

        Args:
            session_id: Session identifier
            preferences: User preferences dictionary
            ttl: Time to live in seconds

        Returns:
            True if saved successfully
        """
        client = get_redis_client()
        if not client:
            return False

        try:
            key = format_key(KEY_PATTERN_USER_PREFS, session_id=session_id)
            client.setex(key, ttl, CacheManager._serialize(preferences))
            logger.info(f"✅ Saved user preferences for session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving user preferences: {str(e)}")
            return False

    @staticmethod
    @with_redis_retry(max_retries=3, default_return=None)
    def get_user_preferences(session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user preferences

        Args:
            session_id: Session identifier

        Returns:
            User preferences or None
        """
        client = get_redis_client()
        if not client:
            return None

        try:
            key = format_key(KEY_PATTERN_USER_PREFS, session_id=session_id)
            cached_data = client.get(key)

            if cached_data:
                prefs = CacheManager._deserialize(cached_data)
                logger.info(f"✅ Retrieved user preferences for session: {session_id}")
                return prefs

            return None

        except Exception as e:
            logger.error(f"Error retrieving user preferences: {str(e)}")
            return None

    # ========== Ranked Results ==========

    @staticmethod
    @with_redis_retry(max_retries=3, default_return=False)
    def save_ranked_results(session_id: str, results: List[Dict[str, Any]], ttl: int = CACHE_TTL_SESSIONS) -> bool:
        """
        Save ranked results for a session

        Args:
            session_id: Session identifier
            results: Ranked results list
            ttl: Time to live in seconds

        Returns:
            True if saved successfully
        """
        client = get_redis_client()
        if not client:
            return False

        try:
            key = format_key(KEY_PATTERN_RANKED, session_id=session_id)
            client.setex(key, ttl, CacheManager._serialize(results))
            logger.info(f"✅ Saved ranked results for session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving ranked results: {str(e)}")
            return False

    @staticmethod
    @with_redis_retry(max_retries=3, default_return=None)
    def get_ranked_results(session_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get ranked results for a session

        Args:
            session_id: Session identifier

        Returns:
            Ranked results or None
        """
        client = get_redis_client()
        if not client:
            return None

        try:
            key = format_key(KEY_PATTERN_RANKED, session_id=session_id)
            cached_data = client.get(key)

            if cached_data:
                results = CacheManager._deserialize(cached_data)
                logger.info(f"✅ Retrieved ranked results for session: {session_id}")
                return results

            return None

        except Exception as e:
            logger.error(f"Error retrieving ranked results: {str(e)}")
            return None

    # ========== Utility Methods ==========

    @staticmethod
    @with_redis_retry(max_retries=3, default_return=0)
    def clear_session(session_id: str) -> int:
        """
        Clear all session-related data

        Args:
            session_id: Session identifier

        Returns:
            Number of keys deleted
        """
        client = get_redis_client()
        if not client:
            return 0

        try:
            keys_to_delete = [
                format_key(KEY_PATTERN_SESSION_STATE, session_id=session_id),
                format_key(KEY_PATTERN_SESSION_MESSAGES, session_id=session_id),
                format_key(KEY_PATTERN_USER_PREFS, session_id=session_id),
                format_key(KEY_PATTERN_RANKED, session_id=session_id),
            ]

            deleted = client.delete(*keys_to_delete)
            logger.info(f"✅ Cleared {deleted} keys for session: {session_id}")
            return deleted

        except Exception as e:
            logger.error(f"Error clearing session: {str(e)}")
            return 0

    @staticmethod
    @with_redis_retry(max_retries=3, default_return={})
    def get_cache_stats() -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        client = get_redis_client()
        if not client:
            return {"error": "Redis not available"}

        try:
            info = client.info("stats")
            memory = client.info("memory")

            return {
                "total_keys": client.dbsize(),
                "used_memory": memory.get("used_memory_human"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": round(
                    info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100,
                    2
                )
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {"error": str(e)}
