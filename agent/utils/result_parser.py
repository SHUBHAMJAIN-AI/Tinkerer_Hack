"""
Result Parser Utility
Extracts structured deal information from raw search results
"""

import re
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ResultParser:
    """Parse and structure raw search results into standardized deal format"""
    
    @staticmethod
    def extract_price_from_content(content: str) -> Optional[str]:
        """Extract price information from content text"""
        if not content:
            return None
            
        # Common price patterns
        price_patterns = [
            r'\$([0-9,]+\.?[0-9]*)',  # $123.45, $1,234.56
            r'Price[:\s]*\$([0-9,]+\.?[0-9]*)',  # Price: $123.45
            r'([0-9,]+\.?[0-9]*)\s*dollars?',  # 123 dollars
            r'\$([0-9,]+)',  # $123
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # Return the first valid price found
                price_str = matches[0].replace(',', '')
                try:
                    price = float(price_str)
                    return f"${price:.2f}"
                except ValueError:
                    continue
        
        return None
    
    @staticmethod
    def extract_discount_from_content(content: str) -> Optional[str]:
        """Extract discount information from content text"""
        if not content:
            return None
            
        discount_patterns = [
            r'Save\s*\$([0-9,]+\.?[0-9]*)',  # Save $50
            r'([0-9]+)%\s*off',  # 25% off
            r'Discount[:\s]*([0-9]+)%',  # Discount: 25%
            r'(-[0-9]+%)',  # -25%
        ]
        
        for pattern in discount_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    @staticmethod
    def extract_rating_from_content(content: str) -> Optional[float]:
        """Extract rating from content text"""
        if not content:
            return None
            
        rating_patterns = [
            r'([0-9]\.?[0-9]*)\s*out of 5',  # 4.5 out of 5
            r'Rating[:\s]*([0-9]\.?[0-9]*)',  # Rating: 4.5
            r'([0-9]\.?[0-9]*)\s*stars?',  # 4.5 stars
            r'([0-9]\.?[0-9]*)/5',  # 4.5/5
        ]
        
        for pattern in rating_patterns:
            matches = re.findall(pattern, content)
            if matches:
                try:
                    rating = float(matches[0])
                    if 0 <= rating <= 5:
                        return rating
                except ValueError:
                    continue
        
        return None
    
    @staticmethod
    def extract_store_from_url(url: str) -> str:
        """Extract store name from URL"""
        if not url:
            return "Unknown Store"
            
        try:
            domain = urlparse(url).netloc.lower()
            
            # Store mappings
            store_mappings = {
                'amazon.com': 'Amazon',
                'bestbuy.com': 'Best Buy',
                'target.com': 'Target',
                'walmart.com': 'Walmart',
                'ebay.com': 'eBay',
                'costco.com': 'Costco',
                'homedepot.com': 'Home Depot',
                'lowes.com': "Lowe's",
                'newegg.com': 'Newegg',
                'bhphotovideo.com': 'B&H Photo',
                'macys.com': "Macy's",
                'kohls.com': "Kohl's",
                'jcpenney.com': 'JCPenney',
                'sears.com': 'Sears',
                'overstock.com': 'Overstock',
                'wayfair.com': 'Wayfair',
            }
            
            # Check for exact matches
            for domain_key, store_name in store_mappings.items():
                if domain_key in domain:
                    return store_name
            
            # Extract main domain name as fallback
            domain_parts = domain.replace('www.', '').split('.')
            if len(domain_parts) >= 2:
                return domain_parts[0].title()
                
            return "Unknown Store"
            
        except Exception as e:
            logger.warning(f"Error extracting store from URL {url}: {e}")
            return "Unknown Store"
    
    @staticmethod
    def parse_tavily_result(result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a single Tavily search result into structured deal format"""
        try:
            url = result.get('url', '')
            title = result.get('title', 'Unknown Product')
            content = result.get('content', '')
            score = result.get('score', 0)
            
            # Extract structured information
            price = ResultParser.extract_price_from_content(content)
            discount = ResultParser.extract_discount_from_content(content)
            rating = ResultParser.extract_rating_from_content(content)
            store = ResultParser.extract_store_from_url(url)
            
            # Clean up title (remove common prefixes/suffixes)
            clean_title = title.strip()
            if clean_title.startswith('Amazon.com'):
                clean_title = clean_title.replace('Amazon.com', '').strip(' :-')
            
            return {
                'title': clean_title,
                'url': url,
                'price': price or 'N/A',  # Ensure price is never None
                'originalPrice': None,  # Would need more sophisticated extraction
                'discount': discount,
                'store': store,
                'rating': rating,
                'content': content[:200] + '...' if len(content) > 200 else content,
                'score': score,
                'source': 'tavily',
                'verified': True,
                'image': None,  # Not typically available in Tavily results
            }
            
        except Exception as e:
            logger.error(f"Error parsing Tavily result: {e}")
            return {
                'title': result.get('title', 'Unknown Product'),
                'url': result.get('url', ''),
                'price': 'N/A',
                'store': 'Unknown Store',
                'content': str(result),
                'score': 0,
                'verified': False
            }
    
    @staticmethod
    def parse_tavily_response(response: str) -> List[Dict[str, Any]]:
        """Parse full Tavily API response into structured deals list"""
        try:
            # Handle string responses that contain the actual data
            if isinstance(response, str):
                # Try to extract the results from the string response
                import json
                import ast
                
                # Look for patterns that indicate the results structure
                if 'results' in response:
                    # Try to extract JSON-like content
                    start_idx = response.find("'results': [")
                    if start_idx == -1:
                        start_idx = response.find('"results": [')
                    
                    if start_idx != -1:
                        # Find the complete results array
                        bracket_count = 0
                        result_start = response.find('[', start_idx)
                        current_idx = result_start
                        
                        while current_idx < len(response):
                            if response[current_idx] == '[':
                                bracket_count += 1
                            elif response[current_idx] == ']':
                                bracket_count -= 1
                                if bracket_count == 0:
                                    results_str = response[result_start:current_idx + 1]
                                    try:
                                        # Try to safely evaluate as Python literal
                                        results_data = ast.literal_eval(results_str)
                                        if isinstance(results_data, list):
                                            return [ResultParser.parse_tavily_result(item) for item in results_data]
                                    except:
                                        pass
                                    break
                            current_idx += 1
            
            # Fallback: create a single result from the raw response
            logger.warning("Could not parse Tavily response structure, creating fallback result")
            return [{
                'title': 'Search Results',
                'url': 'https://example.com',
                'price': 'N/A',
                'store': 'Unknown Store',
                'content': response[:500] + '...' if len(response) > 500 else response,
                'score': 0,
                'verified': False
            }]
            
        except Exception as e:
            logger.error(f"Error parsing Tavily response: {e}")
            return [{
                'title': 'Error Processing Results',
                'url': 'https://example.com',
                'price': 'N/A',
                'store': 'Unknown Store',
                'content': f"Error: {str(e)}",
                'score': 0,
                'verified': False
            }]
