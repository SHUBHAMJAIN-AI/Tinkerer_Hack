"""
Test Product Query Detection
Diagnose why "tell me about deal 3" isn't being detected
"""

import sys
import os

# Add agent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import get_session_manager
import re

def test_product_query_detection():
    """Test if product queries are detected correctly"""
    
    print("=" * 80)
    print("🧪 PRODUCT QUERY DETECTION TEST")
    print("=" * 80)
    
    # Test queries
    test_queries = [
        "tell me about deal 3",
        "tell me about #3",
        "what about product 2",
        "compare #1 and #2",
        "the cheapest one",
        "give me expensive iphone",  # Should NOT match (it's a search query)
    ]
    
    # Product reference patterns
    product_patterns = [
        r'#\d+',  # #1, #2, etc.
        r'\bproduct\s+\d+',  # product 1, product 2
        r'\bnumber\s+\d+',  # number 1, number 2
        r'\bdeal\s+\d+',  # deal 1, deal 2 - MISSING!
        r'\bfirst\s+one\b',  # first one
        r'\bsecond\s+one\b',  # second one
        r'\bthird\s+one\b',  # third one
        r'\btop\s+one\b',  # top one
        r'\bcheapest\b',  # cheapest
        r'\bmost\s+expensive\b',  # most expensive
    ]
    
    follow_up_patterns = [
        'tell me about',
        'tell me more',
        'what about',
        'how about',
        'details on',
        'info on',
        'information about',
        'compare',
        'vs',
        'versus',
        'difference between',
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        query_lower = query.lower()
        
        # Check product patterns
        pattern_matches = []
        for pattern in product_patterns:
            if re.search(pattern, query_lower):
                pattern_matches.append(pattern)
        
        # Check follow-up patterns
        followup_matches = []
        for pattern in follow_up_patterns:
            if pattern in query_lower:
                followup_matches.append(pattern)
        
        is_product_query = len(pattern_matches) > 0 or len(followup_matches) > 0
        
        if is_product_query:
            print(f"   ✅ DETECTED as product query")
            if pattern_matches:
                print(f"      - Pattern matches: {pattern_matches}")
            if followup_matches:
                print(f"      - Follow-up matches: {followup_matches}")
        else:
            print(f"   ❌ NOT DETECTED")
    
    print("\n" + "=" * 80)
    print("🔍 ISSUE FOUND:")
    print("   The pattern 'deal \\d+' is MISSING from product_patterns!")
    print("   Users can say 'deal 3' but it won't be detected.")
    print("=" * 80)


if __name__ == "__main__":
    test_product_query_detection()
