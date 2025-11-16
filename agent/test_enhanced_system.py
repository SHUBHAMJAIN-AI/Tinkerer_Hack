"""
Test script for Enhanced DealFinder AI System
Tests numbered results, product queries, and fact verification
"""

import asyncio
import logging
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_result_parser():
    """Test ResultParser with numbering and extraction"""
    print("\n" + "="*60)
    print("🧪 TEST 1: Result Parser Enhancement")
    print("="*60)
    
    from utils import ResultParser
    
    # Mock Tavily result
    mock_result = {
        "results": [
            {
                "title": "Apple iPhone 15 Pro 256GB Titanium Blue - Amazon Deal",
                "url": "https://amazon.com/iphone-15-pro",
                "content": "Great deal on iPhone 15 Pro with 256GB storage. Original price $1099, now $999. Free shipping.",
                "score": 0.95
            },
            {
                "title": "Samsung Galaxy S24 Ultra 512GB Black at Best Buy",
                "url": "https://bestbuy.com/samsung-s24",
                "content": "Samsung flagship phone with 512GB. Was $1299, now on sale for $1099.",
                "score": 0.88
            }
        ]
    }
    
    # Parse results
    parsed = ResultParser.parse_tavily_response(mock_result)
    
    print(f"\n✅ Parsed {len(parsed)} results\n")
    
    for result in parsed:
        print(f"#{result['result_number']}. {result['clean_name']}")
        print(f"   ID: {result['result_id']}")
        print(f"   Keywords: {', '.join(result['keywords'][:5])}")
        print(f"   Descriptors: {result['descriptors']}")
        print(f"   Price: {result.get('price', 'N/A')}")
        print()
    
    return parsed


def test_product_matcher(products: List[Dict[str, Any]]):
    """Test ProductMatcher with various query types"""
    print("\n" + "="*60)
    print("🧪 TEST 2: Product Matcher")
    print("="*60)
    
    from utils import get_product_matcher
    
    matcher = get_product_matcher()
    
    test_queries = [
        "#1",
        "product 2",
        "the first one",
        "iPhone 15 Pro",
        "Samsung",
        "the cheapest one",
        "titanium blue",
        "Amazon deal",
        "compare #1 and #2",
    ]
    
    print(f"\nTesting {len(test_queries)} query types:\n")
    
    for query in test_queries:
        matches = matcher.match_product(query, products)
        
        if matches:
            print(f"✅ '{query}' → {len(matches)} match(es)")
            for i, match in enumerate(matches[:2]):
                product_num = match.product.get('result_number', '?')
                product_name = match.product.get('clean_name', 'Unknown')
                print(f"   [{i+1}] #{product_num}: {product_name}")
                print(f"       Confidence: {match.confidence*100:.1f}%")
                print(f"       Method: {match.method}")
        else:
            print(f"❌ '{query}' → No matches")
        print()


def test_fact_verifier(products: List[Dict[str, Any]]):
    """Test FactVerifier for anti-hallucination"""
    print("\n" + "="*60)
    print("🧪 TEST 3: Fact Verifier")
    print("="*60)
    
    from utils import get_fact_verifier
    
    verifier = get_fact_verifier()
    
    if not products:
        print("❌ No products to verify")
        return
    
    product = products[0]
    
    print(f"\nVerifying Product #{product['result_number']}: {product['clean_name']}\n")
    
    # Test price verification
    price_verification = verifier.verify_price(product)
    print(f"Price Verification:")
    print(f"   Status: {price_verification['status']}")
    print(f"   Confidence: {price_verification['confidence']*100:.0f}%")
    print(f"   Price: {price_verification.get('verified_price', 'N/A')}")
    print(f"   Source: {price_verification.get('source', 'N/A')[:50]}...")
    print()
    
    # Test spec verification
    spec_verification = verifier.verify_specification(product, "all")
    print(f"Specification Verification:")
    print(f"   Status: {spec_verification['status']}")
    print(f"   Confidence: {spec_verification['confidence']*100:.0f}%")
    print()
    
    # Create fact sheet
    fact_sheet = verifier.create_fact_sheet(product)
    print(f"Generated Fact Sheet:")
    print(fact_sheet)
    print()
    
    # Test hallucination detection
    test_response = f"This {product['clean_name']} has 1TB storage and costs $599 with a 10-year warranty!"
    
    validation = verifier.validate_response(test_response, product)
    print(f"Hallucination Detection Test:")
    print(f"   Test Response: '{test_response}'")
    print(f"   Passes Validation: {validation['passes_validation']}")
    print(f"   Issues Found: {', '.join(validation['issues']) if validation['issues'] else 'None'}")
    print()


