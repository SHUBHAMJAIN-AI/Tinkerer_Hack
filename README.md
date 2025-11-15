# 🛒 DealFinder AI - Multi-Agent Shopping Assistant

A sophisticated AI-powered deal-finding and price comparison system built with **CopilotKit**, **LangGraph**, **Tavily**, and **Redis**. Features a multi-agent pipeline with specialized agents for search, verification, reranking, and synthesis.

## 🚀 Quick Start

### Prerequisites

- **Node.js 18+**
- **Python 3.12+**
- **OpenAI API Key** (required) - [Get from OpenAI Platform](https://platform.openai.com/)
- **Tavily API Key** (required) - [Get from Tavily](https://app.tavily.com/home/)
- **Redis Cloud** (optional) - For caching and session management

### Installation Steps

1. **Clone the repository:**
   ```bash
   cd /path/to/dealfinder-ai
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Set up Python virtual environment:**
   ```bash
   python3 -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

4. **Install Python dependencies:**
   ```bash
   cd agent
   pip install -r requirements.txt
   cd ..
   ```

5. **Configure environment variables:**

   Edit `agent/.env` with your API keys:
   ```bash
   # Required API Keys
   OPENAI_API_KEY=your-openai-api-key-here
   TAVILY_API_KEY=your-tavily-api-key-here

   # Optional: Redis Cloud (for caching)
   REDIS_URL=redis://localhost:6379
   # Or for Redis Cloud:
   # REDIS_URL=rediss://default:password@host:port

   # Agent Configuration
   AGENT_TYPE=multi_agent
   LANGCHAIN_TRACING_V2=false
   ```

6. **Start the application:**
   ```bash
   npm run dev
   ```

7. **Open the app:**
   ```
   http://localhost:3000
   ```

## 🎯 Multi-Agent Architecture

The system uses a specialized 4-agent pipeline:

### 1. 🔍 **Search Agent**
- Searches for deals using Tavily web research API
- Implements Redis caching for faster repeated queries
- Tools: `search_for_deals`, `extract_product_details`, `crawl_store_catalog`, `compare_prices`

### 2. ✓ **Verification Agent**
- Validates search results for quality and accessibility
- Checks URL validity, data completeness, and relevance
- Filters out low-quality or inaccessible deals
- Runs verification in parallel using ThreadPoolExecutor

### 3. 🔄 **Reranking Agent**
- Intelligently ranks results using hybrid approach:
  - **Algorithmic scoring**: Price, discount, rating, freshness
  - **LLM semantic analysis**: GPT-3.5-turbo for query intent matching
- Final score: Algorithmic + LLM boost (-20 to +20 points)

### 4. 🎨 **Synthesis Agent**
- Generates comprehensive answers using GPT-4o
- Formats results for frontend display
- Creates price comparisons across stores
- Provides actionable recommendations

## ✨ Features

- **🤖 Multi-Agent Pipeline**: 4 specialized agents working together
- **💾 Redis Caching**: Fast response times for repeated queries (optional)
- **🔍 Smart Search**: Tavily-powered web research across major retailers
- **💰 Price Comparison**: Amazon, eBay, Walmart, Target, Best Buy, Costco
- **📊 Quality Filtering**: Automated verification and ranking
- **💬 Natural Interface**: CopilotKit conversational UI
- **🎨 Dynamic UI**: Real-time generative components

## 🗣️ Try These Commands

```
"Find deals on wireless headphones under $100"
"Compare prices for iPhone 15 Pro"
"Search for gaming laptops with RTX 4060"
"Show me the best deals on 4K TVs"
"Set the theme to purple"
```

## 🛠️ Development

```bash
# Development (both servers)
npm run dev

# UI only (Next.js on port 3000)
npm run dev:ui

# Agent only (LangGraph on port 8123)
npm run dev:agent

# Debug mode
npm run dev:debug
```

## 📁 Project Structure

```
dealfinder-ai/
├── src/
│   ├── app/
│   │   ├── page.tsx              # Main UI component
│   │   └── api/copilotkit/       # CopilotKit API route
│   └── ...
├── agent/
│   ├── agent_multi.py            # Multi-agent orchestrator
│   ├── agent.py                  # Simple single-agent (legacy)
│   ├── nodes/
│   │   ├── search_agent.py       # Search with Tavily + Redis
│   │   ├── verification_agent.py # Quality filtering
│   │   ├── reranking_agent.py    # Hybrid ranking
│   │   └── synthesis_agent.py    # Answer generation
│   ├── utils/
│   │   ├── redis_client.py       # Redis connection manager
│   │   ├── cache.py              # Caching operations
│   │   ├── llm_cache.py          # LLM response caching
│   │   └── state.py              # Agent state schema
│   ├── requirements.txt          # Python dependencies
│   ├── langgraph.json           # Graph configuration
│   └── .env                     # Environment variables
└── package.json
```

## 🔧 Configuration

### Agent Configuration (agent/.env)

```bash
# Choose agent type
AGENT_TYPE=multi_agent  # or "sample_agent" for simple mode

# Enable/disable features
ENABLE_CACHING=true
ENABLE_VERIFICATION=true
ENABLE_RERANKING=true
ENABLE_LLM_CACHE=true

# Verification settings
VERIFICATION_STRICTNESS=moderate  # strict, moderate, lenient

# Reranking settings
RERANKING_STRATEGY=hybrid  # llm, hybrid, algorithmic
RERANKING_MODEL=gpt-3.5-turbo

# Result limits
MAX_SEARCH_RESULTS=20
MAX_VERIFIED_RESULTS=15
MAX_RANKED_RESULTS=10

# Cache TTL (seconds)
REDIS_TTL_SEARCH=3600      # 1 hour
REDIS_TTL_LLM=3600         # 1 hour
REDIS_TTL_SESSIONS=86400   # 24 hours
```

## 📊 System Workflow

```
User Query
    ↓
Chat Node (Entry Point)
    ↓
Tool Node (Backend Tools)
    ↓
Search Agent (Tavily + Redis Cache)
    ↓
Verification Agent (Quality Filtering)
    ↓
Reranking Agent (Hybrid Scoring)
    ↓
Synthesis Agent (Answer Generation)
    ↓
Final Response to User
```

## 🔌 API Endpoints

- **Frontend UI**: http://localhost:3000
- **Agent API**: http://localhost:8123
- **Health Check**: http://localhost:8123/ok
- **API Docs**: http://localhost:8123/docs

## 📚 Dependencies

### Frontend
- Next.js 16
- React 19
- CopilotKit
- TypeScript

### Backend
- LangChain 1.0.7
- LangGraph 1.0.3
- OpenAI SDK
- Tavily Python SDK
- Redis 5.0+
- FastAPI
- Python 3.12

## 🚨 Troubleshooting

### Agent Connection Issues
If you see connection errors:
1. Check that both servers are running (`npm run dev`)
2. Verify ports 3000 and 8123 are available
3. Check API keys in `agent/.env`

### Redis Warnings
Redis SSL warnings are harmless if you see:
```
⚠️ Redis connection failed... Caching disabled
```
The system works without Redis, just without caching benefits.

### Module Not Found Errors
```bash
cd agent
source ../env/bin/activate
pip install -r requirements.txt
```

### Port Already in Use
```bash
# Kill processes on ports
lsof -ti:3000 -ti:8123 | xargs kill -9
```

## 🎓 Learn More

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [CopilotKit Documentation](https://docs.copilotkit.ai)
- [Tavily API](https://docs.tavily.com/)
- [Redis Documentation](https://redis.io/docs/)

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! Feel free to submit issues and pull requests.

---

**Built with ❤️ using LangGraph, CopilotKit, and Tavily**
