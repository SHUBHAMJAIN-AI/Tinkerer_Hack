# 🚀 Multi-Agent DealFinder Setup Guide

Complete guide for setting up and running the advanced multi-agent DealFinder AI system with Redis caching, verification, and intelligent reranking.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Redis Setup](#redis-setup)
4. [Configuration](#configuration)
5. [Architecture Overview](#architecture-overview)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### Required
- **Node.js** 18+ ([Download](https://nodejs.org/))
- **Python** 3.12+ ([Download](https://www.python.org/))
- **OpenAI API Key** ([Get it here](https://platform.openai.com/api-keys))

### Optional but Recommended
- **Tavily API Key** ([Sign up](https://app.tavily.com/)) - For web research features
- **Redis Cloud Account** ([Free tier](https://redis.com/try-free/)) - For caching and sessions
- **LangSmith API Key** ([Get it](https://smith.langchain.com/)) - For debugging

---

## ⚡ Quick Start

### 1. Install Dependencies

```bash
# Install Node.js dependencies (this also installs Python dependencies via postinstall)
npm install

# Verify Python dependencies were installed
cd agent && python -c "import redis; print('Redis:', redis.__version__)" && cd ..
```

###  2. Configure Environment Variables

```bash
# Copy the template
cp agent/.env agent/.env.backup  # Backup existing if you have one

# Edit agent/.env with your API keys
# See "Configuration" section below for details
```

**Minimum required in `agent/.env`:**
```bash
OPENAI_API_KEY=your-openai-api-key-here
AGENT_TYPE=multi_agent
```

### 3. Start the Application

```bash
# Start both UI and multi-agent system
npm run dev
```

**The app will be available at:**
- UI: http://localhost:3000
- Agent API: http://localhost:8123
- Agent Docs: http://localhost:8123/docs

---

## 🔴 Redis Setup

### Option A: Redis Cloud (Recommended for Production)

1. **Sign up** at [Redis Cloud](https://redis.com/try-free/)
2. **Create a free database**:
   - Select cloud provider (AWS/GCP/Azure)
   - Choose region closest to you
   - Free tier: 30MB storage
3. **Get connection details**:
   - Go to "Databases" → Your database
   - Copy the "Public endpoint" (format: `redis-xxxxx.redislabs.com:port`)
   - Copy the "Default user password"

4. **Update `agent/.env`**:
```bash
REDIS_URL=rediss://default:YOUR_PASSWORD@redis-xxxxx.redislabs.com:12345
REDIS_PASSWORD=your-password-here
ENABLE_CACHING=true
ENABLE_LLM_CACHE=true
```

### Option B: Local Redis (For Development)

#### macOS (using Homebrew)
```bash
brew install redis
brew services start redis

# Verify it's running
redis-cli ping
# Should return: PONG
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify
redis-cli ping
```

#### Windows (using WSL or Docker)
```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Verify
docker ps  # Should see redis container
```

**Update `agent/.env` for local Redis:**
```bash
REDIS_URL=redis://localhost:6379
ENABLE_CACHING=true
ENABLE_LLM_CACHE=true
```

### Verify Redis Connection

```bash
cd agent
python -c "from utils.redis_client import redis_health_check; import json; print(json.dumps(redis_health_check(), indent=2))"
```

**Expected output:**
```json
{
  "available": true,
  "caching_enabled": true,
  "url": "redis://localhost:6379",
  "info": {
    "used_memory": "1.2M",
    "connected_clients": 1,
    "uptime_in_days": 0
  }
}
```

---

## ⚙️ Configuration

### Environment Variables Reference

**File**: `agent/.env`

```bash
# ============================================
# REQUIRED
# ============================================

# OpenAI API Key (REQUIRED)
OPENAI_API_KEY=sk-proj-...

# ============================================
# AGENT SELECTION
# ============================================

# Which agent graph to use (multi_agent or sample_agent)
AGENT_TYPE=multi_agent

# ============================================
# REDIS CONFIGURATION
# ============================================

# Redis connection URL
# Local: redis://localhost:6379
# Cloud: rediss://default:password@host:port
REDIS_URL=redis://localhost:6379

# Redis password (if using Redis Cloud)
REDIS_PASSWORD=

# ============================================
# OPTIONAL ENHANCEMENTS
# ============================================

# Tavily API Key (for web search/crawl)
TAVILY_API_KEY=tvly-...

# LangSmith API Key (for debugging)
LANGSMITH_API_KEY=lsv2_pt_...

# ============================================
# FEATURE FLAGS
# ============================================

# Enable Redis caching
ENABLE_CACHING=true

# Enable LLM response caching
ENABLE_LLM_CACHE=true

# Enable verification agent
ENABLE_VERIFICATION=true

# Enable reranking agent
ENABLE_RERANKING=true

# ============================================
# AGENT BEHAVIOR
# ============================================

# Verification strictness (strict, moderate, lenient)
VERIFICATION_STRICTNESS=moderate

# Reranking strategy (llm, hybrid, algorithmic)
RERANKING_STRATEGY=hybrid

# Reranking model
RERANKING_MODEL=gpt-3.5-turbo

# ============================================
# RESULT LIMITS
# ============================================

# Maximum raw search results from Tavily
MAX_SEARCH_RESULTS=20

# Maximum results after verification
MAX_VERIFIED_RESULTS=15

# Maximum results shown to user (after reranking)
MAX_RANKED_RESULTS=10

# ============================================
# CACHE TTL SETTINGS (seconds)
# ============================================

# Search results cache (1 hour)
REDIS_TTL_SEARCH=3600

# Web crawl data cache (6 hours)
REDIS_TTL_CRAWL=21600

# Session data cache (24 hours)
REDIS_TTL_SESSIONS=86400

# User preferences cache (7 days)
REDIS_TTL_USER_PREFS=604800

# LLM response cache (1 hour)
REDIS_TTL_LLM=3600
```

### Frontend Configuration

**File**: `.env.local` (create in project root if using multi_agent)

```bash
# Match the agent type from backend
NEXT_PUBLIC_AGENT_TYPE=multi_agent
```

---

## 🏗️ Architecture Overview

### Multi-Agent Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    USER QUERY                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
              ┌─────────────┐
              │  chat_node  │ ◄─── Entry Point (GPT-4o)
              └──────┬──────┘
                     │
                     ▼
              ┌─────────────┐
              │  tool_node  │ ◄─── Execute Tavily search tools
              └──────┬──────┘
                     │
                     ▼
         ┌──────────────────────┐
         │   search_agent       │ ◄─── Redis cache check
         │   - Cache lookup     │      Cache hit → skip to verify
         │   - Store raw results│      Cache miss → use tool results
         └──────┬───────────────┘
                │
                ▼
         ┌──────────────────────┐
         │ verification_agent   │ ◄─── Quality filtering
         │   - URL validation   │      - Parallel HEAD requests
         │   - Data completeness│      - Relevance scoring
         │   - Quality scoring  │      - Configurable strictness
         └──────┬───────────────┘
                │
                ▼
         ┌──────────────────────┐
         │  reranking_agent     │ ◄─── Hybrid AI ranking
         │   - Algorithmic score│      - Price/discount/rating
         │   - GPT-3.5 semantic │      - LLM semantic boost
         │   - Combined ranking │      - Final top N selection
         └──────┬───────────────┘
                │
                ▼
         ┌──────────────────────┐
         │  synthesis_agent     │ ◄─── Answer generation
         │   - GPT-4o synthesis │      - Comprehensive summary
         │   - Frontend actions │      - UI updates (CopilotKit)
         │   - Price comparisons│      - Deal cards
         └──────┬───────────────┘
                │
                ▼
         ┌─────────────────────┐
         │    FINAL ANSWER     │
         │   + Ranked Deals    │
         └─────────────────────┘
```

### Key Components

**Agent Nodes** (`agent/nodes/`):
- `search_agent.py` - Tavily integration + Redis caching
- `verification_agent.py` - Quality validation + filtering
- `reranking_agent.py` - Hybrid ranking (algo + LLM)
- `synthesis_agent.py` - Answer generation + UI updates

**Utilities** (`agent/utils/`):
- `redis_client.py` - Connection pooling + health checks
- `cache.py` - Caching operations with TTL
- `state.py` - Enhanced AgentState schema
- `llm_cache.py` - LangChain LLM cache integration

**Configuration**:
- `redis_config.py` - All Redis and agent settings
- `agent_multi.py` - Multi-agent graph orchestration
- `langgraph.json` - Graph deployment config

---

## 🧪 Testing

### 1. Test Redis Connection

```bash
cd agent
python utils/redis_client.py
```

**Expected output:**
```
Testing Redis connection...
✅ Redis connection successful!
Info: {'used_memory': '1.2M', 'connected_clients': 1, ...}
```

### 2. Test Multi-Agent Graph

```bash
cd agent
python agent_multi.py
```

**Expected output:**
```
🧪 Testing Multi-Agent DealFinder System
============================================================

📝 Query: Find deals on wireless headphones under $100

🔄 Running multi-agent pipeline...

💬 Chat Node activated
🔧 Backend tools detected, routing to tool execution
🔍 Search Agent activated
✓ Verification Agent activated
🔄 Reranking Agent activated
🎨 Synthesis Agent activated

============================================================
✅ Pipeline Complete!
============================================================

📊 Results Summary:
   - Raw results: 10
   - Verified results: 8
   - Ranked results: 10
   - Deals found: 10
   - Cache hit: False
```

### 3. Test the Full Application

```bash
# Start the app
npm run dev
```

**Try these queries in the UI:**

1. **Basic Search**:
   - "Find deals on wireless headphones"
   - "Search for gaming laptops under $800"

2. **Price Comparison**:
   - "Compare prices for MacBook Air M2"
   - "Find the best price for AirPods Pro"

3. **Verify Caching** (run same query twice):
   - First run: Should see fresh search
   - Second run: Should see `[CACHED]` in results

4. **Check Agent Status**:
   - Look for "Agent Pipeline Summary" in the response
   - Should show all 4 agents completed

---

## 🐛 Troubleshooting

### Redis Connection Issues

**Problem**: `Redis connection failed` or `ECONNREFUSED`

**Solutions**:
1. **Check Redis is running**:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

2. **Verify REDIS_URL**:
   ```bash
   echo $REDIS_URL  # or check agent/.env
   ```

3. **Test connection directly**:
   ```bash
   redis-cli -u redis://localhost:6379 ping
   ```

4. **For Redis Cloud**:
   - Ensure URL starts with `rediss://` (with SSL)
   - Check firewall/IP whitelist settings
   - Verify password is correct

### Agent Not Starting

**Problem**: `npm run dev:agent` fails

**Solutions**:
1. **Check Python dependencies**:
   ```bash
   cd agent
   pip list | grep -E "redis|langchain|langgraph"
   ```

2. **Reinstall dependencies**:
   ```bash
   npm run install:agent
   ```

3. **Check for syntax errors**:
   ```bash
   cd agent
   python -m py_compile agent_multi.py
   ```

### No Cache Hits

**Problem**: Always getting fresh results, never cached

**Solutions**:
1. **Verify caching is enabled**:
   ```bash
   grep ENABLE_CACHING agent/.env
   # Should show: ENABLE_CACHING=true
   ```

2. **Check Redis is connected**:
   ```bash
   cd agent
   python -c "from utils.redis_client import redis_health_check; print(redis_health_check())"
   ```

3. **Monitor cache keys**:
   ```bash
   redis-cli KEYS "search:*"
   redis-cli KEYS "crawl:*"
   ```

### Verification Filtering Too Many Results

**Problem**: Most results are filtered out

**Solutions**:
1. **Lower strictness**:
   ```bash
   # In agent/.env
   VERIFICATION_STRICTNESS=lenient  # Was: strict or moderate
   ```

2. **Disable verification temporarily**:
   ```bash
   ENABLE_VERIFICATION=false
   ```

3. **Check logs** for why results are filtered:
   ```bash
   npm run dev:debug
   # Look for verification reasons in output
   ```

### Slow Response Times

**Problem**: Queries take >10 seconds

**Solutions**:
1. **Enable LLM caching**:
   ```bash
   ENABLE_LLM_CACHE=true
   ```

2. **Use algorithmic ranking** (faster than hybrid):
   ```bash
   RERANKING_STRATEGY=algorithmic
   ```

3. **Reduce result limits**:
   ```bash
   MAX_SEARCH_RESULTS=10
   MAX_VERIFIED_RESULTS=8
   MAX_RANKED_RESULTS=5
   ```

4. **Check network latency** to Redis Cloud:
   ```bash
   redis-cli -u YOUR_REDIS_URL --latency
   ```

---

## 📚 Additional Resources

- **CLAUDE.md** - Detailed architecture and implementation guide
- **README.md** - Original project documentation
- **Agent API Docs** - http://localhost:8123/docs (when running)
- **LangSmith Studio** - https://smith.langchain.com/studio/?baseUrl=http://localhost:8123

---

## 🎉 Success Checklist

- [ ] Redis connected (health check passes)
- [ ] Agent starts without errors
- [ ] UI loads at http://localhost:3000
- [ ] Search query returns results
- [ ] Second search of same query shows `[CACHED]`
- [ ] Agent Pipeline Summary appears in responses
- [ ] All 4 agents show "completed" status
- [ ] Deals display in UI with scores

---

**Happy deal hunting with your advanced multi-agent AI system! 🛒🤖**