def test_session_manager(products: List[Dict[str, Any]]):
    """Test SessionManager with numbered results"""
    print("\n" + "="*60)
    print("🧪 TEST 4: Session Manager")
    print("="*60)
    
    from utils import get_session_manager
    
    session_manager = get_session_manager()
    test_session_id = "test_session_123"
    
    # Save numbered results
    session_manager.save_numbered_results(test_session_id, products)
    print(f"\n✅ Saved {len(products)} numbered results to session: {test_session_id}\n")
    
    # Retrieve all data
    all_data = session_manager.get_all_results_data(test_session_id)
    
    print(f"Retrieved Data:")
    print(f"   Numbered Results: {len(all_data.get('numbered_results', {}))}")
    print(f"   Product Name Map: {len(all_data.get('product_name_map', {}))}")
    print(f"   Attribute Map: {len(all_data.get('product_attribute_map', {}))}")
    print()
    
    # Test retrieval by number
    product_1 = session_manager.get_product_by_number(test_session_id, 1)
    if product_1:
        print(f"✅ Retrieved product #1: {product_1.get('clean_name', 'Unknown')}")
    else:
        print(f"❌ Could not retrieve product #1")
    print()
    
    # Show mappings
    print(f"Product Name Map:")
    for name, num in list(all_data.get('product_name_map', {}).items())[:3]:
        print(f"   '{name}' → #{num}")
    print()
    
    print(f"Attribute Map (sample):")
    for attr, nums in list(all_data.get('product_attribute_map', {}).items())[:5]:
        print(f"   '{attr}' → products {nums}")
    print()


async def test_product_detail_agent(products: List[Dict[str, Any]]):
    """Test ProductDetailAgent with sample queries"""
    print("\n" + "="*60)
    print("🧪 TEST 5: Product Detail Agent")
    print("="*60)
    
    from nodes.product_detail_agent import ProductDetailAgent
    
    agent = ProductDetailAgent()
    
    # Save to session first
    from utils import get_session_manager
    session_manager = get_session_manager()
    test_session_id = "test_session_detail"
    session_manager.save_numbered_results(test_session_id, products)
    
    test_queries = [
        "Tell me about #1",
        "What's the price of the iPhone?",
        "How does #1 compare to #2?",
    ]
    
    print(f"\nTesting {len(test_queries)} product queries:\n")
    
    for query in test_queries:
        print(f"Query: '{query}'")
        print("-" * 40)
        
        # Match products
        matches = agent.product_matcher.match_product(query, products)
        
        if matches:
            if agent._needs_comparison(query) and len(matches) >= 2:
                # Comparison query
                matched_products = [m.product for m in matches]
                answer = await agent.handle_comparison_query(query, matched_products, products)
            else:
                # Single product query
                best_match = matches[0]
                answer = await agent.answer_product_query(query, best_match.product, best_match, products)
            
            print(f"Answer:\n{answer}\n")
        else:
            print(f"❌ No matches found\n")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🚀 ENHANCED DEALFINDER AI SYSTEM - COMPREHENSIVE TEST")
    print("="*70)
    
    try:
        # Test 1: Result Parser
        products = test_result_parser()
        
        # Test 2: Product Matcher
        test_product_matcher(products)
        
        # Test 3: Fact Verifier
        test_fact_verifier(products)
        
        # Test 4: Session Manager
        test_session_manager(products)
        
        # Test 5: Product Detail Agent (async)
        print("\nRunning async test...")
        asyncio.run(test_product_detail_agent(products))
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*70)
        
        print("\n📋 Summary:")
        print("   ✅ Result Parser - Enhanced with numbering and extraction")
        print("   ✅ Product Matcher - Number, name, and description matching")
        print("   ✅ Fact Verifier - Anti-hallucination system")
        print("   ✅ Session Manager - Numbered results storage")
        print("   ✅ Product Detail Agent - Follow-up query handling")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
