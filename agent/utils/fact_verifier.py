"""
Fact Verifier - Ensures all claims are sourced and accurate
Prevents LLM hallucinations by validating against actual data
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class FactVerifier:
    """
    Verifies facts against source data to prevent hallucinations
    Core principle: Only state what's explicitly in the source
    """
    
    # Confidence levels
    VERIFIED = "✅"  # Direct from source
    INFERRED = "⚠️"   # Logical deduction
    UNKNOWN = "❌"    # Not available
    
    @staticmethod
    def verify_price(claimed_price: str, source_price: str) -> Dict[str, Any]:
        """
        Verify price claim against source
        
        Returns:
            {
                'is_verified': bool,
                'confidence': str ('✅', '⚠️', '❌'),
                'actual_value': str,
                'message': str
            }
        """
        try:
            # Normalize prices for comparison
            claimed = claimed_price.replace('$', '').replace(',', '').strip()
            source = source_price.replace('$', '').replace(',', '').strip()
            
            if source == 'N/A' or not source:
                return {
                    'is_verified': False,
                    'confidence': FactVerifier.UNKNOWN,
                    'actual_value': None,
                    'message': 'Price not specified in source'
                }
            
            if claimed == source or float(claimed) == float(source):
                return {
                    'is_verified': True,
                    'confidence': FactVerifier.VERIFIED,
                    'actual_value': source_price,
                    'message': f'Price verified: {source_price}'
                }
            else:
                return {
                    'is_verified': False,
                    'confidence': FactVerifier.UNKNOWN,
                    'actual_value': source_price,
                    'message': f'Price mismatch: claimed {claimed_price}, actual {source_price}'
                }
                
        except Exception as e:
            logger.error(f"Error verifying price: {e}")
            return {
                'is_verified': False,
                'confidence': FactVerifier.UNKNOWN,
                'actual_value': None,
                'message': 'Error verifying price'
            }
    
    @staticmethod
    def verify_specification(claim: str, source_data: Dict[str, Any], spec_type: str) -> Dict[str, Any]:
        """
        Verify a specification claim against source data
        
        Args:
            claim: The claimed specification
            source_data: Product data from source
            spec_type: Type of spec ('storage', 'color', 'rating', etc.)
        """
        # Get actual value from source
        actual_value = None
        
        if spec_type == 'storage':
            actual_value = source_data.get('descriptors', {}).get('storage')
        elif spec_type == 'color':
            actual_value = source_data.get('descriptors', {}).get('color')
        elif spec_type == 'rating':
            actual_value = source_data.get('rating')
        elif spec_type == 'store':
            actual_value = source_data.get('store')
        elif spec_type == 'condition':
            actual_value = source_data.get('descriptors', {}).get('condition')
        else:
            # Check in title or content
            title = source_data.get('title', '').lower()
            content = source_data.get('content', '').lower()
            if claim.lower() in title or claim.lower() in content:
                actual_value = claim
        
        if not actual_value:
            return {
                'is_verified': False,
                'confidence': FactVerifier.UNKNOWN,
                'actual_value': None,
                'message': f'{spec_type} not specified in source'
            }
        
        # Normalize for comparison
        claim_norm = str(claim).lower().strip()
        actual_norm = str(actual_value).lower().strip()
        
        if claim_norm == actual_norm or claim_norm in actual_norm or actual_norm in claim_norm:
            return {
                'is_verified': True,
                'confidence': FactVerifier.VERIFIED,
                'actual_value': actual_value,
                'message': f'{spec_type} verified: {actual_value}'
            }
        else:
            return {
                'is_verified': False,
                'confidence': FactVerifier.UNKNOWN,
                'actual_value': actual_value,
                'message': f'{spec_type} mismatch: claimed {claim}, actual {actual_value}'
            }
    
    @staticmethod
    def verify_availability(claimed_status: str, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify availability/stock status"""
        content = source_data.get('content', '').lower()
        title = source_data.get('title', '').lower()
        
        in_stock_indicators = ['in stock', 'available', 'ships', 'delivery']
        out_of_stock_indicators = ['out of stock', 'unavailable', 'sold out', 'not available']
        
        has_in_stock = any(indicator in content or indicator in title for indicator in in_stock_indicators)
        has_out_of_stock = any(indicator in content or indicator in title for indicator in out_of_stock_indicators)
        
        if has_out_of_stock:
            return {
                'is_verified': True,
                'confidence': FactVerifier.VERIFIED,
                'actual_value': 'Out of Stock',
                'message': 'Verified: Out of Stock'
            }
        elif has_in_stock:
            return {
                'is_verified': True,
                'confidence': FactVerifier.VERIFIED,
                'actual_value': 'In Stock',
                'message': 'Verified: In Stock'
            }
        else:
            return {
                'is_verified': False,
                'confidence': FactVerifier.UNKNOWN,
                'actual_value': None,
                'message': 'Availability not specified in source'
            }
    
    @staticmethod
    def verify_product_match(claimed_name: str, actual_product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify that the LLM matched the correct product
        Prevents "tell me about iPhone" → returns MacBook
        """
        clean_name = actual_product.get('clean_name', '').lower()
        title = actual_product.get('title', '').lower()
        keywords = [kw.lower() for kw in actual_product.get('keywords', [])]
        
        claimed_lower = claimed_name.lower()
        claimed_words = set(claimed_lower.split())
        
        # Check if claimed name appears in actual product
        if claimed_lower in clean_name or claimed_lower in title:
            return {
                'is_verified': True,
                'confidence': FactVerifier.VERIFIED,
                'actual_value': clean_name,
                'message': f'Product match verified: {clean_name}'
            }
        
        # Check word overlap
        title_words = set(title.split())
        overlap = claimed_words.intersection(title_words)
        overlap_ratio = len(overlap) / len(claimed_words) if claimed_words else 0
        
        if overlap_ratio >= 0.7:  # 70% word overlap
            return {
                'is_verified': True,
                'confidence': FactVerifier.INFERRED,
                'actual_value': clean_name,
                'message': f'Likely match (70%+ overlap): {clean_name}'
            }
        elif overlap_ratio >= 0.4:
            return {
                'is_verified': False,
                'confidence': FactVerifier.INFERRED,
                'actual_value': clean_name,
                'message': f'Uncertain match ({int(overlap_ratio*100)}% overlap): {clean_name}'
            }
        else:
            return {
                'is_verified': False,
                'confidence': FactVerifier.UNKNOWN,
                'actual_value': clean_name,
                'message': f'Product mismatch: requested "{claimed_name}", got "{clean_name}"'
            }
    
    @staticmethod
    def validate_response(response_text: str, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an LLM response against source data
        Checks for potential hallucinations
        """
        issues = []
        
        # Check for price claims without verification
        price_pattern = r'\$[\d,]+(?:\.\d{2})?'
        prices_in_response = re.findall(price_pattern, response_text)
        
        source_price = source_data.get('price', 'N/A')
        for price in prices_in_response:
            if price != source_price and source_price != 'N/A':
                issues.append({
                    'type': 'price_mismatch',
                    'severity': 'high',
                    'message': f'Response mentions price {price} but source has {source_price}'
                })
        
        # Check for specification claims
        spec_keywords = ['storage', 'ram', 'memory', 'processor', 'cpu', 'gpu', 'screen', 'display', 
                        'battery', 'camera', 'weight', 'dimensions', 'warranty']
        
        for keyword in spec_keywords:
            if keyword in response_text.lower():
                # Check if this spec is in source data
                title = source_data.get('title', '').lower()
                content = source_data.get('content', '').lower()
                descriptors = source_data.get('descriptors', {})
                
                if keyword not in title and keyword not in content and keyword not in str(descriptors).lower():
                    issues.append({
                        'type': 'unverified_specification',
                        'severity': 'medium',
                        'message': f'Response mentions "{keyword}" but not found in source'
                    })
        
        # Check for absolute claims without qualifiers
        absolute_words = ['always', 'never', 'every', 'all', 'none', 'guaranteed', 'certainly', 'definitely']
        for word in absolute_words:
            if word in response_text.lower():
                issues.append({
                    'type': 'absolute_claim',
                    'severity': 'low',
                    'message': f'Response contains absolute word "{word}" - may be overstating'
                })
        
        # Check for source citations
        url_pattern = r'https?://\S+'
        urls_in_response = re.findall(url_pattern, response_text)
        source_url = source_data.get('url', '')
        
        if not urls_in_response and source_url:
            issues.append({
                'type': 'missing_citation',
                'severity': 'medium',
                'message': 'Response lacks source URL citation'
            })
        
        return {
            'is_valid': len([i for i in issues if i['severity'] == 'high']) == 0,
            'issues': issues,
            'confidence': 'high' if not issues else 'medium' if len(issues) <= 2 else 'low'
        }
    
    @staticmethod
    def format_verified_fact(fact_type: str, value: Any, source_url: str, 
                           confidence: str = VERIFIED) -> str:
        """
        Format a fact with proper verification markers
        
        Args:
            fact_type: Type of fact (price, storage, etc.)
            value: The actual value
            source_url: URL to source
            confidence: Confidence level (✅/⚠️/❌)
            
        Returns:
            Formatted string with verification marker
        """
        if value is None or value == 'N/A':
            return f"{FactVerifier.UNKNOWN} {fact_type}: Not specified in listing"
        
        if confidence == FactVerifier.VERIFIED:
            return f"{FactVerifier.VERIFIED} {fact_type}: {value} (Source: {source_url})"
        elif confidence == FactVerifier.INFERRED:
            return f"{FactVerifier.INFERRED} {fact_type}: {value} (Inferred from listing)"
        else:
            return f"{FactVerifier.UNKNOWN} {fact_type}: {value} (Unverified)"
    
    @staticmethod
    def create_fact_sheet(product_data: Dict[str, Any]) -> str:
        """
        Create a verified fact sheet for a product
        Only includes facts that are present in source data
        """
        url = product_data.get('url', 'https://example.com')
        facts = []
        
        # Price (always include)
        price = product_data.get('price')
        if price and price != 'N/A':
            facts.append(FactVerifier.format_verified_fact('Price', price, url, FactVerifier.VERIFIED))
        else:
            facts.append(f"{FactVerifier.UNKNOWN} Price: Not specified")
        
        # Store
        store = product_data.get('store')
        if store and store != 'Unknown Store':
            facts.append(FactVerifier.format_verified_fact('Store', store, url, FactVerifier.VERIFIED))
        
        # Rating
        rating = product_data.get('rating')
        if rating:
            facts.append(FactVerifier.format_verified_fact('Rating', f"{rating}/5", url, FactVerifier.VERIFIED))
        
        # Descriptors
        descriptors = product_data.get('descriptors', {})
        
        if 'storage' in descriptors:
            facts.append(FactVerifier.format_verified_fact('Storage', descriptors['storage'], url, FactVerifier.VERIFIED))
        
        if 'color' in descriptors:
            facts.append(FactVerifier.format_verified_fact('Color', descriptors['color'], url, FactVerifier.VERIFIED))
        
        if 'condition' in descriptors:
            facts.append(FactVerifier.format_verified_fact('Condition', descriptors['condition'], url, FactVerifier.VERIFIED))
        
        # Discount
        discount = product_data.get('discount')
        if discount:
            facts.append(FactVerifier.format_verified_fact('Discount', discount, url, FactVerifier.VERIFIED))
        
        return "\n".join(facts)


def get_fact_verifier() -> FactVerifier:
    """Get FactVerifier instance"""
    return FactVerifier()
