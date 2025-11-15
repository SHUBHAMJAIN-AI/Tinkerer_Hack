# ==================================================
# API KEYS
# ==================================================

# OpenAI API Key for LLM
OPENAI_API_KEY=
# Tavily API Key for web research
TAVILY_API_KEY=
# Disable LangSmith tracing
LANGCHAIN_TRACING_V2=false

# ==================================================
# REDIS CONFIGURATION
# ==================================================

# Redis Connection URL
# Local: redis://localhost:6379
# Redis Cloud: rediss://default:password@host:port
REDIS_URL=redis://localhost:6379

# Redis Password (for Redis Cloud - not needed for local)
REDIS_PASSWORD=

# Redis Database Number
REDIS_DB=0

# Redis Connection Settings
REDIS_MAX_CONNECTIONS=10
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5

# ==================================================
# CACHE TTL SETTINGS (in seconds)
# ==================================================

# Search results cache TTL (1 hour)
REDIS_TTL_SEARCH=3600

# Web crawl data cache TTL (6 hours)
REDIS_TTL_CRAWL=21600

# Session data TTL (24 hours)
REDIS_TTL_SESSIONS=86400

# User preferences TTL (7 days)
REDIS_TTL_USER_PREFS=604800

# LLM response cache TTL (1 hour)
REDIS_TTL_LLM=3600

# ==================================================
# FEATURE FLAGS
# ==================================================

# Enable/disable caching
ENABLE_CACHING=true

# Enable session persistence
ENABLE_SESSION_PERSISTENCE=true

# Enable LLM response caching
ENABLE_LLM_CACHE=true

# Enable verification agent
ENABLE_VERIFICATION=true

# Enable reranking agent
ENABLE_RERANKING=true

# ==================================================
# AGENT CONFIGURATION
# ==================================================

# Agent type: "sample_agent" or "multi_agent"
AGENT_TYPE=multi_agent

# Maximum number of search results from Tavily
MAX_SEARCH_RESULTS=20

# Maximum number of results after verification
MAX_VERIFIED_RESULTS=15

# Maximum number of results after reranking (shown to user)
MAX_RANKED_RESULTS=10

# ==================================================
# VERIFICATION SETTINGS
# ==================================================

# Verification strictness: "strict", "moderate", or "lenient"
VERIFICATION_STRICTNESS=lenient

# Verification timeout in seconds
VERIFICATION_TIMEOUT=5

# Maximum verification retries
MAX_VERIFICATION_RETRIES=3

# ==================================================
# RERANKING SETTINGS
# ==================================================

# Reranking strategy: "llm", "hybrid", or "algorithmic"
RERANKING_STRATEGY=hybrid

# Model for reranking (when using llm or hybrid)
RERANKING_MODEL=gpt-3.5-turbo
