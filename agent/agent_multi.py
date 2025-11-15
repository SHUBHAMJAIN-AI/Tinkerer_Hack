"""
Multi-Agent DealFinder System
Orchestrates search, verification, reranking, and synthesis agents
with Redis caching and session management
"""

import os
import datetime
import logging
from typing import Any, List, Dict
from typing_extensions import Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.types import Command
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv

# Import utilities
from utils import (
    AgentState,
    update_agent_status,
    track_task,
    CacheManager,
    redis_health_check
)
from utils.llm_cache import initialize_llm_cache

# Import agent nodes
from nodes import (
    search_agent,
    verification_agent,
    reranking_agent,
    synthesis_agent
)

# Import search tools
from nodes.search_agent import search_backend_tools

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize LLM cache
initialize_llm_cache()

# Check Redis health
redis_status = redis_health_check()
if redis_status["available"]:
    logger.info(f"✅ Redis connected: {redis_status['info']}")
else:
    logger.warning(f"⚠️  Redis not available: {redis_status.get('error', 'Unknown error')}")


# ========== CHAT NODE (Entry Point) ==========

async def chat_node(
    state: AgentState,
    config: RunnableConfig
) -> Command[Literal["tool_node", "search_agent", "synthesis_agent", "__end__"]]:
    """
    Chat Node - Entry point for multi-agent system

    Analyzes user input and routes to appropriate agent or tool execution.
    Handles frontend tool calls and backend tool calls differently.

    Args:
        state: Current agent state
        config: Runtime configuration

    Returns:
        Command to route to next node
    """
    logger.info("💬 Chat Node activated")

    # Initialize session ID if not present
    if not state.get("session_id"):
        import uuid
        session_id = str(uuid.uuid4())[:8]
        state["session_id"] = session_id
        logger.info(f"📝 New session created: {session_id}")
    else:
        session_id = state["session_id"]

    # 1. Define the model
    model = ChatOpenAI(model="gpt-4o", temperature=0.3)

    # 2. Bind tools to the model
    model_with_tools = model.bind_tools(
        [
            *state.get("tools", []),  # Frontend tools from CopilotKit
            *search_backend_tools,     # Backend search tools
        ],
        parallel_tool_calls=False,
    )

    # 3. Create system prompt
    today = datetime.datetime.today().strftime("%A, %B %d, %Y")

    system_message = SystemMessage(
        content=f"""You are DealFinder AI, an advanced multi-agent shopping assistant powered by specialized AI agents.

**Today's Date:** {today}
**Session ID:** {state.get('session_id', 'N/A')}

**Your Multi-Agent System:**
1. 🔍 **Search Agent** - Finds deals using Tavily web research (with Redis caching)
2. ✓ **Verification Agent** - Validates results for quality and accessibility
3. 🔄 **Reranking Agent** - Intelligently orders results by relevance (hybrid AI)
4. 🎨 **Synthesis Agent** - Generates comprehensive answers and recommendations

**Current Pipeline Status:**
{_format_agent_status(state.get('agent_status', {}))}

**Available Tools:**
- search_for_deals(query, max_price?, category?) - Search for product deals
- extract_product_details(url) - Get detailed product information
- crawl_store_catalog(store_url, category?) - Explore store catalogs
- compare_prices(product_name) - Compare prices across platforms

**Frontend Actions** (for UI updates):
- setThemeColor - Change UI theme
- addDeal - Add deal to UI
- show_deal_card - Display deal card
- addPriceComparison - Show price comparison
- addProverb - Add shopping wisdom

**Your Mission:**
- Help users find the best deals with multi-agent intelligence
- Use tools to search, then let the pipeline handle verification and ranking
- Focus on major retailers: Amazon, eBay, Walmart, Target, Best Buy, Costco
- Provide clear, actionable recommendations with source URLs
- Leverage caching for faster responses

**Workflow:**
1. When user asks for deals → Use search tools
2. Results automatically verified by Verification Agent
3. Results automatically ranked by Reranking Agent
4. Final answer synthesized by Synthesis Agent
5. You receive the polished results to present

Be helpful, accurate, and leverage your multi-agent capabilities!
"""
    )

    # 4. Run the model
    response = await model_with_tools.ainvoke([
        system_message,
        *state["messages"],
    ], config)

    # 5. Route based on tool calls
    tool_calls = getattr(response, "tool_calls", None)

    if not tool_calls:
        # No tool calls - return response and end
        logger.info("📤 No tool calls, ending conversation")
        return Command(
            goto=END,
            update={"messages": [response]}
        )

    # Check if any tool calls are backend tools
    backend_tool_names = [tool.name for tool in search_backend_tools]
    has_backend_tools = any(tc.get("name") in backend_tool_names for tc in tool_calls)

    if has_backend_tools:
        # Backend tools detected - route to tool execution then search agent
        logger.info("🔧 Backend tools detected, routing to tool execution")
        return Command(
            goto="tool_node",
            update={"messages": [response]}
        )
    else:
        # Only frontend tools - let them execute and end
        logger.info("🎨 Frontend tools only, ending")
        return Command(
            goto=END,
            update={"messages": [response]}
        )


