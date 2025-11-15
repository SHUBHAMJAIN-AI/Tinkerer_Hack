#!/usr/bin/env python3
"""
24-Hour Deal Freshness System - Interactive Demo
Shows the deal freshness validation system in action
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.deal_freshness import get_deal_freshness_manager
from utils.redis_client import get_redis_client
from utils.cache import CacheManager

def print_header(title):
    """Print a styled header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def print_box(content, color="blue"):
    """Print content in a colored box"""
    colors = {
        "blue": "\033[94m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "reset": "\033[0m"
    }
    
    print(f"{colors.get(color, '')}{content}{colors['reset']}")

def demo_category_detection():
    """Demonstrate category detection"""
    print_header("🔍 Demo 1: Automatic Category Detection")
    
    manager = get_deal_freshness_manager()
    
    queries = [
        "iPhone 15 Pro Max",
        "Nintendo Switch OLED",
        "Running shoes Nike",
        "Kitchen blender",
        "Microsoft Office 365 license"
    ]
    
    for query in queries:
        category = manager._detect_category(query)
        ttl_hours = manager.CATEGORY_THRESHOLDS.get(category, 24)
        
        print(f"Query: '{query}'")
        print(f"  → Category: {category}")
        print(f"  → Cache TTL: {ttl_hours} hours")
        print(f"  → Freshness: Deals refresh every {ttl_hours}h\n")

def demo_price_sensitivity():
    """Demonstrate price-sensitive detection"""
    print_header("💰 Demo 2: Price-Sensitive Query Detection")
    
    manager = get_deal_freshness_manager()
    
    test_queries = [
        ("iPhone 15 Pro", False, "Normal query"),
        ("cheapest iPhone 15", True, "Price-sensitive"),
        ("best deal MacBook Pro", True, "Price-sensitive"),
        ("Nintendo Switch review", False, "Normal query"),
        ("hot deal on laptop", True, "Price-sensitive")
    ]
    
    for query, expected, label in test_queries:
        is_sensitive = manager._is_price_sensitive(query)
        optimal_ttl = manager.get_optimal_ttl(query)
        
        icon = "🔥" if is_sensitive else "📱"
        print(f"{icon} '{query}'")
        print(f"  → Type: {label}")
        print(f"  → Price-Sensitive: {'Yes' if is_sensitive else 'No'}")
        print(f"  → Cache TTL: {optimal_ttl/3600:.0f} hours")
        print()

def demo_freshness_lifecycle():
    """Demonstrate deal freshness lifecycle"""
    print_header("⏰ Demo 3: Deal Freshness Lifecycle (24-Hour Rule)")
    
    manager = get_deal_freshness_manager()
    
    # Simulate deals at different ages
    ages = [
        (2, "Fresh - Just cached"),
        (6, "Good - Still reliable"),
        (15, "Stale - Approaching limit"),
        (25, "Expired - Must refresh"),
        (48, "Very old - Definitely expired")
    ]
    
    for age_hours, description in ages:
        timestamp = datetime.now().timestamp() - (age_hours * 3600)
        
        cached_data = {
            "timestamp": timestamp,
            "query": "iPhone 15 Pro deals",
            "results": [{
                "title": "iPhone 15 Pro - $999",
                "freshness_metadata": {
                    "cached_at": timestamp,
                    "category": "electronics",
                    "recommended_refresh_hours": 4,
                    "max_age_hours": 24
                }
            }]
        }
        
        validity = manager.check_deals_validity(cached_data)
        
        # Color code based on action
        if validity["action"] == "use_cache":
            color = "green"
            action_icon = "✅"
        elif validity["action"] == "consider_refresh":
            color = "yellow"
            action_icon = "⚠️"
        else:
            color = "red"
            action_icon = "🔄"
        
        print_box(f"{action_icon} {description} ({age_hours} hours old)", color)
        print(f"  Valid: {validity['valid']}")
        print(f"  Action: {validity['action']}")
        print(f"  Reason: {validity['reason']}")
        if validity.get("warning"):
            print(f"  Warning: {validity['warning']}")
        print()

def demo_category_ttl():
    """Demonstrate category-based TTL optimization"""
    print_header("🎯 Demo 4: Smart TTL Based on Product Category")
    
    manager = get_deal_freshness_manager()
    
    products = [
        ("iPhone 15 Pro deals", "electronics", "Prices change frequently"),
        ("Nintendo Switch OLED", "gaming", "Moderate price stability"),
        ("Kindle books on sale", "books", "Very stable pricing"),
        ("Nike running shoes", "fashion", "Seasonal changes"),
        ("Adobe Creative Cloud", "software", "License deals vary")
    ]
    
    print("Product Category Analysis:\n")
    
    for query, expected_category, reasoning in products:
        category = manager._detect_category(query)
        ttl_seconds = manager.get_optimal_ttl(query)
        ttl_hours = ttl_seconds / 3600
        
        print(f"📦 {query}")
        print(f"   Category: {category}")
        print(f"   Reasoning: {reasoning}")
        print(f"   Cache TTL: {ttl_hours:.0f} hours")
        print(f"   Refresh frequency: Every {ttl_hours:.0f}h to ensure fresh prices")
        print()

def demo_real_world_scenario():
    """Demonstrate a real-world search scenario"""
    print_header("🌟 Demo 5: Real-World Search Scenario")
    
    manager = get_deal_freshness_manager()
    cache_manager = CacheManager()
    redis_client = get_redis_client()
    
    query = "cheapest MacBook Pro M3 deals"
    
    print(f"User searches: '{query}'\n")
    
    # Step 1: Detect characteristics
    category = manager._detect_category(query)
    is_price_sensitive = manager._is_price_sensitive(query)
    optimal_ttl = manager.get_optimal_ttl(query)
    
    print("Step 1: Query Analysis")
    print(f"  → Detected category: {category}")
    print(f"  → Price-sensitive: {is_price_sensitive}")
    print(f"  → Optimal TTL: {optimal_ttl/3600:.0f} hours\n")
    
    # Step 2: Simulate API results
    print("Step 2: Fetching Fresh Deals from API")
    mock_results = [
        {
            "title": "MacBook Pro M3 16\" - Best Price",
            "price": "$2,399",
            "url": "https://amazon.com/macbook",
            "store": "Amazon",
            "discount": "15%"
        },
        {
            "title": "MacBook Pro M3 14\" Deal",
            "price": "$1,799",
            "url": "https://bestbuy.com/macbook",
            "store": "Best Buy",
            "discount": "10%"
        }
    ]
    print(f"  → Found {len(mock_results)} deals\n")
    
    # Step 3: Add freshness metadata
    print("Step 3: Adding Freshness Metadata")
    results_with_metadata = manager.add_freshness_metadata(mock_results.copy(), query)
    
    for i, result in enumerate(results_with_metadata, 1):
        print(f"  Deal {i}: {result['title']}")
        meta = result['freshness_metadata']
        print(f"    • Category: {meta['category']}")
        print(f"    • Price-sensitive: {meta['is_price_sensitive']}")
        print(f"    • Refresh after: {meta['recommended_refresh_hours']}h")
        print(f"    • Max age: {meta['max_age_hours']}h")
    
    print()
    
    # Step 4: Cache with optimal TTL
    print("Step 4: Caching Results")
    cache_key = "demo_macbook_search"
    cache_data = {
        "timestamp": datetime.now().timestamp(),
        "query": query,
        "results": results_with_metadata
    }
    
    # Store in Redis
    redis_client.set(
        f"search:{cache_key}",
        json.dumps(cache_data),
        ex=int(optimal_ttl)
    )
    
    print(f"  → Cached {len(results_with_metadata)} deals")
    print(f"  → TTL: {optimal_ttl/3600:.0f} hours (expires: {datetime.now() + timedelta(seconds=optimal_ttl)})")
    print(f"  → Reason: {'Price-sensitive query' if is_price_sensitive else f'{category} category'}\n")
    
    # Step 5: Validate on retrieval
    print("Step 5: Validation on Next Search (simulated)")
    
    # Simulate immediate retrieval
    print("\n  Scenario A: User searches again 1 hour later")
    validity = manager.check_deals_validity(cache_data)
    print(f"    → Status: {validity['action']}")
    print(f"    → Freshness: {validity['reason']}")
    print(f"    → Result: ✅ Use cached deals (still fresh)")
    
    # Simulate retrieval after TTL
    print("\n  Scenario B: User searches again 5 hours later")
    old_cache_data = cache_data.copy()
    old_cache_data["timestamp"] = datetime.now().timestamp() - (5 * 3600)
    validity = manager.check_deals_validity(old_cache_data)
    print(f"    → Status: {validity['action']}")
    print(f"    → Reason: {validity['reason']}")
    print(f"    → Result: 🔄 Refresh required (exceeded {optimal_ttl/3600:.0f}h limit)")
    
    # Cleanup
    redis_client.delete(f"search:{cache_key}")

def main():
    """Run all demos"""
    print_box("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║           🎯 24-HOUR DEAL FRESHNESS SYSTEM - INTERACTIVE DEMO                ║
║                                                                               ║
║  Ensuring Fresh, Accurate, and Trustworthy E-Commerce Deals                  ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """, "blue")
    
    print(f"Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        demo_category_detection()
        input("\nPress Enter to continue to Demo 2...")
        
        demo_price_sensitivity()
        input("\nPress Enter to continue to Demo 3...")
        
        demo_freshness_lifecycle()
        input("\nPress Enter to continue to Demo 4...")
        
        demo_category_ttl()
        input("\nPress Enter to continue to Demo 5...")
        
        demo_real_world_scenario()
        
        print_header("✅ Demo Complete!")
        print_box("""
The 24-Hour Deal Freshness System ensures:

✓ Deals are never older than 24 hours
✓ Category-specific refresh intervals (4-24 hours)
✓ Price-sensitive queries get 4-hour maximum TTL
✓ Automatic freshness validation on every cache hit
✓ Clear warnings when deals approach staleness
✓ Optimal balance between cache efficiency and data freshness

Your users will always see accurate, up-to-date deals! 🎉
        """, "green")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
