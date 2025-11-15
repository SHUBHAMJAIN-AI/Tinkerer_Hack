# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DealFinder AI is a sophisticated multi-agent AI-powered deal-finding and price comparison system built with:
- **Frontend**: Next.js 16 (Turbopack) + React 19 + CopilotKit + Tailwind CSS
- **Backend**: Python + LangGraph multi-agent system + Tavily API + OpenAI GPT-4/GPT-3.5
- **Caching & Sessions**: Redis Cloud with LangChain cache integration
- **Communication**: Model Context Protocol (MCP) via CopilotKit's AG-UI integration

### Dual Graph System
The project supports TWO agent architectures (switchable via `AGENT_TYPE` env variable):
1. **`sample_agent`** (agent.py) - Original single-agent system (backward compatible)
2. **`multi_agent`** (agent_multi.py) - NEW: Advanced multi-agent pipeline with verification, reranking, and Redis caching

## Development Commands

### Starting the Application
```bash
# Start both UI (port 3000) and agent (port 8123) simultaneously
npm run dev

# Start with debug logging
npm run dev:debug

# Start only UI server
npm run dev:ui

# Start only agent server
npm run dev:agent
```

### Build & Production
```bash
# Build for production
npm run build

# Start production server
npm run start

# Lint code
npm run lint
```

### Setup & Dependencies
```bash
# Install all dependencies (includes postinstall for Python agent)
npm install

# Manually install/reinstall agent dependencies
npm run install:agent
```

### Testing & Debugging
```bash
# Check agent API documentation
curl http://localhost:8123/docs

# Verify agent environment variables
cd agent && python -c "import os; print('OPENAI_API_KEY:', bool(os.getenv('OPENAI_API_KEY'))); print('TAVILY_API_KEY:', bool(os.getenv('TAVILY_API_KEY')))"

# Kill processes on ports if needed
lsof -ti:3000 | xargs kill
lsof -ti:8123 | xargs kill
```

## Architecture Overview

### Agent Architecture (Python/LangGraph)

**Location**: `agent/agent.py`

**Pattern**: ReAct (Reasoning + Acting) agent using LangGraph's StateGraph

**State Management** (`AgentState`):
- `messages`: Conversation history (from MessagesState)
- `proverbs`: Shopping wisdom/tips
- `deals_found`: Discovered deals
- `search_results`: Search history
- `price_comparisons`: Price comparison data
- `tools`: Frontend-defined tools passed from CopilotKit

**Graph Structure**:
1. **Entry Point**: `chat_node` - Main reasoning node with GPT-4
2. **Tool Node**: Executes backend tools (search_for_deals, extract_product_details, etc.)
3. **Routing Logic**: `route_to_tool_node()` checks if response has backend tool calls
4. **Flow**: chat_node → tool_node (if needed) → chat_node → END

**Backend Tools**:
- `search_for_deals(query, max_price?, category?)` - Multi-platform deal search
- `extract_product_details(url)` - Deep product information extraction
- `crawl_store_catalog(store_url, product_category?)` - Store catalog exploration
- `compare_prices(product_name)` - Cross-platform price comparison
- `get_weather(location)` - Weather lookup (example tool)

**Tavily Integration**:
- Gracefully handles missing TAVILY_API_KEY (returns informative messages)
- `TavilySearch` - Advanced web search across major retailers
- `TavilyExtract` - Deep content extraction from product pages
- `TavilyCrawl` - Catalog crawling with depth/breadth control

### Frontend Architecture (Next.js/React/CopilotKit)

**Location**: `src/app/page.tsx`

**CopilotKit Integration**:
- `useCoAgent<AgentState>` - Syncs frontend state with LangGraph agent state
- `useCopilotAction` - Defines frontend actions callable by the agent

**Frontend Actions**:
- `setThemeColor` - Dynamic UI theme customization
- `addDeal` - Add discovered deals to UI state
- `addPriceComparison` - Add price comparison data
- `addProverb` - Add shopping wisdom
- `show_deal_card` - Generative UI component for deal display

