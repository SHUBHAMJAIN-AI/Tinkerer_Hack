"""
Redis Configuration for Multi-Agent System
Manages connection settings, TTL values, and key patterns
"""

import os
from typing import Optional

# Redis Connection Settings
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Connection Pool Settings
REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
REDIS_SOCKET_TIMEOUT = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
REDIS_SOCKET_CONNECT_TIMEOUT = int(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "5"))

# Cache TTL Settings (in seconds)
CACHE_TTL_SEARCH = int(os.getenv("REDIS_TTL_SEARCH", "3600"))  # 1 hour
CACHE_TTL_CRAWL = int(os.getenv("REDIS_TTL_CRAWL", "21600"))  # 6 hours
CACHE_TTL_SESSIONS = int(os.getenv("REDIS_TTL_SESSIONS", "86400"))  # 24 hours
CACHE_TTL_USER_PREFS = int(os.getenv("REDIS_TTL_USER_PREFS", "604800"))  # 7 days
CACHE_TTL_LLM = int(os.getenv("REDIS_TTL_LLM", "3600"))  # 1 hour for LLM responses

# Redis Key Patterns
KEY_PATTERN_SESSION = "session:{session_id}"
KEY_PATTERN_SESSION_MESSAGES = "session:{session_id}:messages"
KEY_PATTERN_SESSION_STATE = "session:{session_id}:state"
KEY_PATTERN_SESSION_METADATA = "session:{session_id}:metadata"

KEY_PATTERN_SEARCH = "search:{query_hash}"
KEY_PATTERN_CRAWL = "crawl:{url_hash}"
KEY_PATTERN_USER_PREFS = "prefs:{session_id}"
KEY_PATTERN_VERIFIED = "verified:{session_id}:{result_id}"
KEY_PATTERN_RANKED = "ranked:{session_id}"

# Feature Flags
ENABLE_CACHING = os.getenv("ENABLE_CACHING", "true").lower() == "true"
ENABLE_SESSION_PERSISTENCE = os.getenv("ENABLE_SESSION_PERSISTENCE", "true").lower() == "true"
ENABLE_LLM_CACHE = os.getenv("ENABLE_LLM_CACHE", "true").lower() == "true"

# Result Limits
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "20"))
MAX_VERIFIED_RESULTS = int(os.getenv("MAX_VERIFIED_RESULTS", "15"))
MAX_RANKED_RESULTS = int(os.getenv("MAX_RANKED_RESULTS", "10"))

# Agent Configuration
AGENT_TYPE = os.getenv("AGENT_TYPE", "multi_agent")  # or "sample_agent"
ENABLE_VERIFICATION = os.getenv("ENABLE_VERIFICATION", "true").lower() == "true"
ENABLE_RERANKING = os.getenv("ENABLE_RERANKING", "true").lower() == "true"

# Verification Settings
VERIFICATION_STRICTNESS = os.getenv("VERIFICATION_STRICTNESS", "moderate")  # strict, moderate, lenient
VERIFICATION_TIMEOUT = int(os.getenv("VERIFICATION_TIMEOUT", "5"))  # seconds
MAX_VERIFICATION_RETRIES = int(os.getenv("MAX_VERIFICATION_RETRIES", "3"))

# Reranking Settings
RERANKING_STRATEGY = os.getenv("RERANKING_STRATEGY", "hybrid")  # llm, hybrid, algorithmic
RERANKING_MODEL = os.getenv("RERANKING_MODEL", "gpt-3.5-turbo")


def get_redis_connection_kwargs() -> dict:
    """Get Redis connection kwargs for redis.from_url()"""
    
    kwargs = {
        "decode_responses": True,
        "socket_timeout": REDIS_SOCKET_TIMEOUT,
        "socket_connect_timeout": REDIS_SOCKET_CONNECT_TIMEOUT,
        "max_connections": REDIS_MAX_CONNECTIONS,
        "retry_on_timeout": True,
        "health_check_interval": 30,
    }

    return kwargs


def format_key(pattern: str, **kwargs) -> str:
    """
    Format a Redis key pattern with given parameters

    Example:
        format_key(KEY_PATTERN_SESSION, session_id="abc123")
        # Returns: "session:abc123"
    """
    return pattern.format(**kwargs)