def _format_agent_status(agent_status: Dict[str, str]) -> str:
    """Format agent status for system prompt"""
    if not agent_status:
        return "No agents have run yet"

    status_symbols = {
        "running": "🔄",
        "completed": "✅",
        "failed": "❌",
        "skipped": "⏭️",
        "no_data": "⚠️"
    }

    lines = []
    for agent, status in agent_status.items():
        symbol = status_symbols.get(status, "❓")
        lines.append(f"  {symbol} {agent}: {status}")

    return "\n".join(lines)


# ========== ROUTING FUNCTIONS ==========

def route_after_tools(state: AgentState) -> Literal["verification_agent", "chat_node"]:
    """
    Route after tool execution

    Always route to verification_agent after tool execution to process results.
    """
    logger.info("🔍 Tool execution complete, routing to verification agent")
    return "verification_agent"


# ========== BUILD GRAPH ==========

def build_multi_agent_graph() -> StateGraph:
    """
    Build the multi-agent workflow graph

    Flow:
        chat_node → tool_node → search_agent → verification_agent →
        reranking_agent → synthesis_agent → END

    Returns:
        Compiled StateGraph
    """
    logger.info("🏗️  Building multi-agent graph...")

    # Create graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("chat_node", chat_node)
    workflow.add_node("tool_node", ToolNode(tools=search_backend_tools))
    workflow.add_node("search_agent", search_agent)
    workflow.add_node("verification_agent", verification_agent)
    workflow.add_node("reranking_agent", reranking_agent)
    workflow.add_node("synthesis_agent", synthesis_agent)

    # Set entry point
    workflow.set_entry_point("chat_node")

    # Add edges
    # tool_node can route to verification_agent or back to chat_node
    workflow.add_conditional_edges(
        "tool_node",
        route_after_tools,
        {
            "verification_agent": "verification_agent",
            "chat_node": "chat_node"
        }
    )

    # chat_node routes are defined in the node itself via Command

    # search_agent routes are defined in the node itself via Command
    # (goes to verification_agent or tool_node)

    # Linear flow after search
    # verification_agent → reranking_agent (defined in verification_agent.py)
    # reranking_agent → synthesis_agent (defined in reranking_agent.py)
    # synthesis_agent → END (defined in synthesis_agent.py)

    logger.info("✅ Multi-agent graph built successfully")

    return workflow


# ========== COMPILE GRAPH ==========

# Build and compile the graph
workflow = build_multi_agent_graph()
graph = workflow.compile()

logger.info("🚀 Multi-agent DealFinder system ready!")
logger.info(f"   - Search Agent: ✓ (with Redis caching)")
logger.info(f"   - Verification Agent: ✓ (quality filtering)")
logger.info(f"   - Reranking Agent: ✓ (hybrid AI ranking)")
logger.info(f"   - Synthesis Agent: ✓ (answer generation)")


# ========== MAIN (For Testing) ==========

if __name__ == "__main__":
    import asyncio

    async def test_graph():
        """Test the multi-agent graph"""
        print("\n" + "="*60)
        print("🧪 Testing Multi-Agent DealFinder System")
        print("="*60 + "\n")

        # Test input
        test_query = "Find deals on wireless headphones under $100"

        initial_state = {
            "messages": [HumanMessage(content=test_query)],
            "session_id": "test_session",
        }

        print(f"📝 Query: {test_query}\n")
        print("🔄 Running multi-agent pipeline...\n")

        try:
            result = await graph.ainvoke(initial_state)

            print("\n" + "="*60)
            print("✅ Pipeline Complete!")
            print("="*60 + "\n")

            print(f"📊 Results Summary:")
            print(f"   - Raw results: {len(result.get('raw_search_results', []))}")
            print(f"   - Verified results: {len(result.get('verified_results', []))}")
            print(f"   - Ranked results: {len(result.get('ranked_results', []))}")
            print(f"   - Deals found: {len(result.get('deals_found', []))}")
            print(f"   - Cache hit: {result.get('cache_hit', False)}")
            print(f"\n📝 Final Answer:\n{result.get('final_answer', 'No answer generated')}")

            if result.get("agent_errors"):
                print(f"\n⚠️  Errors: {len(result['agent_errors'])}")
                for error in result["agent_errors"]:
                    print(f"   - {error['agent']}: {error['error']}")

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

    # Run test
    asyncio.run(test_graph())
