#!/usr/bin/env python3
"""
DealFinder AI Agent - Simplified Version
A web research agent for finding deals and comparing prices across e-commerce platforms.
"""

import asyncio
import json
import os
import traceback
from typing import Any, Dict, List, Optional, TypedDict
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool

# Tavily import (optional)
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    print("Tavily not available. Web search functionality will be limited.")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize APIs
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Initialize clients
llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=OPENAI_API_KEY,
    temperature=0.1
)

tavily_client = None
if TAVILY_AVAILABLE and TAVILY_API_KEY:
    try:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        print("✅ Tavily client initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing Tavily client: {e}")

# Data models
class Deal(TypedDict):
    product_name: str
    store: str
    price: str
    original_price: Optional[str]
    discount: Optional[str]
    url: str
    description: str
    rating: Optional[str]
    availability: str

class PriceComparison(TypedDict):
    product_name: str
    stores: List[Dict[str, Any]]
    lowest_price: str
    highest_price: str
    savings: str

class AgentRequest(BaseModel):
    messages: List[Dict[str, Any]]

class AgentResponse(BaseModel):
    messages: List[Dict[str, Any]]

# Tools
@tool
def search_for_deals(query: str, max_results: int = 10) -> str:
    """
    Search for product deals across major e-commerce platforms.
    
    Args:
        query: Product search query (e.g., "iPhone 15", "running shoes", "laptop deals")
        max_results: Maximum number of results to return (default: 10)
    
    Returns:
        JSON string with search results containing deals information
    """
    try:
        if tavily_client:
            # Use Tavily for comprehensive search
            search_query = f"{query} deals price comparison site:amazon.com OR site:walmart.com OR site:target.com OR site:bestbuy.com"
            
            results = tavily_client.search(
                query=search_query,
                search_depth="advanced",
                max_results=max_results,
                include_domains=["amazon.com", "walmart.com", "target.com", "bestbuy.com", "ebay.com"]
            )
            
            deals = []
            for result in results.get('results', []):
                deal = {
                    "product_name": query,
                    "store": result.get('url', '').split('/')[2].replace('www.', ''),
                    "price": "Price available on site",
                    "original_price": None,
                    "discount": None,
                    "url": result.get('url', ''),
                    "description": result.get('content', ''),
                    "rating": None,
                    "availability": "Check website"
                }
                deals.append(deal)
            
            return json.dumps({
                "query": query,
                "deals_found": len(deals),
                "deals": deals,
                "search_method": "tavily_web_search"
            }, indent=2)
        else:
            # Fallback to mock data
            mock_deals = [
                {
                    "product_name": query,
                    "store": "amazon.com",
                    "price": "$299.99",
                    "original_price": "$399.99",
                    "discount": "25% off",
                    "url": f"https://amazon.com/search?q={query.replace(' ', '+')}",
                    "description": f"Great deal on {query} with fast shipping",
                    "rating": "4.5/5",
                    "availability": "In Stock"
                },
                {
                    "product_name": query,
                    "store": "walmart.com", 
                    "price": "$289.99",
                    "original_price": "$379.99",
                    "discount": "24% off",
                    "url": f"https://walmart.com/search?q={query.replace(' ', '+')}",
                    "description": f"Competitive price for {query}",
                    "rating": "4.3/5", 
                    "availability": "In Stock"
                }
            ]
            
            return json.dumps({
                "query": query,
                "deals_found": len(mock_deals),
                "deals": mock_deals,
                "search_method": "mock_data",
                "note": "Tavily API not available. Using sample data for demonstration."
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "error": f"Search failed: {str(e)}",
            "query": query,
            "deals_found": 0,
            "deals": []
        }, indent=2)

