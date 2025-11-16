"""
Product Matcher - Intelligent product matching using LLM
Matches user queries to products by number, name, or description
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import os
from openai import OpenAI

logger = logging.getLogger(__name__)


@dataclass
class ProductMatch:
    """Represents a product match with confidence score"""
    product_number: int
    product_data: Dict[str, Any]
    confidence: float
    reasoning: str
    match_type: str  # 'exact_number', 'name', 'description', 'attribute'


class ProductMatcher:
    """
    Intelligently matches user queries to products
    Supports numbers, names, descriptions, and natural language
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def detect_number_reference(self, query: str) -> List[int]:
        """
        Detect numbered product references in query
        
        Examples:
        - "#1", "#2" → [1, 2]
        - "product 3" → [3]
        - "number 5" → [5]
        - "first one" → [1]
        """
        numbers = []
        query_lower = query.lower()
        
        # Pattern 1: #N
        hash_pattern = r'#(\d+)'
        hash_matches = re.findall(hash_pattern, query)
        numbers.extend([int(n) for n in hash_matches])
        
        # Pattern 2: "product N", "number N", "item N"
        word_pattern = r'(?:product|number|item)\s+(\d+)'
        word_matches = re.findall(word_pattern, query_lower)
        numbers.extend([int(n) for n in word_matches])
        
        # Pattern 3: Ordinals
        ordinals = {
            'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
            'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10,
            '1st': 1, '2nd': 2, '3rd': 3, '4th': 4, '5th': 5,
            '6th': 6, '7th': 7, '8th': 8, '9th': 9, '10th': 10
        }
        
        for word, num in ordinals.items():
            if word in query_lower:
                numbers.append(num)
        
        # Remove duplicates and sort
        return sorted(list(set(numbers)))
    
    def match_by_number(self, numbers: List[int], products: Dict[str, Dict]) -> List[ProductMatch]:
        """Match products by exact number"""
        matches = []
        
        for num in numbers:
            num_str = str(num)
            if num_str in products:
                matches.append(ProductMatch(
                    product_number=num,
                    product_data=products[num_str],
                    confidence=1.0,
                    reasoning=f"Exact number match: #{num}",
                    match_type='exact_number'
                ))
        
        return matches
    
    def match_by_description(self, query: str, products: Dict[str, Dict]) -> List[ProductMatch]:
        """
        Match products by descriptive attributes
        Examples: "cheapest", "blue one", "Amazon deal"
        """
        matches = []
        query_lower = query.lower()
        
        # Convert to list for easier processing
        product_list = [(int(k), v) for k, v in products.items()]
        
        # Price-based matching
        if any(word in query_lower for word in ['cheapest', 'lowest price', 'most affordable']):
            # Find product with lowest price
            valid_products = []
            for num, prod in product_list:
                price_str = prod.get('price', 'N/A')
                if price_str != 'N/A':
                    try:
                        price = float(price_str.replace('$', '').replace(',', ''))
                        valid_products.append((num, prod, price))
                    except:
                        pass
            
            if valid_products:
                cheapest = min(valid_products, key=lambda x: x[2])
                matches.append(ProductMatch(
                    product_number=cheapest[0],
                    product_data=cheapest[1],
                    confidence=0.9,
                    reasoning=f"Lowest price: {cheapest[1].get('price')}",
                    match_type='description'
                ))
        
        if any(word in query_lower for word in ['most expensive', 'highest price', 'premium']):
            valid_products = []
            for num, prod in product_list:
                price_str = prod.get('price', 'N/A')
                if price_str != 'N/A':
                    try:
                        price = float(price_str.replace('$', '').replace(',', ''))
                        valid_products.append((num, prod, price))
                    except:
                        pass
            
            if valid_products:
                most_expensive = max(valid_products, key=lambda x: x[2])
                matches.append(ProductMatch(
                    product_number=most_expensive[0],
                    product_data=most_expensive[1],
                    confidence=0.9,
                    reasoning=f"Highest price: {most_expensive[1].get('price')}",
                    match_type='description'
                ))
        
        # Store-based matching
        for num, prod in product_list:
            store = prod.get('store', '').lower()
            if store and store in query_lower:
                matches.append(ProductMatch(
                    product_number=num,
                    product_data=prod,
                    confidence=0.85,
                    reasoning=f"Store match: {prod.get('store')}",
                    match_type='attribute'
                ))
        
        # Attribute-based matching (color, storage, etc.)
        for num, prod in product_list:
            descriptors = prod.get('descriptors', {})
            
            # Color matching
            if 'color' in descriptors:
                color = descriptors['color'].lower()
                if color in query_lower:
                    matches.append(ProductMatch(
                        product_number=num,
                        product_data=prod,
                        confidence=0.8,
                        reasoning=f"Color match: {descriptors['color']}",
                        match_type='attribute'
                    ))
            
            # Storage matching
            if 'storage' in descriptors:
                storage = descriptors['storage'].lower()
                if storage in query_lower:
                    matches.append(ProductMatch(
                        product_number=num,
                        product_data=prod,
                        confidence=0.8,
                        reasoning=f"Storage match: {descriptors['storage']}",
                        match_type='attribute'
                    ))
        
        return matches
    
    def match_by_name_fuzzy(self, query: str, products: Dict[str, Dict]) -> List[ProductMatch]:
        """Fuzzy match product names"""
        matches = []
        query_lower = query.lower()
        
        for num_str, prod in products.items():
            num = int(num_str)
            clean_name = prod.get('clean_name', '').lower()
            title = prod.get('title', '').lower()
            keywords = [kw.lower() for kw in prod.get('keywords', [])]
            
            # Calculate match score
            score = 0
            reasons = []
            
            # Exact name match
            if query_lower in clean_name or clean_name in query_lower:
                score += 0.9
                reasons.append("Name match")
            
            # Title partial match
            elif query_lower in title or any(word in title for word in query_lower.split()):
                score += 0.7
                reasons.append("Title partial match")
            
            # Keyword match
            query_words = set(query_lower.split())
            keyword_matches = query_words.intersection(set(keywords))
            if keyword_matches:
                score += 0.3 * (len(keyword_matches) / len(query_words)) if query_words else 0
                reasons.append(f"{len(keyword_matches)} keyword matches")
            
            if score > 0.3:  # Threshold for fuzzy matching
                matches.append(ProductMatch(
                    product_number=num,
                    product_data=prod,
                    confidence=min(score, 0.95),
                    reasoning=", ".join(reasons),
                    match_type='name'
                ))
        
        # Sort by confidence
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches
    
    def match_with_llm(self, query: str, products: Dict[str, Dict], context: str = "") -> Dict[str, Any]:
        """
        Use LLM to intelligently match user query to products
        Handles ambiguity and complex queries
        """
        try:
            # Prepare product list for LLM
            product_descriptions = []
            for num_str, prod in products.items():
                desc = f"{num_str}. {prod.get('title', 'Unknown')} - {prod.get('price', 'N/A')} ({prod.get('store', 'Unknown')})"
                product_descriptions.append(desc)
            
            products_text = "\n".join(product_descriptions)
            
            prompt = f"""You are a product matching assistant. Match the user's query to the most relevant product(s).

Available Products:
{products_text}

User Query: "{query}"

{f"Context: {context}" if context else ""}

Return a JSON response with:
{{
  "matches": [
    {{
      "product_number": <number>,
      "confidence": <0.0-1.0>,
      "reasoning": "<why this product matches>"
    }}
  ],
  "is_ambiguous": <true/false>,
  "clarification": "<question to ask user if ambiguous>"
}}

Rules:
- Match based on product name, attributes, price, store
- If multiple products match, include all with confidence scores
- If ambiguous, set is_ambiguous=true and provide clarification
- Be strict: only match if query clearly refers to a product
- Return empty matches if no clear match
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise product matching assistant. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Convert to ProductMatch objects
            llm_matches = []
            for match_data in result.get('matches', []):
                num = match_data.get('product_number')
                num_str = str(num)
                
                if num_str in products:
                    llm_matches.append(ProductMatch(
                        product_number=num,
                        product_data=products[num_str],
                        confidence=match_data.get('confidence', 0.5),
                        reasoning=match_data.get('reasoning', 'LLM match'),
                        match_type='llm'
                    ))
            
            return {
                'matches': llm_matches,
                'is_ambiguous': result.get('is_ambiguous', False),
                'clarification': result.get('clarification', None)
            }
            
        except Exception as e:
            logger.error(f"LLM matching error: {e}")
            return {'matches': [], 'is_ambiguous': False, 'clarification': None}
    
    def match_product(self, query: str, products: Dict[str, Dict], 
                     use_llm: bool = True, context: str = "") -> Dict[str, Any]:
        """
        Main method to match user query to products
        
        Args:
            query: User's query
            products: Dict of numbered products {1: {data}, 2: {data}}
            use_llm: Whether to use LLM for complex matching
            context: Additional context from conversation
            
        Returns:
            {
                'matches': List[ProductMatch],
                'is_ambiguous': bool,
                'clarification': Optional[str]
            }
        """
        all_matches = []
        
        # Step 1: Check for number references (highest priority)
        numbers = self.detect_number_reference(query)
        if numbers:
            number_matches = self.match_by_number(numbers, products)
            if number_matches:
                return {
                    'matches': number_matches,
                    'is_ambiguous': False,
                    'clarification': None
                }
        
        # Step 2: Try descriptive matching
        desc_matches = self.match_by_description(query, products)
        all_matches.extend(desc_matches)
        
        # Step 3: Try name-based fuzzy matching
        name_matches = self.match_by_name_fuzzy(query, products)
        all_matches.extend(name_matches)
        
        # Remove duplicates (keep highest confidence)
        unique_matches = {}
        for match in all_matches:
            if match.product_number not in unique_matches or \
               match.confidence > unique_matches[match.product_number].confidence:
                unique_matches[match.product_number] = match
        
        all_matches = list(unique_matches.values())
        all_matches.sort(key=lambda x: x.confidence, reverse=True)
        
        # Step 4: Use LLM for complex/ambiguous queries
        if use_llm and (len(all_matches) > 3 or len(all_matches) == 0):
            llm_result = self.match_with_llm(query, products, context)
            if llm_result['matches']:
                return llm_result
        
        # Step 5: Handle ambiguity
        if len(all_matches) > 1:
            # Check if top matches have similar confidence
            top_confidence = all_matches[0].confidence
            similar_matches = [m for m in all_matches if m.confidence >= top_confidence - 0.2]
            
            if len(similar_matches) > 1:
                # Ambiguous - ask for clarification
                clarification = "I found multiple matches. Did you mean:\n"
                for match in similar_matches[:3]:
                    clarification += f"{match.product_number}️⃣ {match.product_data.get('title')}\n"
                
                return {
                    'matches': similar_matches,
                    'is_ambiguous': True,
                    'clarification': clarification
                }
        
        return {
            'matches': all_matches,
            'is_ambiguous': False,
            'clarification': None
        }


def get_product_matcher() -> ProductMatcher:
    """Get ProductMatcher instance"""
    return ProductMatcher()
