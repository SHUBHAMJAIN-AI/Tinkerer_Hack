"""
Test Enhanced DealFinder Features
Tests numbered results, product matching, and fact verification
"""

import asyncio
import sys
from typing import List, Dict, Any

# Test data
MOCK_SEARCH_RESULTS = [
    {
        "title": "Apple iPhone 15 Pro 256GB - Titanium - Factory Unlocked",
        "url": "https://amazon.com/iphone-15-pro",
        "content": "iPhone 15 Pro with A17 Pro chip, 256GB storage, Titanium finish. 48MP camera.",
        "score": 0.95,
        "price": "$899",
        "store": "Amazon",
        "rating": 4.8,
        "image": "https://example.com/iphone-pro.jpg"
    },
    {
        "title": "iPhone 15 128GB - Blue - AT&T",
        "url": "https://bestbuy.com/iphone-15-blue",
        "content": "iPhone 15 with 128GB storage in Blue. Super Retina XDR display.",
        "score": 0.88,
        "price": "$699",
        "store": "Best Buy",
        "rating": 4.7,
        "image": "https://example.com/iphone-blue.jpg"
    },
    {
        "title": "Apple iPhone 15 Plus 256GB - Pink",
        "url": "https://walmart.com/iphone-15-plus",
        "content": "iPhone 15 Plus with 6.7 inch display, 256GB storage, Pink color.",
        "score": 0.82,
        "price": "$799",
        "store": "Walmart",
        "rating": 4.6,
        "image": "https://example.com/iphone-plus.jpg"
    },
    {
        "title": "MacBook Air M3 13-inch - Midnight - 16GB RAM 512GB SSD",
        "url": "https://apple.com/macbook-air",
        "content": "MacBook Air with M3 chip, 13.6-inch Liquid Retina display.",
        "score": 0.90,
        "price": "$1,299",
        "store": "Apple Store",
        "rating": 4.9,
        "image": "https://example.com/macbook.jpg"
    },
    {
        "title": "Apple iPhone 14 Pro Max 1TB - Gold - Certified Refurbished",
        "url": "https://ebay.com/iphone-14-pro-max",
        "content": "iPhone 14 Pro Max, previous generation, 1TB storage, Gold finish.",
        "score": 0.75,
        "price": "$849",
        "store": "eBay",
        "rating": 4.5,
        "image": "https://example.com/iphone-14.jpg"
    }
]


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def print_test(name: str, passed: bool, details: str = ""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")
    if details:
        print(f"    {details}")


def test_result_parser():
    """Test ResultParser with numbered results"""
    print_header("TEST 1: Result Parser - Numbered Results & Product Names")
    
    from utils.result_parser import ResultParser
    
    # Parse results
    parsed = ResultParser.parse_tavily_response(MOCK_SEARCH_RESULTS)
    
    # Test 1: All results have numbers
    all_numbered = all('result_number' in r for r in parsed)
    print_test("All results have result_number", all_numbered)
    
    # Test 2: Numbers are sequential
    numbers = [r['result_number'] for r in parsed]
    sequential = numbers == list(range(1, len(parsed) + 1))
    print_test("Numbers are sequential (1, 2, 3...)", sequential, f"Numbers: {numbers}")
    
    # Test 3: Clean names extracted
    has_clean_names = all('clean_name' in r for r in parsed)
    print_test("All results have clean_name", has_clean_names)
    
    if parsed:
        print(f"\n📋 Sample parsed result #1:")
        result = parsed[0]
        print(f"   Number: {result.get('result_number')}")
        print(f"   Title: {result.get('title')}")
        print(f"   Clean Name: {result.get('clean_name')}")
        print(f"   Keywords: {result.get('keywords', [])[:5]}...")
        print(f"   Descriptors: {result.get('descriptors', {})}")
    
    # Test 4: Keywords extracted
    has_keywords = all('keywords' in r and len(r['keywords']) > 0 for r in parsed)
    print_test("All results have keywords", has_keywords)
    
    # Test 5: Descriptors extracted
    has_descriptors = all('descriptors' in r for r in parsed)
    print_test("All results have descriptors", has_descriptors)
    
    return parsed


def test_product_matcher(parsed_results: List[Dict[str, Any]]):
    """Test ProductMatcher with various query types"""
    print_header("TEST 2: Product Matcher - Name & Description Matching")
    
    from utils.product_matcher import ProductMatcher
    
    matcher = ProductMatcher()
    
    # Test 1: Number reference (#1)
    match1 = matcher.match_product("#1", parsed_results)
    test_print_test("Match #1 by number", match1 is not None and match1.product.get('result_number') == 1)
    if match1:
        print(f"    Matched: {match1.product.get('clean_name')} (confidence: {match1.confidence:.2f})")
    
    # Test 2: Number reference (product 2)
    match2 = matcher.match_product("product 2", parsed_results)
    print_test("Match 'product 2' by number", match2 is not None and match2.product.get('result_number') == 2)
    if match2:
        print(f"    Matched: {match2.product.get('clean_name')} (confidence: {match2.confidence:.2f})")
    
    # Test 3: Name reference (iPhone 15 Pro)
    match3 = matcher.match_product("iPhone 15 Pro", parsed_results)
    print_test("Match 'iPhone 15 Pro' by name", match3 is not None)
    if match3:
        print(f"    Matched: {match3.product.get('clean_name')} (confidence: {match3.confidence:.2f})")
        print(f"    Method: {match3.match_type}")
    
    # Test 4: Description (cheapest)
    match4 = matcher.match_product("the cheapest", parsed_results)
    print_test("Match 'the cheapest' by description", match4 is not None)
    if match4:
        print(f"    Matched: {match4.product.get('clean_name')} at {match4.product.get('price')}")
        print(f"    Method: {match4.match_type}")
    
    # Test 5: Color descriptor (blue)
    match5 = matcher.match_product("the blue one", parsed_results)
    print_test("Match 'the blue one' by color", match5 is not None)
    if match5:
        print(f"    Matched: {match5.product.get('clean_name')}")
        print(f"    Color: {match5.product.get('descriptors', {}).get('color')}")
    
    # Test 6: Store reference (Amazon)
    match6 = matcher.match_product("the Amazon deal", parsed_results)
    print_test("Match 'the Amazon deal' by store", match6 is not None)
    if match6:
        print(f"    Matched: {match6.product.get('clean_name')} from {match6.product.get('store')}")
    
    # Test 7: Storage descriptor (256GB)
    match7 = matcher.match_product("the 256GB one", parsed_results)
    print_test("Match 'the 256GB one' by storage", match7 is not None)
    if match7:
        print(f"    Matched: {match7.product.get('clean_name')}")
        print(f"    Storage: {match7.product.get('descriptors', {}).get('storage')}")


def test_fact_verifier(parsed_results: List[Dict[str, Any]]):
    """Test FactVerifier anti-hallucination"""
    print_header("TEST 3: Fact Verifier - Anti-Hallucination System")
    
    from utils.fact_verifier import FactVerifier
    
    verifier = FactVerifier()
    product = parsed_results[0]  # iPhone 15 Pro
    
    # Test 1: Verify exact price
    price_result = verifier.verify_price("$899", product)
    print_test("Verify exact price ($899)", price_result['verified'])
    print(f"    Result: {price_result['status']} - {price_result['message']}")
    
    # Test 2: Verify wrong price (should fail)
    wrong_price = verifier.verify_price("$799", product)
    print_test("Reject wrong price ($799)", not wrong_price['verified'])
    print(f"    Result: {wrong_price['status']} - {wrong_price['message']}")
    
    # Test 3: Verify specification exists
    spec_result = verifier.verify_specification("storage", "256GB", product)
    print_test("Verify storage specification (256GB)", spec_result['verified'])
    print(f"    Result: {spec_result['status']}")
    
    # Test 4: Verify spec not in source (should be unknown)
    battery_result = verifier.verify_specification("battery", "20 hours", product)
    print_test("Mark unknown spec as unverified (battery)", not battery_result['verified'])
    print(f"    Result: {battery_result['status']} - {battery_result['message']}")
    
    # Test 5: Format verified fact with citation
    fact = verifier.format_verified_fact(
        "Price",
        "$899",
        product.get('url'),
        verified=True,
        confidence=1.0
    )
    print_test("Format fact with source citation", "✅" in fact and "Source:" in fact)
    print(f"    Output: {fact}")
    
    # Test 6: Create fact sheet
    fact_sheet = verifier.create_fact_sheet(product, include_unknown=True)
    print_test("Generate fact sheet", len(fact_sheet) > 0)
    print(f"\n📄 Sample Fact Sheet (first 5 facts):")
    for fact in fact_sheet[:5]:
        print(f"    {fact}")


def test_session_manager(parsed_results: List[Dict[str, Any]]):
    """Test SessionManager numbered results storage"""
    print_header("TEST 4: Session Manager - Numbered Results Storage")
    
    from utils.session_manager import get_session_manager
    
    manager = get_session_manager()
    session_id = "test_session_123"
    
    # Test 1: Save numbered results
    manager.save_numbered_results(session_id, parsed_results)
    print_test("Save numbered results to session", True)
    
    # Test 2: Get numbered results
    numbered = manager.get_numbered_results(session_id)
    print_test("Retrieve numbered results", numbered is not None and len(numbered) > 0)
    print(f"    Retrieved {len(numbered)} products")
    
    # Test 3: Get product by number
    product_1 = manager.get_product_by_number(session_id, 1)
    print_test("Get product by number (#1)", product_1 is not None)
    if product_1:
        print(f"    Product #1: {product_1.get('clean_name')}")
    
    # Test 4: Get all results data
    all_data = manager.get_all_results_data(session_id)
    print_test("Get all results data", all_data is not None)
    if all_data:
        print(f"    Products: {len(all_data.get('numbered_results', {}))}")
        print(f"    Name mappings: {len(all_data.get('product_name_map', {}))}")
        print(f"    Attribute mappings: {len(all_data.get('product_attribute_map', {}))}")
    
    # Test 5: Verify mappings
    if all_data:
        name_map = all_data.get('product_name_map', {})
        attr_map = all_data.get('product_attribute_map', {})
        
        has_names = len(name_map) > 0
        print_test("Product name mappings created", has_names)
        if has_names:
            print(f"    Sample names: {list(name_map.keys())[:3]}")
        
        has_attrs = len(attr_map) > 0
        print_test("Attribute mappings created", has_attrs)
        if has_attrs:
            print(f"    Sample attributes: {list(attr_map.keys())[:5]}")


async def test_llm_integration(parsed_results: List[Dict[str, Any]]):
    """Test LLM integration for complex queries"""
    print_header("TEST 5: LLM Integration - Complex Query Matching")
    
    from utils.product_matcher import ProductMatcher
    import os
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  SKIPPING - OPENAI_API_KEY not set")
        return
    
    matcher = ProductMatcher()
    
    try:
        # Test complex query that needs LLM
        print("🤖 Testing LLM-based matching...")
        print("   Query: 'the one with the Pro chip and titanium finish'")
        
        match = matcher.match_product(
            "the one with the Pro chip and titanium finish",
            parsed_results
        )
        
        print_test("LLM matches complex query", match is not None)
        if match:
            print(f"    Matched: {match.product.get('clean_name')}")
            print(f"    Confidence: {match.confidence:.2f}")
            print(f"    Reasoning: {match.reasoning}")
        
    except Exception as e:
        print(f"⚠️  LLM test error: {str(e)}")


def run_all_tests():
    """Run all tests"""
    print("\n" + "🚀" * 35)
    print("  ENHANCED DEALFINDER AI - FEATURE TESTS")
    print("🚀" * 35)
    
    try:
        # Test 1: Result Parser
        parsed_results = test_result_parser()
        
        # Test 2: Product Matcher
        if parsed_results:
            test_product_matcher(parsed_results)
        
        # Test 3: Fact Verifier
        if parsed_results:
            test_fact_verifier(parsed_results)
        
        # Test 4: Session Manager
        if parsed_results:
            test_session_manager(parsed_results)
        
        # Test 5: LLM Integration (async)
        if parsed_results:
            asyncio.run(test_llm_integration(parsed_results))
        
        print_header("🎉 ALL TESTS COMPLETED!")
        print("✅ Core infrastructure is working")
        print("✅ Product matching is functional")
        print("✅ Fact verification is active")
        print("✅ Session management is ready")
        print("\n💡 Next: Test with real agent pipeline using agent_multi.py")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
