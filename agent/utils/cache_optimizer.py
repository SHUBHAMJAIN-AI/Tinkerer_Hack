"""
Cache Optimizer for Redis Cloud
Implements intelligent cache utilization strategies
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from utils.redis_client import get_redis_client
from utils.cache import CacheManager
from utils.session_manager import SessionManager
import hashlib

logger = logging.getLogger(__name__)


class CacheOptimizer:
    """
    Optimizes cache usage for faster responses and reduced API calls
    """
    
    def __init__(self):
        self.redis_client = get_redis_client()
        self.cache_manager = CacheManager()
        self.session_manager = SessionManager()
    
    def analyze_query_similarity(self, new_query: str, threshold: float = 0.8) -> Optional[Dict]:
        """
        Find similar cached queries to reuse results
        
        Args:
            new_query: The new search query
            threshold: Similarity threshold (0.0-1.0)
            
        Returns:
            Similar cached query data or None
        """
        try:
            # Get all search cache keys
            search_keys = self.redis_client.keys("search:*")
            
            if not search_keys:
                return None
            
            new_query_words = set(new_query.lower().split())
            best_match = None
            best_score = 0.0
            
            for key in search_keys:
                cached_data = self.redis_client.get(key)
                if not cached_data:
                    continue
                    
                try:
                    data = json.loads(cached_data)
                    cached_query = data.get("query", "")
                    
                    # Calculate similarity
                    cached_words = set(cached_query.lower().split())
                    
                    if not cached_words or not new_query_words:
                        continue
                    
                    # Jaccard similarity
                    intersection = new_query_words.intersection(cached_words)
                    union = new_query_words.union(cached_words)
                    similarity = len(intersection) / len(union) if union else 0.0
                    
                    if similarity > best_score and similarity >= threshold:
                        best_score = similarity
                        best_match = {
                            "key": key,
                            "query": cached_query,
                            "similarity": similarity,
                            "results": data.get("results", []),
                            "timestamp": data.get("timestamp")
                        }
                        
                except json.JSONDecodeError:
                    continue
            
            if best_match:
                logger.info(f"🎯 Found similar cached query: '{best_match['query']}' "
                           f"(similarity: {best_match['similarity']:.2f})")
            
            return best_match
            
        except Exception as e:
            logger.error(f"Error analyzing query similarity: {e}")
            return None
    
    def get_contextual_cache_suggestions(self, session_id: str, 
                                       new_query: str) -> List[Dict]:
        """
        Get cache suggestions based on session context
        
        Args:
            session_id: Current session ID
            new_query: New search query
            
        Returns:
            List of relevant cached results
        """
        suggestions = []
        
        try:
            # Get session context
            session_data = self.session_manager.load_session(session_id)
            if not session_data:
                return suggestions
            
            # Get previous searches from this session
            context = session_data.get("current_context", {})
            last_topic = context.get("search_topic", "")
            
            if last_topic:
                # Find related cached searches
                similar_cache = self.analyze_query_similarity(last_topic, threshold=0.6)
                if similar_cache:
                    suggestions.append({
                        "type": "session_related",
                        "source": "Previous session search",
                        "query": similar_cache["query"],
                        "results": similar_cache["results"][:5],  # Top 5 results
                        "relevance": "high"
                    })
            
            # Check for product category matches
            query_lower = new_query.lower()
            product_keywords = ["iphone", "macbook", "nintendo", "laptop", "phone", "game"]
            
            for keyword in product_keywords:
                if keyword in query_lower:
                    # Find cached searches with same product category
                    pattern_query = f"*{keyword}*"
                    related_cache = self.find_cached_by_pattern(pattern_query)
                    
                    if related_cache:
                        suggestions.append({
                            "type": "category_related",
                            "source": f"Cached {keyword} searches",
                            "results": related_cache[:3],  # Top 3 results
                            "relevance": "medium"
                        })
                        break
            
            logger.info(f"📋 Found {len(suggestions)} contextual cache suggestions")
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting contextual suggestions: {e}")
            return suggestions
    
    def find_cached_by_pattern(self, pattern: str, limit: int = 10) -> List[Dict]:
        """
        Find cached results matching a pattern
        
        Args:
            pattern: Search pattern
            limit: Maximum results to return
            
        Returns:
            List of matching cached results
        """
        results = []
        
        try:
            search_keys = self.redis_client.keys("search:*")
            
            for key in search_keys[:limit]:
                cached_data = self.redis_client.get(key)
                if not cached_data:
                    continue
                
                try:
                    data = json.loads(cached_data)
                    query = data.get("query", "").lower()
                    
                    # Simple pattern matching
                    pattern_clean = pattern.replace("*", "").lower()
                    if pattern_clean in query:
                        results.extend(data.get("results", [])[:2])  # Top 2 from each
                        
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            logger.error(f"Error finding cached patterns: {e}")
        
        return results[:limit]
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get detailed cache usage statistics
        
        Returns:
            Cache statistics dictionary
        """
        stats = {
            "total_keys": 0,
            "search_cache": {"count": 0, "total_results": 0},
            "session_data": {"count": 0, "active_sessions": 0},
            "llm_cache": {"count": 0, "estimated_savings": 0},
            "cache_hit_potential": 0.0
        }
        
        try:
            all_keys = self.redis_client.keys("*")
            stats["total_keys"] = len(all_keys)
            
            # Analyze search cache
            search_keys = [k for k in all_keys if k.startswith("search:")]
            stats["search_cache"]["count"] = len(search_keys)
            
            total_results = 0
            for key in search_keys:
                data = self.redis_client.get(key)
                if data:
                    try:
                        parsed = json.loads(data)
                        total_results += len(parsed.get("results", []))
                    except:
                        pass
            
            stats["search_cache"]["total_results"] = total_results
            
            # Analyze sessions
            session_keys = [k for k in all_keys if k.startswith("session:")]
            stats["session_data"]["count"] = len(session_keys)
            
            # Analyze LLM cache (hash keys)
            llm_keys = [k for k in all_keys if len(k) == 32 and k.isalnum()]
            stats["llm_cache"]["count"] = len(llm_keys)
            
            # Estimate cache hit potential
            if stats["search_cache"]["count"] > 0:
                stats["cache_hit_potential"] = min(0.9, stats["search_cache"]["count"] / 10.0)
            
            logger.info(f"📊 Cache statistics: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache statistics: {e}")
            return stats
    
    def optimize_query_execution(self, query: str, session_id: str) -> Dict[str, Any]:
        """
        Optimize query execution using available cache
        
        Args:
            query: Search query
            session_id: Current session ID
            
        Returns:
            Optimization strategy and cached data
        """
        optimization = {
            "strategy": "full_search",  # Default
            "cached_data": None,
            "suggestions": [],
            "cache_hit": False,
            "estimated_time_saved": 0
        }
        
        try:
            # 1. Check for exact cache hit
            cache_key = self._generate_cache_key(query)
            cached_result = self.cache_manager.get_cached_search(query)
            
            if cached_result:
                optimization["strategy"] = "cache_hit"
                optimization["cached_data"] = cached_result
                optimization["cache_hit"] = True
                optimization["estimated_time_saved"] = 5  # seconds
                logger.info(f"🎯 Cache hit for query: '{query}'")
                return optimization
            
            # 2. Check for similar queries
            similar = self.analyze_query_similarity(query, threshold=0.75)
            if similar:
                optimization["strategy"] = "similar_cache"
                optimization["cached_data"] = similar["results"]
                optimization["estimated_time_saved"] = 3
                logger.info(f"🔄 Using similar cached query: '{similar['query']}'")
                return optimization
            
            # 3. Get contextual suggestions
            suggestions = self.get_contextual_cache_suggestions(session_id, query)
            if suggestions:
                optimization["strategy"] = "contextual_cache"
                optimization["suggestions"] = suggestions
                optimization["estimated_time_saved"] = 1
                logger.info(f"💡 Found {len(suggestions)} contextual suggestions")
            
            return optimization
            
        except Exception as e:
            logger.error(f"Error optimizing query execution: {e}")
            return optimization
    
    def _generate_cache_key(self, query: str) -> str:
        """Generate cache key for query"""
        query_normalized = query.lower().strip()
        return f"search:{hashlib.md5(query_normalized.encode()).hexdigest()[:16]}"


def get_cache_optimizer() -> CacheOptimizer:
    """Get CacheOptimizer instance"""
    return CacheOptimizer()
