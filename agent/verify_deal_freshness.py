#!/usr/bin/env python3
"""
Quick Verification Script for 24-Hour Deal Freshness System
Run this to confirm the implementation is working correctly
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_imports():
    """Verify all necessary imports work"""
    print("🔍 Verifying imports...")
    try:
        from utils.deal_freshness import DealFreshnessManager, get_deal_freshness_manager
        from utils import get_deal_freshness_manager as utils_import
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def verify_manager_creation():
    """Verify manager can be created"""
    print("\n🔍 Verifying manager creation...")
    try:
        from utils.deal_freshness import get_deal_freshness_manager
        manager = get_deal_freshness_manager()
        print(f"✅ Manager created: {type(manager)}")
        return True, manager
    except Exception as e:
        print(f"❌ Error creating manager: {e}")
        return False, None

def verify_methods(manager):
    """Verify all key methods exist"""
    print("\n🔍 Verifying methods...")
    
    methods = [
        'should_refresh_cache',
        'check_deals_validity',
        'get_optimal_ttl',
        'add_freshness_metadata',
        '_detect_category',
        '_is_price_sensitive',
        '_get_freshness_status',
        '_get_cache_key'
    ]
    
    all_exist = True
    for method in methods:
        if hasattr(manager, method):
            print(f"  ✅ {method}")
        else:
            print(f"  ❌ {method} - MISSING")
            all_exist = False
    
    return all_exist

def verify_category_detection(manager):
    """Verify category detection works"""
    print("\n🔍 Verifying category detection...")
    
    tests = [
        ("iPhone 15 Pro", "electronics"),
        ("Nintendo Switch", "gaming"),
        ("Running shoes", "fashion")
    ]
    
    all_correct = True
    for query, expected in tests:
        result = manager._detect_category(query)
        if result == expected:
            print(f"  ✅ '{query}' → {result}")
        else:
            print(f"  ❌ '{query}' → {result} (expected {expected})")
            all_correct = False
    
    return all_correct

def verify_ttl_calculation(manager):
    """Verify TTL calculation works"""
    print("\n🔍 Verifying TTL calculation...")
    
    try:
        ttl_electronics = manager.get_optimal_ttl("iPhone deals")
        ttl_gaming = manager.get_optimal_ttl("Nintendo Switch")
        ttl_price_sensitive = manager.get_optimal_ttl("cheapest laptop")
        
        print(f"  ✅ Electronics TTL: {ttl_electronics/3600}h")
        print(f"  ✅ Gaming TTL: {ttl_gaming/3600}h")
        print(f"  ✅ Price-sensitive TTL: {ttl_price_sensitive/3600}h")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def verify_metadata_addition(manager):
    """Verify metadata can be added to results"""
    print("\n🔍 Verifying metadata addition...")
    
    try:
        test_results = [
            {"title": "iPhone 15 Pro", "price": "$999"}
        ]
        
        results_with_meta = manager.add_freshness_metadata(test_results, "iPhone deals")
        
        if "freshness_metadata" in results_with_meta[0]:
            meta = results_with_meta[0]["freshness_metadata"]
            print(f"  ✅ Metadata added")
            print(f"    - Category: {meta.get('category')}")
            print(f"    - Price-sensitive: {meta.get('is_price_sensitive')}")
            print(f"    - Max age: {meta.get('max_age_hours')}h")
            return True
        else:
            print(f"  ❌ Metadata not added")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def verify_search_agent_integration():
    """Verify search agent has the integration"""
    print("\n🔍 Verifying search agent integration...")
    
    try:
        with open('nodes/search_agent.py', 'r') as f:
            content = f.read()
            
        checks = [
            ('get_deal_freshness_manager', 'Import statement'),
            ('freshness_manager', 'Manager usage'),
            ('check_deals_validity', 'Validity check'),
            ('add_freshness_metadata', 'Metadata addition'),
            ('get_optimal_ttl', 'TTL calculation')
        ]
        
        all_found = True
        for check, description in checks:
            if check in content:
                print(f"  ✅ {description} found")
            else:
                print(f"  ❌ {description} NOT found")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Run all verifications"""
    print("="*80)
    print("  24-HOUR DEAL FRESHNESS SYSTEM - VERIFICATION")
    print("="*80)
    
    results = []
    
    # Run all checks
    results.append(("Imports", verify_imports()))
    
    success, manager = verify_manager_creation()
    results.append(("Manager Creation", success))
    
    if manager:
        results.append(("Methods Exist", verify_methods(manager)))
        results.append(("Category Detection", verify_category_detection(manager)))
        results.append(("TTL Calculation", verify_ttl_calculation(manager)))
        results.append(("Metadata Addition", verify_metadata_addition(manager)))
    else:
        print("\n⚠️ Skipping remaining tests (manager creation failed)")
    
    results.append(("Search Agent Integration", verify_search_agent_integration()))
    
    # Print summary
    print("\n" + "="*80)
    print("  VERIFICATION SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL VERIFICATIONS PASSED!")
        print("\nThe 24-hour deal freshness system is fully implemented and ready to use.")
        print("\nNext steps:")
        print("  1. Run tests: python test_deal_freshness_system.py")
        print("  2. Run demo: python demo_deal_freshness.py")
        print("  3. Test with real queries in the agent")
        return 0
    else:
        print(f"\n⚠️ {total - passed} verification(s) failed.")
        print("Please review the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