**UI Components**:
- `DealFinderContent` - Main content area with state display
- `DealCard` - Individual deal display cards
- `PriceComparisonCard` - Price comparison tables
- `CopilotSidebar` - Chat interface (from CopilotKit)

**API Route** (`src/app/api/copilotkit/route.ts`):
- Connects CopilotKit runtime to LangGraph agent via `LangGraphAgent` adapter
- Uses `ExperimentalEmptyAdapter` for single-agent setup
- Proxies requests between frontend and agent server (port 8123)

### Configuration Files

**Agent Config** (`agent/langgraph.json`):
- `python_version`: 3.12
- `graphs.sample_agent`: Points to `agent.py:graph`
- `env`: `.env` file location

**Environment Variables** (`agent/.env`):
```
OPENAI_API_KEY=required
TAVILY_API_KEY=optional (for full functionality)
LANGSMITH_API_KEY=optional (for debugging)
```

## Key Implementation Details

### Agent-Frontend Communication Flow

1. User sends message via CopilotSidebar
2. CopilotKit runtime forwards to LangGraph agent (via `/api/copilotkit` route)
3. Agent's `chat_node` processes with GPT-4, decides on actions
4. If backend tools needed: routes to `tool_node`, executes, returns to `chat_node`
5. Agent can call frontend actions (e.g., `addDeal`, `show_deal_card`)
6. State updates sync bidirectionally between agent and frontend
7. Response streams back to user in sidebar

### Tool Routing Logic

The agent distinguishes between:
- **Backend tools**: Executed in Python (search_for_deals, etc.) - triggers `tool_node`
- **Frontend actions**: Executed in React (addDeal, setThemeColor, etc.) - handled by CopilotKit

**Critical**: `route_to_tool_node()` only routes to tool_node if tool call name matches `backend_tool_names` list.

### State Synchronization

- Agent state (Python) and frontend state (React) share the same structure
- `useCoAgent` hook maintains bidirectional sync
- Agent can update state via tool calls
- Frontend can update state via user interactions (e.g., removing proverbs)

## Common Development Tasks

### Adding a New Backend Tool

1. Define tool in `agent/agent.py` using `@tool` decorator
2. Add to `backend_tools` list
3. Update system prompt in `chat_node` to describe the new tool
4. Agent will automatically use it based on GPT-4's reasoning

### Adding a New Frontend Action

1. Add `useCopilotAction` in `src/app/page.tsx`
2. Define parameters and handler
3. Agent can call it like any other tool
4. For generative UI, add `render` function to the action

### Modifying Agent State

1. Update `AgentState` class in `agent/agent.py`
2. Update TypeScript `AgentState` type in `src/app/page.tsx`
3. Update `initialState` in `useCoAgent` hook
4. Ensure both Python and TypeScript states match

### Debugging Agent Behavior

- Access LangSmith Studio: `https://smith.langchain.com/studio/?baseUrl=http://localhost:8123`
- Check agent API docs: `http://localhost:8123/docs`
- Enable debug logging: `npm run dev:debug`
- Monitor console output for `[agent]` prefixed messages

## Multi-Agent System Architecture (NEW)

### Agent Pipeline Flow
```
User Query → chat_node → tool_node → search_agent → verification_agent →
             reranking_agent → synthesis_agent → END
```

### Agent Nodes (`agent/nodes/`)

**1. Search Agent** ([search_agent.py](agent/nodes/search_agent.py))
- Executes Tavily web search/crawl
- **Redis caching** for search results (1 hour TTL)
- Checks cache before hitting Tavily API
- Stores raw results in state

**2. Verification Agent** ([verification_agent.py](agent/nodes/verification_agent.py))
- Validates URL accessibility (parallel HEAD requests)
- Checks data completeness (required fields)
- Calculates relevance scores (0-100)
- Filters by strictness level (strict/moderate/lenient)
- Outputs verified results with scores