@tool  
def compare_prices(product_name: str, stores: List[str] = None) -> str:
    """
    Compare prices for a specific product across multiple stores.
    
    Args:
        product_name: Name of the product to compare
        stores: List of store domains to search (optional)
    
    Returns:
        JSON string with price comparison data
    """
    try:
        if not stores:
            stores = ["amazon.com", "walmart.com", "target.com", "bestbuy.com"]
            
        if tavily_client:
            all_results = []
            
            for store in stores:
                try:
                    search_query = f"{product_name} price site:{store}"
                    results = tavily_client.search(
                        query=search_query,
                        search_depth="basic",
                        max_results=3,
                        include_domains=[store]
                    )
                    
                    for result in results.get('results', []):
                        all_results.append({
                            "store": store,
                            "url": result.get('url', ''),
                            "content": result.get('content', ''),
                            "title": result.get('title', '')
                        })
                except Exception as e:
                    print(f"Error searching {store}: {e}")
                    continue
            
            return json.dumps({
                "product_name": product_name,
                "stores_searched": stores,
                "results_found": len(all_results),
                "results": all_results,
                "search_method": "tavily_web_search"
            }, indent=2)
        else:
            # Mock comparison data
            mock_comparison = {
                "product_name": product_name,
                "stores": [
                    {"store": "amazon.com", "price": "$299.99", "availability": "In Stock"},
                    {"store": "walmart.com", "price": "$289.99", "availability": "In Stock"},
                    {"store": "target.com", "price": "$319.99", "availability": "Limited"},
                    {"store": "bestbuy.com", "price": "$309.99", "availability": "In Stock"}
                ],
                "lowest_price": "$289.99",
                "highest_price": "$319.99", 
                "savings": "$30.00",
                "search_method": "mock_data"
            }
            
            return json.dumps(mock_comparison, indent=2)
            
    except Exception as e:
        return json.dumps({
            "error": f"Price comparison failed: {str(e)}",
            "product_name": product_name,
            "stores_searched": stores or [],
            "results": []
        }, indent=2)

@tool
def extract_product_details(product_url: str) -> str:
    """
    Extract detailed product information from a specific product page.
    
    Args:
        product_url: URL of the product page to analyze
    
    Returns:
        JSON string with detailed product information
    """
    try:
        if tavily_client:
            # Extract content from specific URL
            results = tavily_client.extract(urls=[product_url])
            
            extracted_data = {
                "url": product_url,
                "content_extracted": True,
                "details": results.get('results', [{}])[0] if results.get('results') else {},
                "extraction_method": "tavily_extract"
            }
            
            return json.dumps(extracted_data, indent=2)
        else:
            # Mock product details
            mock_details = {
                "url": product_url,
                "product_name": "Sample Product",
                "price": "$299.99",
                "rating": "4.4/5 stars",
                "reviews_count": "1,234 reviews",
                "availability": "In Stock",
                "features": ["Feature 1", "Feature 2", "Feature 3"],
                "description": "High-quality product with excellent reviews",
                "extraction_method": "mock_data"
            }
            
            return json.dumps(mock_details, indent=2)
            
    except Exception as e:
        return json.dumps({
            "error": f"Product extraction failed: {str(e)}",
            "url": product_url,
            "content_extracted": False
        }, indent=2)

@tool
def crawl_store_catalog(store_domain: str, category: str = None) -> str:
    """
    Explore a store's catalog for deals in a specific category.
    
    Args:
        store_domain: Domain of the store (e.g., "amazon.com")
        category: Product category to focus on (optional)
    
    Returns:
        JSON string with catalog exploration results
    """
    try:
        if tavily_client:
            if category:
                search_query = f"{category} deals site:{store_domain}"
            else:
                search_query = f"deals sale clearance site:{store_domain}"
                
            results = tavily_client.search(
                query=search_query,
                search_depth="basic",
                max_results=15,
                include_domains=[store_domain]
            )
            
            catalog_data = {
                "store_domain": store_domain,
                "category": category,
                "items_found": len(results.get('results', [])),
                "items": results.get('results', []),
                "search_method": "tavily_crawl"
            }
            
            return json.dumps(catalog_data, indent=2)
        else:
            # Mock catalog data
            mock_catalog = {
                "store_domain": store_domain,
                "category": category or "general",
                "items_found": 5,
                "items": [
                    {"title": f"Great deal on {category or 'products'}", "url": f"https://{store_domain}/deal1"},
                    {"title": f"Limited time offer", "url": f"https://{store_domain}/deal2"},
                    {"title": f"Clearance sale", "url": f"https://{store_domain}/deal3"}
                ],
                "search_method": "mock_data"
            }
            
            return json.dumps(mock_catalog, indent=2)
            
    except Exception as e:
        return json.dumps({
            "error": f"Catalog crawl failed: {str(e)}",
            "store_domain": store_domain,
            "category": category,
            "items_found": 0,
            "items": []
        }, indent=2)

