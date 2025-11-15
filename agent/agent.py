"""
DealFinder AI Agent - A web research agent for finding and comparing deals
This is the main entry point for the agent.
It defines the workflow graph, state, tools, nodes and edges.
"""

import os
import datetime
from typing import Any, List, Dict
from typing_extensions import Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.types import Command
from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode
from langchain_tavily import TavilySearch, TavilyExtract, TavilyCrawl
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AgentState(MessagesState):
    """
    DealFinder Agent State
    
    This state manages both the conversation and deal-finding specific data.
    """
    proverbs: List[str] = []
    tools: List[Any] = []
    deals_found: List[Dict[str, Any]] = []
    search_results: List[Dict[str, Any]] = []
    price_comparisons: List[Dict[str, Any]] = []

# Initialize Tavily web research tools
def create_tavily_tools():
    """Create and configure Tavily tools for web research"""
    # Check if Tavily API key is available
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        print("Warning: TAVILY_API_KEY not found. Tavily tools will not be functional.")
        # Return mock tools that explain they need API key
        return None, None, None
    
    # General web search for deals and products
    deal_search = TavilySearch(
        max_results=10,
        topic="general",
        search_depth="advanced",
        include_domains=["amazon.com", "ebay.com", "walmart.com", "target.com", "bestbuy.com", "costco.com"]
    )
    
    # Extract detailed product information from specific pages
    product_extract = TavilyExtract(extract_depth="advanced", include_images=True)
    
    # Crawl e-commerce sites for comprehensive product catalogs
    product_crawl = TavilyCrawl(max_depth=2, max_breadth=5)
    
    return deal_search, product_extract, product_crawl

# Create Tavily tools
tavily_search, tavily_extract, tavily_crawl = create_tavily_tools()

@tool
def search_for_deals(query: str, max_price: float = None, category: str = None) -> str:
    """
    Search for deals and discounts on products across major e-commerce platforms.
    
    Args:
        query: Product name or description to search for
        max_price: Maximum price limit for the search (optional)
        category: Product category (electronics, clothing, home, etc.) (optional)
    
    Returns:
        Formatted search results with product details and prices
    """
    # Check if Tavily tools are available
    if tavily_search is None:
        return "Tavily API key not configured. Please set TAVILY_API_KEY environment variable to enable web search functionality."
    
    # Enhance query for better deal finding
    enhanced_query = f"{query} deals discount sale price"
    if category:
        enhanced_query += f" {category}"
    if max_price:
        enhanced_query += f" under ${max_price}"
    
    try:
        results = tavily_search.run(enhanced_query)
        # Return the search results as a formatted string
        return f"Deal search results for '{query}':\n\n{results}"
    except Exception as e:
        return f"Error searching for deals: {str(e)}"

@tool
def extract_product_details(url: str) -> str:
    """
    Extract detailed product information from a specific e-commerce page.
    
    Args:
        url: URL of the product page to extract information from
    
    Returns:
        Detailed product information including price, specifications, reviews
    """
    # Check if Tavily tools are available
    if tavily_extract is None:
        return "Tavily API key not configured. Please set TAVILY_API_KEY environment variable to enable web extraction functionality."
    
    try:
        result = tavily_extract.run([url])
        return str(result)
    except Exception as e:
        return f"Error extracting product details from {url}: {str(e)}"

@tool
def crawl_store_catalog(store_url: str, product_category: str = None) -> str:
    """
    Crawl an e-commerce store to find products in a specific category.
    
    Args:
        store_url: Base URL of the e-commerce store
        product_category: Specific category to focus on (optional)
    
    Returns:
        Catalog of products found with basic details
    """
    # Check if Tavily tools are available
    if tavily_crawl is None:
        return "Tavily API key not configured. Please set TAVILY_API_KEY environment variable to enable web crawling functionality."
    
    try:
        # Configure crawl with product-specific paths if category is provided
        if product_category:
            result = tavily_crawl.run(
                store_url,
                include_paths=[f"/{product_category}", f"/category/{product_category}", f"/products/{product_category}"]
            )
        else:
            result = tavily_crawl.run(store_url)
        return str(result)
    except Exception as e:
        return f"Error crawling store catalog: {str(e)}"