**3. Reranking Agent** ([reranking_agent.py](agent/nodes/reranking_agent.py))
- **Hybrid approach**: Algorithmic scoring + GPT-3.5-turbo semantic analysis
- Scoring factors: price, discount %, rating, freshness, verification score
- LLM provides +/- 20 point boost based on semantic understanding
- Final ranking combines both approaches
- Outputs top N ranked results (configurable)

**4. Synthesis Agent** ([synthesis_agent.py](agent/nodes/synthesis_agent.py))
- Generates comprehensive answer using GPT-4o
- Calls frontend actions (addDeal, show_deal_card, etc.)
- Creates price comparisons
- Returns final formatted response

### Redis Integration

**Location**: `agent/utils/redis_client.py`, `agent/utils/cache.py`

**Caching Strategy**:
- Search results: 1 hour TTL (key: `search:{query_hash}`)
- Web crawl data: 6 hours TTL (key: `crawl:{url_hash}`)
- Chat sessions: 24 hours TTL (key: `session:{session_id}:state`)
- User preferences: 7 days TTL (key: `prefs:{session_id}`)
- LLM responses: 1 hour TTL (automatic via LangChain cache)

**Features**:
- Connection pooling (max 10 connections)
- Retry logic (3 attempts)
- Graceful degradation (works without Redis)
- Health check endpoint

### Configuration (`agent/redis_config.py`)

**Environment Variables** (in agent/.env):
```bash
# Redis
REDIS_URL=redis://localhost:6379  # or rediss:// for Redis Cloud
REDIS_PASSWORD=                    # Optional

# Agent Type
AGENT_TYPE=multi_agent             # or sample_agent

# Feature Flags
ENABLE_CACHING=true
ENABLE_VERIFICATION=true
ENABLE_RERANKING=true
ENABLE_LLM_CACHE=true

# Verification
VERIFICATION_STRICTNESS=moderate   # strict, moderate, lenient

# Reranking
RERANKING_STRATEGY=hybrid          # llm, hybrid, algorithmic
RERANKING_MODEL=gpt-3.5-turbo

# Result Limits
MAX_SEARCH_RESULTS=20
MAX_VERIFIED_RESULTS=15
MAX_RANKED_RESULTS=10
```

### State Management

**Enhanced AgentState** ([utils/state.py](agent/utils/state.py)):
```python
class AgentState(MessagesState):
    # Original fields (backward compatible)
    proverbs, deals_found, search_results, price_comparisons

    # Multi-agent fields
    raw_search_results      # From search agent
    verified_results        # After verification
    ranked_results          # After reranking
    final_answer           # Synthesized response

    # Coordination
    current_agent          # Active agent name
    agent_status          # {agent_name: status}
    agent_errors          # Error tracking

    # Caching
    cache_hit             # Whether results from cache
    session_id            # Redis session ID

    # Metadata
    verification_scores, reranking_confidence
```

### Switching Between Graphs

**Option 1: Environment Variable** (Recommended)
```bash
# In agent/.env
AGENT_TYPE=multi_agent  # or sample_agent

# Frontend also needs to match (in root .env.local)
NEXT_PUBLIC_AGENT_TYPE=multi_agent
```

**Option 2: Runtime Switch**
- Update `agent/.env` and restart: `npm run dev:agent`
- Both graphs are always compiled in `langgraph.json`

## Important Notes

- **Parallel Tool Calls**: Disabled (`parallel_tool_calls=False`) for better control flow
- **Store Targeting**: Searches focus on Amazon, eBay, Walmart, Target, Best Buy, Costco
- **Graceful Degradation**: Works without Redis or Tavily (reduced functionality)
- **ReAct Pattern**: Agent follows think-act-observe cycle for complex queries
- **Models**: GPT-4o (chat/synthesis), GPT-3.5-turbo (reranking)
- **Backward Compatible**: Original `sample_agent` still works unchanged
