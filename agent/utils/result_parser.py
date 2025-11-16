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
    def extract_product_name(title: str) -> str:
        """Extract clean product name from title"""
        # Remove common suffixes and prefixes
        clean = title.strip()
        
        # Remove store names
        store_prefixes = ['Amazon.com', 'Best Buy', 'Walmart', 'Target', 'eBay']
        for prefix in store_prefixes:
            if clean.startswith(prefix):
                clean = clean.replace(prefix, '').strip(' :-')
        
        # Remove trailing junk
        clean = re.sub(r'\s*[-|]\s*Amazon\.com$', '', clean)
        clean = re.sub(r'\s*\(.*?\)$', '', clean)  # Remove trailing parentheses
        
        return clean
    
    @staticmethod
    def extract_keywords(title: str, content: str) -> List[str]:
        """Extract searchable keywords from title and content"""
        text = f"{title} {content}".lower()
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'with', 'from', 'of', 'is', 'are', 'was', 'were', 'be', 'been'}
        
        # Extract words (alphanumeric sequences)
        words = re.findall(r'\b\w+\b', text)
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        return unique_keywords[:20]  # Limit to top 20
    
    @staticmethod
    def extract_descriptors(title: str, content: str, price: str, store: str) -> Dict[str, Any]:
        """Extract product descriptors for matching"""
        descriptors = {}
        text = f"{title} {content}".lower()
        
        # Color extraction
        colors = ['black', 'white', 'silver', 'gold', 'rose', 'blue', 'red', 'green', 
                 'pink', 'purple', 'yellow', 'titanium', 'gray', 'grey', 'bronze']
        for color in colors:
            if color in text:
                descriptors['color'] = color.title()
                break
        
        # Storage extraction
        storage_pattern = r'(\d+)(gb|tb)'
        storage_match = re.search(storage_pattern, text, re.IGNORECASE)
        if storage_match:
            descriptors['storage'] = f"{storage_match.group(1)}{storage_match.group(2).upper()}"
        
        # Condition
        if any(word in text for word in ['refurbished', 'renewed', 'used', 'open box']):
            descriptors['condition'] = 'Refurbished'
        else:
            descriptors['condition'] = 'New'
        
        # Price tier
        if price and price != 'N/A':
            try:
                price_val = float(price.replace('$', '').replace(',', ''))
                if price_val < 100:
                    descriptors['price_tier'] = 'budget'
                elif price_val < 500:
                    descriptors['price_tier'] = 'mid-range'
                else:
                    descriptors['price_tier'] = 'premium'
            except:
                pass
        
        # Store
        descriptors['store'] = store
        
        return descriptors
    
    @staticmethod
    def parse_tavily_result(result: Dict[str, Any], result_number: int = None) -> Dict[str, Any]:
        """Parse a single Tavily search result into structured deal format with numbering"""
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
            
            # Clean up title
            clean_title = ResultParser.extract_product_name(title)
            
            # NEW: Extract product name and metadata
            clean_name = clean_title.split('-')[0].strip() if '-' in clean_title else clean_title
            keywords = ResultParser.extract_keywords(clean_title, content)
            descriptors = ResultParser.extract_descriptors(clean_title, content, price or 'N/A', store)
            
            # Generate unique result ID
            import hashlib
            result_id = hashlib.md5(f"{url}{clean_title}".encode()).hexdigest()[:12]
            
            return {
                'result_number': result_number,  # NEW: Sequential number
                'result_id': result_id,  # NEW: Unique identifier
                'title': clean_title,
                'clean_name': clean_name,  # NEW: Extracted clean name
                'keywords': keywords,  # NEW: Searchable keywords
                'descriptors': descriptors,  # NEW: Color, storage, condition, etc.
                'url': url,
                'price': price or 'N/A',
                'originalPrice': None,
                'discount': discount,
                'store': store,
                'rating': rating,
                'content': content[:200] + '...' if len(content) > 200 else content,
                'score': score,
                'source': 'tavily',
                'verified': True,
                'image': None,
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
        """Parse full Tavily API response into structured deals list with numbering"""
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
                                            # NEW: Add sequential numbering
                                            return [
                                                ResultParser.parse_tavily_result(item, idx + 1) 
                                                for idx, item in enumerate(results_data)
                                            ]
                                    except:
                                        pass
                                    break
                            current_idx += 1
            
            # Fallback: create a single result from the raw response
            logger.warning("Could not parse Tavily response structure, creating fallback result")
            return [{
                'result_number': 1,
                'result_id': 'fallback_001',
                'title': 'Search Results',
                'clean_name': 'Search Results',
                'keywords': [],
                'descriptors': {},
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
                'result_number': 1,
                'result_id': 'error_001',
                'title': 'Error Processing Results',
                'clean_name': 'Error',
                'keywords': [],
                'descriptors': {},
                'url': 'https://example.com',
                'price': 'N/A',
                'store': 'Unknown Store',
                'content': f"Error: {str(e)}",
                'score': 0,
                'verified': False
            }]