# System prompt
SYSTEM_PROMPT = """You are DealFinder AI, an expert web research agent specializing in finding the best deals and comparing prices across major e-commerce platforms.

Your capabilities include:
1. 🔍 **Product Search**: Search for deals across Amazon, Walmart, Target, Best Buy, and other major retailers
2. 💰 **Price Comparison**: Compare prices for specific products across multiple stores  
3. 📊 **Product Analysis**: Extract detailed product information including ratings, reviews, and specifications
4. 🏪 **Store Exploration**: Browse store catalogs for category-specific deals and promotions

**Available Tools:**
- search_for_deals(query, max_results): Find deals for any product
- compare_prices(product_name, stores): Compare prices across stores
- extract_product_details(product_url): Get detailed product information
- crawl_store_catalog(store_domain, category): Explore store deals

**Response Guidelines:**
- Always provide specific, actionable information
- Include prices, discounts, and store names when available
- Highlight the best deals and savings opportunities
- Mention product ratings and availability
- Provide direct links when possible
- Be concise but comprehensive

**Example Queries You Can Handle:**
- "Find the best deals on iPhone 15"
- "Compare laptop prices under $1000"
- "What are the best Black Friday TV deals?"
- "Find running shoes on sale"
- "Compare prices for Nintendo Switch"

Start by understanding what the user is looking for, then use the appropriate tools to find the best deals and provide a helpful summary.
"""

# FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "DealFinder AI Agent",
        "status": "running",
        "tavily_available": tavily_client is not None,
        "tools": ["search_for_deals", "compare_prices", "extract_product_details", "crawl_store_catalog"]
    }

@app.post("/chat")
async def chat_endpoint(request: AgentRequest):
    try:
        messages = request.messages
        
        # Convert to LangChain messages
        lc_messages = [SystemMessage(content=SYSTEM_PROMPT)]
        
        for msg in messages:
            if msg.get("role") == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
        
        # Get user's latest message
        user_message = messages[-1]["content"] if messages else ""
        
        # Simple tool routing based on user intent
        response_content = ""
        
        if any(keyword in user_message.lower() for keyword in ["find", "search", "deals", "looking for"]):
            # Extract product name from user message
            product_query = user_message.replace("find", "").replace("search", "").replace("deals", "").replace("for", "").strip()
            result = search_for_deals.invoke({"query": product_query})
            response_content = f"I found some great deals for you! Here's what I discovered:\n\n{result}"
            
        elif any(keyword in user_message.lower() for keyword in ["compare", "comparison", "prices", "vs"]):
            # Extract product name for comparison
            product_name = user_message.replace("compare", "").replace("prices", "").replace("for", "").strip()
            result = compare_prices.invoke({"product_name": product_name})
            response_content = f"Here's the price comparison for {product_name}:\n\n{result}"
            
        elif "http" in user_message and any(keyword in user_message.lower() for keyword in ["details", "extract", "analyze"]):
            # Extract URL and get details
            import re
            urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', user_message)
            if urls:
                result = extract_product_details.invoke({"product_url": urls[0]})
                response_content = f"Here are the product details:\n\n{result}"
            else:
                response_content = "I couldn't find a valid URL in your message. Please provide a product URL to analyze."
                
        elif any(keyword in user_message.lower() for keyword in ["catalog", "browse", "explore", "store"]):
            # Default store exploration
            result = crawl_store_catalog.invoke({"store_domain": "amazon.com", "category": "deals"})
            response_content = f"Here's what I found while browsing for deals:\n\n{result}"
            
        else:
            # General LLM response
            lc_messages.append(HumanMessage(content=user_message))
            response = llm.invoke(lc_messages)
            response_content = response.content
        
        return AgentResponse(
            messages=[
                {
                    "role": "assistant", 
                    "content": response_content
                }
            ]
        )
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting DealFinder AI Agent...")
    print(f"📡 Tavily Web Search: {'✅ Available' if tavily_client else '❌ Not Available'}")
    print(f"🤖 OpenAI API: {'✅ Available' if OPENAI_API_KEY else '❌ Not Available'}")
    print("🌐 Server starting on http://localhost:8123")
    
    uvicorn.run(app, host="0.0.0.0", port=8123)
