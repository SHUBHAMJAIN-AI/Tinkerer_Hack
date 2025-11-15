"""
Search Agent Node
Handles web search and crawling with Redis caching for performance
"""

import logging
from typing import Any, Dict, List
from typing_extensions import Literal
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langchain.tools import tool
from langchain_tavily import TavilySearch, TavilyExtract, TavilyCrawl
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import AgentState, update_agent_status, track_task, CacheManager, ResultParser
from redis_config import MAX_SEARCH_RESULTS, CACHE_TTL_SEARCH, CACHE_TTL_CRAWL

logger = logging.getLogger(__name__)

# Initialize Tavily web research tools
def create_tavily_tools():
    """Create and configure Tavily tools for web research"""
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        logger.warning("TAVILY_API_KEY not found. Tavily tools will not be functional.")
        return None, None, None

    # General web search for deals and products
    deal_search = TavilySearch(
        max_results=MAX_SEARCH_RESULTS,
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
    Automatically caches results to improve performance.

    Args:
        query: Product name or description to search for
        max_price: Maximum price limit for the search (optional)
        category: Product category (electronics, clothing, home, etc.) (optional)

    Returns:
        Formatted search results with product details and prices
    """
    # Check cache first
    cache_manager = CacheManager()
    cache_key = f"{query}_{max_price}_{category}"

    cached_results = cache_manager.get_cached_search(cache_key)
    if cached_results:
        logger.info(f"✅ Using cached search results for: '{query}'")
        return f"[CACHED] Deal search results for '{query}':\n\n{str(cached_results)}"

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
        # Attempt the web search with timeout handling
        results = tavily_search.run(enhanced_query)
        
        if not results:
            logger.warning(f"No results returned from Tavily search for: '{query}'")
            return f"No deals found for '{query}'. Try a different search term or check back later."

        # Parse the results into structured format
        parsed_results = ResultParser.parse_tavily_response(results)
        
        if not parsed_results:
            logger.warning(f"Failed to parse any results for: '{query}'")
            # Fallback: create a basic result from the raw response
            parsed_results = [{
                "title": f"Search results for {query}",
                "content": str(results)[:200] + "..." if len(str(results)) > 200 else str(results),
                "url": "https://example.com",
                "price": "N/A",
                "store": "Multiple Stores",
                "verified": False,
                "score": 50.0
            }]
        
        # Cache the parsed results
        cache_manager.cache_search_results(cache_key, parsed_results, ttl=CACHE_TTL_SEARCH)

        logger.info(f"✅ Found {len(parsed_results)} structured deals for '{query}'")
        
        # Return structured results for consistency
        return f"Deal search results for '{query}' ({len(parsed_results)} results):\n\n{str(parsed_results)}"
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during search for '{query}': {str(e)}")
        return f"Network error while searching for deals: {str(e)}. Please check your internet connection and try again."
    except Exception as e:
        logger.error(f"Error searching for deals: {str(e)}")
        return f"Error searching for deals: {str(e)}"


@tool
def extract_product_details(url: str) -> str:
    """
    Extract detailed product information from a specific e-commerce page.
    Caches extraction results for faster repeat access.

    Args:
        url: URL of the product page to extract information from

    Returns:
        Detailed product information including price, specifications, reviews
    """
    # Check cache first
    cache_manager = CacheManager()
    cached_data = cache_manager.get_cached_crawl(url)
    if cached_data:
        logger.info(f"✅ Using cached extraction for URL: {url}")
        return f"[CACHED] {str(cached_data)}"

    # Check if Tavily tools are available
    if tavily_extract is None:
        return "Tavily API key not configured. Please set TAVILY_API_KEY environment variable to enable web extraction functionality."

    try:
        result = tavily_extract.run([url])

        # Cache the extraction result
        cache_manager.cache_crawl_data(url, result, ttl=CACHE_TTL_CRAWL)

        return str(result)
    except Exception as e:
        logger.error(f"Error extracting product details from {url}: {str(e)}")
        return f"Error extracting product details from {url}: {str(e)}"


@tool
def crawl_store_catalog(store_url: str, product_category: str = None) -> str:
    """
    Crawl an e-commerce store to find products in a specific category.
    Caches crawl data to avoid redundant requests.

    Args:
        store_url: Base URL of the e-commerce store
        product_category: Specific category to focus on (optional)

    Returns:
        Catalog of products found with basic details
    """
    # Check cache first
    cache_manager = CacheManager()
    cache_key = f"{store_url}_{product_category}"
    cached_data = cache_manager.get_cached_crawl(cache_key)
    if cached_data:
        logger.info(f"✅ Using cached crawl for: {store_url}")
        return f"[CACHED] {str(cached_data)}"

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

        # Cache the crawl result
        cache_manager.cache_crawl_data(cache_key, result, ttl=CACHE_TTL_CRAWL)

        return str(result)
    except Exception as e:
        logger.error(f"Error crawling store catalog: {str(e)}")
        return f"Error crawling store catalog: {str(e)}"


@tool
def compare_prices(product_name: str) -> str:
    """
    Compare prices of a specific product across multiple e-commerce platforms.
    Results are cached for quick access.

    Args:
        product_name: Name or model of the product to compare

    Returns:
        Price comparison results from different stores
    """
    # Check cache first
    cache_manager = CacheManager()
    cached_results = cache_manager.get_cached_search(f"compare_{product_name}")
    if cached_results:
        logger.info(f"✅ Using cached price comparison for: '{product_name}'")
        return f"[CACHED] Price comparison for '{product_name}':\n\n{str(cached_results)}"

    # Check if Tavily tools are available
    if tavily_search is None:
        return "Tavily API key not configured. Please set TAVILY_API_KEY environment variable to enable price comparison functionality."

    try:
        # Search for the product on different platforms
        comparison_query = f"{product_name} price comparison buy"
        results = tavily_search.run(comparison_query)

        # Cache the comparison results
        cache_manager.cache_search_results(f"compare_{product_name}", results, ttl=CACHE_TTL_SEARCH)

        # Return formatted price comparison results
        return f"Price comparison for '{product_name}':\n\n{results}"
    except Exception as e:
        logger.error(f"Error comparing prices: {str(e)}")
        return f"Error comparing prices: {str(e)}"


# Backend tools for search agent
search_backend_tools = [
    search_for_deals,
    extract_product_details,
    crawl_store_catalog,
    compare_prices,
]


async def search_agent(
    state: AgentState,
    config: RunnableConfig
) -> Command[Literal["verification_agent", "tool_node"]]:
    """
    Search Agent Node

    Handles web search and crawling with intelligent caching.
    Routes to tool execution or next agent based on state.

    Args:
        state: Current agent state
        config: Runtime configuration

    Returns:
        Command to route to next node
    """
    logger.info("🔍 Search Agent activated")

    # Update agent status
    state = update_agent_status(state, "search_agent", "running")
    state = track_task(state, "search")

    # Check if we have a cached query
    from langchain_core.messages import HumanMessage
    query = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            query = msg.content
            break

    if query:
        # Try to get cached search results
        cache_manager = CacheManager()
        cached_results = cache_manager.get_cached_search(query)

        if cached_results:
            logger.info(f"✅ Cache HIT for query: '{query}'")
            # Populate state with cached results
            state["raw_search_results"] = cached_results
            state["cache_hit"] = True
            if "cached_queries" not in state:
                state["cached_queries"] = {}
            state["cached_queries"][query] = "hit"

            # Update agent status to completed
            state = update_agent_status(state, "search_agent", "completed")

            # Skip to verification since we have results
            return Command(
                goto="verification_agent",
                update={
                    "raw_search_results": cached_results,
                    "cache_hit": True,
                    "agent_status": state.get("agent_status", {}),
                    "current_agent": "search_agent",
                    "current_task": "search",
                }
            )
        else:
            logger.info(f"❌ Cache MISS for query: '{query}'")
            state["cache_hit"] = False
            if "cached_queries" not in state:
                state["cached_queries"] = {}
            state["cached_queries"][query] = "miss"

    # No cache hit - need to execute tools
    logger.info("🔧 Routing to tool execution")

    return Command(
        goto="tool_node",
        update={
            "cache_hit": False,
            "agent_status": state.get("agent_status", {}),
            "current_agent": "search_agent",
            "current_task": "search",
        }
    )
