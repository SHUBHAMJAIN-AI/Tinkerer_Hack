#!/usr/bin/env python3
"""
Test Deal Freshness System
Validates 24-hour deal freshness implementation
"""

import json
import time
from datetime import datetime, timedelta
from utils.deal_freshness import get_deal_freshness_manager
from utils.cache import CacheManager
from utils.redis_client import get_redis_client

def test_deal_freshness():
    """Test the 24-hour deal freshness system"""
    
    print("="*60)
    print("🧪 Testing 24-Hour Deal Freshness System")
    print("="*60)
    
    freshness_manager = get_deal_freshness_manager()
    cache_manager = CacheManager()
    redis_client = get_redis_client()
    
    # Test 1: Category Detection
    print("\n📋 Test 1: Category Detection")
    print("-" * 60)
    test_queries = [
        ("Nintendo Switch deals", "gaming"),
        ("iPhone 15 cheap", "electronics"),
        ("MacBook Pro discount", "electronics"),
        ("Nike shoes sale", "fashion"),
        ("Microsoft Office license", "software"),
    ]
    
    for query, expected_category in test_queries:
        detected = freshness_manager._detect_category(query)
        status = "✅" if detected == expected_category else "❌"
        print(f"{status} '{query}' -> {detected} (expected: {expected_category})")
    
    # Test 2: Price Sensitivity Detection
    print("\n💰 Test 2: Price-Sensitive Query Detection")
    print("-" * 60)
    price_sensitive_queries = [
        "cheapest iPhone",
        "best deal MacBook",
        "lowest price Nintendo Switch",
        "budget laptop",
    ]
    
    for query in price_sensitive_queries:
        is_sensitive = freshness_manager._is_price_sensitive(query)
        status = "✅" if is_sensitive else "❌"
        print(f"{status} '{query}' -> Price-sensitive: {is_sensitive}")
    
    # Test 3: Optimal TTL Calculation
    print("\n⏰ Test 3: Optimal TTL Calculation")
    print("-" * 60)
    for query, expected_category in test_queries:
        ttl_seconds = freshness_manager.get_optimal_ttl(query)
        ttl_hours = ttl_seconds / 3600
        print(f"'{query}' -> {ttl_hours:.1f} hours TTL")
    
    # Test 4: Freshness Metadata
    print("\n📊 Test 4: Freshness Metadata Addition")
    print("-" * 60)
    sample_results = [
        {"title": "Nintendo Switch OLED", "price": "$299", "store": "Best Buy"},
        {"title": "Nintendo Switch Lite", "price": "$199", "store": "Amazon"},
    ]
    
    query = "Nintendo Switch deals"
    results_with_metadata = freshness_manager.add_freshness_metadata(
        sample_results, query
    )
    
    if results_with_metadata[0].get("freshness_metadata"):
        print("✅ Metadata added successfully:")
        metadata = results_with_metadata[0]["freshness_metadata"]
        print(f"   - Category: {metadata['category']}")
        print(f"   - Price Sensitive: {metadata['is_price_sensitive']}")
        print(f"   - Recommended Refresh: {metadata['recommended_refresh_hours']}h")
        print(f"   - Max Age: {metadata['max_age_hours']}h")
    else:
        print("❌ Failed to add metadata")
    
    # Test 5: Cache Freshness Check (simulate old cache)
    print("\n🔍 Test 5: Cache Freshness Validation")
    print("-" * 60)
    
    # Simulate cached data at different ages
    current_time = datetime.now().timestamp()
    test_cases = [
        ("Fresh cache (2h old)", current_time - (2 * 3600), "fresh"),
        ("Good cache (10h old)", current_time - (10 * 3600), "good"),
        ("Stale cache (20h old)", current_time - (20 * 3600), "stale"),
        ("Expired cache (25h old)", current_time - (25 * 3600), "expired"),
    ]
    
    for description, timestamp, expected_status in test_cases:
        cached_data = {
            "results": sample_results,
            "timestamp": timestamp,
            "query": "test query"
        }
        
        validity = freshness_manager.check_deals_validity(cached_data)
        age_hours = validity["age_hours"]
        status = "✅" if validity["action"] == "use_cache" or validity["action"] == "consider_refresh" else "⚠️ REFRESH"
        
        print(f"{status} {description}:")
        print(f"    Age: {age_hours:.1f}h | Action: {validity['action']}")
        if validity.get("warning"):
            print(f"    Warning: {validity['warning']}")
    
    # Test 6: Should Refresh Cache Decision
    print("\n🔄 Test 6: Should Refresh Cache Decision")
    print("-" * 60)
    
    # Create test cached data
    test_query = "iPhone 15 deals"
    cache_key = freshness_manager._get_cache_key(test_query)
    
    # Store fresh data
    test_data = {
        "results": [{"title": "iPhone 15", "price": "$799"}],
        "timestamp": current_time,
        "query": test_query
    }
    
    redis_client.set(cache_key, json.dumps(test_data), ex=86400)
    
    # Check if should refresh
    decision = freshness_manager.should_refresh_cache(test_query, category="electronics")
    
    print(f"Query: '{test_query}'")
    print(f"Should Refresh: {decision['should_refresh']}")
    print(f"Reason: {decision['reason']}")
    print(f"Age: {decision['age_hours']:.2f}h")
    print(f"Freshness Level: {decision['freshness_level']}")
    
    # Test 7: Category-Specific Thresholds
    print("\n⚙️  Test 7: Category-Specific Thresholds")
    print("-" * 60)
    
    for category, threshold in freshness_manager.CATEGORY_THRESHOLDS.items():
        print(f"{category.capitalize()}: {threshold}h refresh threshold")
    
    # Cleanup
    redis_client.delete(cache_key)
    
    print("\n" + "="*60)
    print("✅ Deal Freshness System Test Complete!")
    print("="*60)


def test_integration_with_search():
    """Test integration with search agent"""
    
    print("\n" + "="*60)
    print("🔗 Testing Integration with Search Agent")
    print("="*60)
    
    from nodes.search_agent import search_for_deals
    
    # Test fresh search
    print("\n🔍 Test: Fresh Search (No Cache)")
    print("-" * 60)
    
    query = "Nintendo Switch OLED test"
    result = search_for_deals(query, max_price=350.0, category="gaming")
    
    if "[FRESH SEARCH]" in result or "results" in result.lower():
        print("✅ Fresh search executed successfully")
    else:
        print("❌ Fresh search failed")
    
    print(f"Result preview: {result[:200]}...")
    
    # Wait and test cached search
    print("\n💾 Test: Cached Search (Immediate Re-query)")
    print("-" * 60)
    
    time.sleep(1)
    result2 = search_for_deals(query, max_price=350.0, category="gaming")
    
    if "[CACHED" in result2:
        print("✅ Cache hit detected")
    else:
        print("⚠️ Expected cache hit but got fresh search")
    
    print(f"Result preview: {result2[:200]}...")


if __name__ == "__main__":
    try:
        test_deal_freshness()
        # Uncomment to test integration (requires Tavily API key)
        # test_integration_with_search()
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
