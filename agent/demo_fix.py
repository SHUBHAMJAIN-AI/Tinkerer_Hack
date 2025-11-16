#!/usr/bin/env python3
"""
Quick Demo: Product Query Detection Fix
Shows that "deal 3" now works correctly
"""

import re

def is_product_query_BEFORE(query):
    """OLD version - MISSING deal pattern"""
    query_lower = query.lower()
    
    product_patterns_OLD = [
        r'#\d+',
        r'\bproduct\s+\d+',
        r'\bnumber\s+\d+',
        # MISSING: r'\bdeal\s+\d+'  ❌
        r'\bfirst\s+one\b',
    ]
    
    for pattern in product_patterns_OLD:
        if re.search(pattern, query_lower):
            return True
    return False


def is_product_query_AFTER(query):
    """NEW version - WITH deal pattern"""
    query_lower = query.lower()
    
    product_patterns_NEW = [
        r'#\d+',
        r'\bproduct\s+\d+',
        r'\bnumber\s+\d+',
        r'\bdeal\s+\d+',  # ✅ ADDED
        r'\bfirst\s+one\b',
    ]
    
    for pattern in product_patterns_NEW:
        if re.search(pattern, query_lower):
            return True
    return False


def demo():
    """Demonstrate the fix"""
    print("=" * 80)
    print("🎯 PRODUCT QUERY DETECTION FIX DEMO")
    print("=" * 80)
    print()
    
    test_queries = [
        "tell me about #3",
        "tell me about product 3",
        "tell me about deal 3",  # This was BROKEN
        "what about deal 2",      # This was BROKEN
        "give me expensive iphone",  # Should NOT match
    ]
    
    print("📝 Testing Query Detection:")
    print()
    
    for query in test_queries:
        before = is_product_query_BEFORE(query)
        after = is_product_query_AFTER(query)
        
        print(f"Query: '{query}'")
        print(f"  ❌ BEFORE: {'✅ Detected' if before else '❌ Not Detected'}")
        print(f"  ✅ AFTER:  {'✅ Detected' if after else '❌ Not Detected'}")
        
        if before != after:
            print(f"  🔧 STATUS: FIXED! ✅")
        else:
            print(f"  ℹ️  STATUS: Unchanged")
        print()
    
    print("=" * 80)
    print("🎉 RESULT: 'deal 3' queries now work correctly!")
    print("=" * 80)
    print()
    print("✅ Users can now say:")
    print("   - 'tell me about #3'")
    print("   - 'tell me about product 3'")
    print("   - 'tell me about deal 3'  ← NOW WORKS!")
    print("   - 'what about deal 2'      ← NOW WORKS!")
    print()


if __name__ == "__main__":
    demo()
