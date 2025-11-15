#!/usr/bin/env python3
"""
Comprehensive Test for 24-Hour Deal Freshness System
Tests all aspects of the deal freshness validation and cache invalidation
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.deal_freshness import DealFreshnessManager, get_deal_freshness_manager
from utils.redis_client import get_redis_client
from utils.cache import CacheManager

def print_separator(title=""):
    """Print a visual separator"""
    print("\n" + "="*80)
    if title:
        print(f"  {title}")
        print("="*80)

def print_test_result(test_name, passed, details=""):
    """Print test result"""
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"{status}: {test_name}")
    if details:
        print(f"  Details: {details}")

def test_category_detection():
    """Test category detection from queries"""
    print_separator("Test 1: Category Detection")
    
    manager = get_deal_freshness_manager()
    
    test_cases = [
        ("iPhone 15 Pro", "electronics"),
        ("Nintendo Switch OLED", "gaming"),
        ("Running shoes Nike", "fashion"),
        ("Kitchen appliance", "home"),
        ("Microsoft Office license", "software"),
        ("Yoga mat fitness", "sports"),
        ("Random product", "default")
    ]
    
    all_passed = True
    for query, expected_category in test_cases:
        detected = manager._detect_category(query)
        passed = detected == expected_category
        all_passed = all_passed and passed
        print_test_result(
            f"Category for '{query}'",
            passed,
            f"Expected: {expected_category}, Got: {detected}"
        )
    
    return all_passed

def test_price_sensitivity_detection():
    """Test price-sensitive query detection"""
    print_separator("Test 2: Price-Sensitive Query Detection")
    
    manager = get_deal_freshness_manager()
    
    sensitive_queries = [
        "cheapest iPhone deals",
        "best deal on MacBook",
        "hot deal Nintendo Switch",
        "bargain laptop"
    ]
    
    normal_queries = [
        "iPhone 15 Pro",
        "MacBook Pro review",
        "Nintendo Switch games"
    ]
    
    all_passed = True
    
    for query in sensitive_queries:
        is_sensitive = manager._is_price_sensitive(query)
        passed = is_sensitive == True
        all_passed = all_passed and passed
        print_test_result(
            f"'{query}' is price-sensitive",
            passed,
            f"Result: {is_sensitive}"
        )
    
    for query in normal_queries:
        is_sensitive = manager._is_price_sensitive(query)
        passed = is_sensitive == False
        all_passed = all_passed and passed
        print_test_result(
            f"'{query}' is NOT price-sensitive",
            passed,
            f"Result: {is_sensitive}"
        )
    
    return all_passed

def test_optimal_ttl_calculation():
    """Test optimal TTL calculation"""
    print_separator("Test 3: Optimal TTL Calculation")
    
    manager = get_deal_freshness_manager()
    
    test_cases = [
        ("iPhone 15 deals", "electronics", 4 * 3600),  # 4 hours for electronics
        ("Nintendo Switch", "gaming", 8 * 3600),        # 8 hours for gaming
        ("cheapest MacBook", None, 4 * 3600),          # Price-sensitive: 4 hours
        ("Running shoes", "fashion", 12 * 3600),       # 12 hours for fashion
        ("Random product", None, 24 * 3600)            # Default: 24 hours
    ]
    
    all_passed = True
    for query, category, expected_ttl in test_cases:
        ttl = manager.get_optimal_ttl(query, category)
        passed = ttl == expected_ttl
        all_passed = all_passed and passed
        print_test_result(
            f"TTL for '{query}'",
            passed,
            f"Expected: {expected_ttl/3600}h, Got: {ttl/3600}h"
        )
    
    return all_passed

def test_freshness_metadata():
    """Test adding freshness metadata to results"""
    print_separator("Test 4: Freshness Metadata Addition")
    
    manager = get_deal_freshness_manager()
    
    test_results = [
        {
            "title": "iPhone 15 Pro Deal",
            "price": "$999",
            "url": "https://example.com/iphone"
        },
        {
            "title": "MacBook Pro M3",
            "price": "$1999",
            "url": "https://example.com/macbook"
        }
    ]
    
    query = "iPhone 15 Pro deals"
    results_with_metadata = manager.add_freshness_metadata(test_results.copy(), query)
    
    all_passed = True
    
    # Check if metadata was added
    has_metadata = all("freshness_metadata" in result for result in results_with_metadata)
    print_test_result("Metadata added to all results", has_metadata)
    all_passed = all_passed and has_metadata
    
    if has_metadata:
        metadata = results_with_metadata[0]["freshness_metadata"]
        
        # Check metadata fields
        required_fields = ["cached_at", "category", "is_price_sensitive", 
                          "recommended_refresh_hours", "max_age_hours"]
        
        for field in required_fields:
            has_field = field in metadata
            print_test_result(f"Metadata has '{field}' field", has_field)
            all_passed = all_passed and has_field
        
        # Verify values
        category_correct = metadata.get("category") == "electronics"
        print_test_result(
            "Category is 'electronics'",
            category_correct,
            f"Got: {metadata.get('category')}"
        )
        all_passed = all_passed and category_correct
        
        max_age_correct = metadata.get("max_age_hours") == 24
        print_test_result(
            "Max age is 24 hours",
            max_age_correct,
            f"Got: {metadata.get('max_age_hours')}"
        )
        all_passed = all_passed and max_age_correct
    
    return all_passed

def test_cache_freshness_validation():
    """Test cache freshness validation with simulated cache ages"""
    print_separator("Test 5: Cache Freshness Validation (24-Hour Rule)")
    
    manager = get_deal_freshness_manager()
    redis_client = get_redis_client()
    
    # Test different cache ages
    test_cases = [
        ("Fresh cache (2 hours old)", 2, True, "fresh", "use_cache"),
        ("Good cache (10 hours old)", 10, True, "good", "use_cache"),
        ("Stale cache (20 hours old)", 20, True, "stale", "use_cache"),
        ("Expired cache (25 hours old)", 25, False, "expired", "refresh_required"),
        ("Very old cache (48 hours old)", 48, False, "expired", "refresh_required")
    ]
    
    all_passed = True
    
    for test_name, age_hours, expected_valid, expected_status, expected_action in test_cases:
        # Create simulated cached data
        timestamp = datetime.now().timestamp() - (age_hours * 3600)
        cached_data = {
            "timestamp": timestamp,
            "results": [
                {
                    "title": "Test Deal",
                    "price": "$99",
                    "freshness_metadata": {
                        "cached_at": timestamp,
                        "category": "electronics",
                        "recommended_refresh_hours": 24,
                        "max_age_hours": 24
                    }
                }
            ]
        }
        
        # Validate freshness
        validity = manager.check_deals_validity(cached_data)
        
        # Check results
        valid_correct = validity["valid"] == expected_valid
        action_correct = validity["action"] == expected_action
        
        passed = valid_correct and action_correct
        all_passed = all_passed and passed
        
        print_test_result(
            test_name,
            passed,
            f"Age: {age_hours}h, Valid: {validity['valid']}, Action: {validity['action']}"
        )
        
        if validity.get("warning"):
            print(f"    Warning: {validity['warning']}")
    
    return all_passed

def test_should_refresh_cache():
    """Test should_refresh_cache decision logic"""
    print_separator("Test 6: Should Refresh Cache Decision")
    
    manager = get_deal_freshness_manager()
    redis_client = get_redis_client()
    
    # Create test cache entries with different ages
    test_queries = [
        ("test_fresh_electronics", "iPhone deals", 2, False),    # 2h old - should NOT refresh
        ("test_stale_electronics", "MacBook deals", 5, True),    # 5h old electronics - should refresh (>4h)
        ("test_expired_gaming", "Nintendo Switch", 25, True),    # 25h old - should refresh (>24h)
        ("test_price_sensitive", "cheapest laptop", 5, True)     # 5h old price-sensitive - should refresh (>4h)
    ]
    
    all_passed = True
    
    for cache_key, query, age_hours, should_refresh in test_queries:
        # Create cached data
        timestamp = datetime.now().timestamp() - (age_hours * 3600)
        cached_data = {
            "timestamp": timestamp,
            "query": query,
            "results": [{"title": "Test Deal"}]
        }
        
        # Store in Redis
        full_key = f"search:{cache_key}"
        redis_client.set(full_key, json.dumps(cached_data), ex=86400)
        
        # Test refresh decision
        decision = manager.should_refresh_cache(query)
        
        passed = decision["should_refresh"] == should_refresh
        all_passed = all_passed and passed
        
        print_test_result(
            f"Query: '{query}' ({age_hours}h old)",
            passed,
            f"Should refresh: {should_refresh}, Decision: {decision['should_refresh']}, Reason: {decision['reason']}"
        )
        
        # Cleanup
        redis_client.delete(full_key)
    
    return all_passed

def test_integration_with_search():
    """Test integration with search agent flow"""
    print_separator("Test 7: Integration with Search Flow")
    
    manager = get_deal_freshness_manager()
    cache_manager = CacheManager()
    
    # Simulate a search result
    test_query = "iPhone 15 Pro"
    test_results = [
        {
            "title": "iPhone 15 Pro - Best Deal",
            "price": "$999",
            "url": "https://example.com/iphone",
            "store": "Amazon"
        }
    ]
    
    # Step 1: Add freshness metadata
    results_with_metadata = manager.add_freshness_metadata(test_results.copy(), test_query)
    metadata_added = "freshness_metadata" in results_with_metadata[0]
    print_test_result("Step 1: Freshness metadata added", metadata_added)
    
    # Step 2: Calculate optimal TTL
    optimal_ttl = manager.get_optimal_ttl(test_query)
    ttl_correct = optimal_ttl == 4 * 3600  # Electronics should be 4 hours
    print_test_result(
        "Step 2: Optimal TTL calculated",
        ttl_correct,
        f"TTL: {optimal_ttl/3600}h (expected 4h for electronics)"
    )
    
    # Step 3: Cache with optimal TTL
    cache_key = f"integration_test_{test_query}"
    cache_data = {
        "timestamp": datetime.now().timestamp(),
        "query": test_query,
        "results": results_with_metadata
    }
    cache_manager.cache_search_results(cache_key, results_with_metadata, ttl=optimal_ttl)
    print_test_result("Step 3: Results cached with optimal TTL", True)
    
    # Step 4: Validate freshness on retrieval
    cached_results = cache_manager.get_cached_search(cache_key)
    if cached_results:
        validity = manager.check_deals_validity(cached_results)
        should_use = validity["action"] == "use_cache"
        print_test_result(
            "Step 4: Freshness validation on retrieval",
            should_use,
            f"Action: {validity['action']}, Age: {validity['age_hours']:.2f}h"
        )
    else:
        print_test_result("Step 4: Freshness validation on retrieval", False, "No cached data found")
        should_use = False
    
    all_passed = metadata_added and ttl_correct and should_use
    return all_passed

def run_all_tests():
    """Run all tests and print summary"""
    print_separator("🧪 24-HOUR DEAL FRESHNESS SYSTEM - COMPREHENSIVE TEST SUITE")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Category Detection", test_category_detection),
        ("Price Sensitivity Detection", test_price_sensitivity_detection),
        ("Optimal TTL Calculation", test_optimal_ttl_calculation),
        ("Freshness Metadata Addition", test_freshness_metadata),
        ("Cache Freshness Validation", test_cache_freshness_validation),
        ("Should Refresh Cache Decision", test_should_refresh_cache),
        ("Integration with Search Flow", test_integration_with_search)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed, None))
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"\n❌ Test '{test_name}' failed with exception: {e}")
    
    # Print summary
    print_separator("📊 TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, passed, _ in results if passed)
    failed_tests = total_tests - passed_tests
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, passed, error in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status}: {test_name}")
        if error:
            print(f"    Error: {error}")
    
    print_separator()
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! 24-hour deal freshness system is working correctly!")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