@tool
def compare_prices(product_name: str) -> str:
    """
    Compare prices of a specific product across multiple e-commerce platforms.
    
    Args:
        product_name: Name or model of the product to compare
    
    Returns:
        Price comparison results from different stores
    """
    # Check if Tavily tools are available
    if tavily_search is None:
        return "Tavily API key not configured. Please set TAVILY_API_KEY environment variable to enable price comparison functionality."
    
    try:
        # Search for the product on different platforms
        comparison_query = f"{product_name} price comparison buy"
        results = tavily_search.run(comparison_query)
        
        # Return formatted price comparison results
        return f"Price comparison for '{product_name}':\n\n{results}"
    except Exception as e:
        return f"Error comparing prices: {str(e)}"

@tool  
def get_weather(location: str):
    """
    Get the weather for a given location.
    """
    return f"The weather for {location} is 70 degrees."

# Define all backend tools
backend_tools = [
    search_for_deals,
    extract_product_details,
    crawl_store_catalog,
    compare_prices,
    get_weather
]

# Extract tool names from backend_tools for comparison
backend_tool_names = [tool.name for tool in backend_tools]

async def chat_node(state: AgentState, config: RunnableConfig) -> Command[Literal["tool_node", "__end__"]]:
    """
    DealFinder chat node based on the ReAct design pattern.
    Specialized for finding deals, comparing prices, and researching products.
    """

    # 1. Define the model
    model = ChatOpenAI(model="gpt-4o")

    # 2. Bind the tools to the model
    model_with_tools = model.bind_tools(
        [
            *state.get("tools", []), # bind tools defined by CopilotKit
            *backend_tools,
        ],
        parallel_tool_calls=False,  # Disable parallel tool calls for better control
    )

    # 3. Create DealFinder-specific system prompt
    today = datetime.datetime.today().strftime("%A, %B %d, %Y")
    
    system_message = SystemMessage(
        content=f"""You are DealFinder AI, an expert web research agent specializing in finding the best deals, 
comparing prices, and researching products across major e-commerce platforms.

**Today's Date:** {today}

**Your Mission:** Help users find the best deals, compare prices, and make informed purchasing decisions.

**Available Tools:**
1. **search_for_deals** - Search for deals and discounts on products
2. **extract_product_details** - Get detailed information from specific product pages  
3. **crawl_store_catalog** - Explore store catalogs for comprehensive product discovery
4. **compare_prices** - Compare prices across multiple platforms
5. **get_weather** - Get weather information (for context)

**Current State:**
- Proverbs: {state.get('proverbs', [])}
- Deals Found: {len(state.get('deals_found', []))} deals
- Recent Searches: {len(state.get('search_results', []))} results

**Guidelines:**
- Always search for current deals and compare prices across multiple platforms
- Focus on major retailers: Amazon, eBay, Walmart, Target, Best Buy, Costco
- Provide clear price comparisons with source URLs
- Look for discounts, sales, and special offers
- Extract detailed product specifications when relevant
- Recommend the best value options based on price and features
- Always cite your sources with URLs

**Workflow:**
1. **Search** for deals using search_for_deals
2. **Extract** details from promising product pages using extract_product_details  
3. **Compare** prices across platforms using compare_prices
4. **Crawl** store catalogs if comprehensive discovery is needed
5. **Synthesize** findings into actionable recommendations

Be thorough, accurate, and always provide the best deals with clear source attribution.
"""
    )

    # 4. Run the model to generate a response
    response = await model_with_tools.ainvoke([
        system_message,
        *state["messages"],
    ], config)

    # 5. Route to tool node if needed
    if route_to_tool_node(response):
        print("routing to tool node")
        return Command(
            goto="tool_node",
            update={
                "messages": [response],
            }
        )

    # 6. End the conversation
    return Command(
        goto=END,
        update={
            "messages": [response],
        }
    )

def route_to_tool_node(response: BaseMessage):
    """
    Route to tool node if any tool call in the response matches a backend tool name.
    """
    tool_calls = getattr(response, "tool_calls", None)
    if not tool_calls:
        return False

    for tool_call in tool_calls:
        if tool_call.get("name") in backend_tool_names:
            return True
    return False

# Define the DealFinder workflow graph
workflow = StateGraph(AgentState)
workflow.add_node("chat_node", chat_node)
workflow.add_node("tool_node", ToolNode(tools=backend_tools))
workflow.add_edge("tool_node", "chat_node")
workflow.set_entry_point("chat_node")

# Compile the graph
graph = workflow.compile()
