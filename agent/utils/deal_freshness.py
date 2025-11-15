# filepath: /Users/shubhamjain/Documents/Ai_tinkerers_hack/dealfinder-ai/agent/utils/deal_freshness.py
"""
Deal Freshness Manager for Redis Cloud
Implements 24-hour deal freshness validation and smart cache invalidation
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from utils.redis_client import get_redis_client
from utils.cache import CacheManager
import hashlib

logger = logging.getLogger(__name__)


class DealFreshnessManager:
    """
    Manages deal freshness and cache invalidation for optimal user experience
    Implements 24-hour maximum age policy for deal data
    """
    
    # Deal freshness thresholds (in hours)
    MAX_DEAL_AGE = 24         # Maximum age - deals expire after 24 hours
    FRESH_THRESHOLD = 4       # < 4 hours = fresh
    GOOD_THRESHOLD = 12       # 4-12 hours = good quality
    STALE_THRESHOLD = 24      # 12-24 hours = stale but usable
    
    # Product categories with different freshness requirements
    CATEGORY_THRESHOLDS = {
        "electronics": 4,     # Electronics change prices frequently - 4h TTL
        "gaming": 8,          # Gaming deals change moderately - 8h TTL
        "fashion": 12,        # Fashion deals are more stable - 12h TTL
        "books": 24,          # Books rarely change prices - 24h TTL
        "home": 16,           # Home goods moderate changes - 16h TTL
        "software": 6,        # Software licenses change - 6h TTL
        "sports": 12,         # Sports equipment deals - 12h TTL
        "default": 24         # Default 24 hours maximum age
    }
    
    # Keywords that indicate price-sensitive searches (shorter TTL)
    PRICE_SENSITIVE_KEYWORDS = [
        "cheapest", "lowest price", "best deal", "discount", "sale", 
        "clearance", "bargain", "hot deal", "limited time", "cheap",
        "affordable", "budget", "markdown", "reduced", "best price"
    ]
    
    def __init__(self):
        self.redis_client = get_redis_client()
        self.cache_manager = CacheManager()
    
    def should_refresh_cache(self, query: str, category: str = None) -> Dict[str, Any]:
        """
        Determine if cache should be refreshed based on 24-hour freshness policy
        
        Args:
            query: Search query
            category: Product category (optional)
            
        Returns:
            Dictionary with refresh decision and reasoning
        """
        try:
            # Get cache key and data
            cache_key = self._get_cache_key(query)
            cached_data = self.redis_client.get(cache_key)
            
            if not cached_data:
                return {
                    "should_refresh": True,
                    "reason": "No cached data found",
                    "age_hours": 0,
                    "freshness_level": "expired"
                }
            
            # Parse cached data
            data = json.loads(cached_data)
            cached_timestamp = data.get("timestamp", 0)
            cache_age_hours = (datetime.now().timestamp() - cached_timestamp) / 3600
            
            # Determine category if not provided
            if category is None:
                category = self._detect_category(query)
            
            # Get category-specific threshold
            category_threshold = self.CATEGORY_THRESHOLDS.get(category, self.CATEGORY_THRESHOLDS["default"])
            
            # Check if price-sensitive (gets 4-hour TTL regardless of category)
            is_price_sensitive = self._is_price_sensitive(query)
            if is_price_sensitive:
                category_threshold = 4
            
            # Determine freshness level and refresh decision
            if cache_age_hours >= self.MAX_DEAL_AGE:
                # Deals over 24 hours are always refreshed
                return {
                    "should_refresh": True,
                    "reason": f"Deals are {cache_age_hours:.1f} hours old (max: {self.MAX_DEAL_AGE}h)",
                    "age_hours": cache_age_hours,
                    "freshness_level": "expired",
                    "warning": "⚠️ These deals may no longer be available"
                }
            elif cache_age_hours >= category_threshold:
                # Category-specific threshold exceeded
                return {
                    "should_refresh": True,
                    "reason": f"Category '{category}' threshold exceeded ({cache_age_hours:.1f}h > {category_threshold}h)",
                    "age_hours": cache_age_hours,
                    "freshness_level": "stale" if cache_age_hours < self.STALE_THRESHOLD else "expired",
                    "warning": f"💡 Consider refreshing for current {category} deals"
                }
            elif cache_age_hours >= self.STALE_THRESHOLD:
                # In stale range but within category threshold
                return {
                    "should_refresh": False,
                    "reason": f"Stale but within category threshold",
                    "age_hours": cache_age_hours,
                    "freshness_level": "stale",
                    "warning": f"⚠️ Deals are {int(cache_age_hours)} hours old"
                }
            elif cache_age_hours >= self.GOOD_THRESHOLD:
                # Good quality range
                return {
                    "should_refresh": False,
                    "reason": f"Good quality deals",
                    "age_hours": cache_age_hours,
                    "freshness_level": "good",
                    "warning": None
                }
            else:
                # Fresh deals
                return {
                    "should_refresh": False,
                    "reason": f"Fresh deals",
                    "age_hours": cache_age_hours,
                    "freshness_level": "fresh",
                    "warning": None
                }
                
        except Exception as e:
            logger.error(f"Error checking cache freshness: {e}")
            return {
                "should_refresh": True,
                "reason": f"Error checking cache: {e}",
                "age_hours": 0,
                "freshness_level": "expired"
            }
    
    def validate_deal_freshness(self, cached_data: Dict, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Validate if cached deal data is still fresh enough to use
        
        Args:
            cached_data: Cached deal data with timestamp
            max_age_hours: Maximum acceptable age in hours (default: 24)
            
        Returns:
            Validation result with freshness status
        """
        try:
            timestamp = cached_data.get("timestamp", 0)
            age_hours = (datetime.now().timestamp() - timestamp) / 3600
            
            is_fresh = age_hours < max_age_hours
            
            return {
                "is_fresh": is_fresh,
                "age_hours": age_hours,
                "max_age_hours": max_age_hours,
                "status": self._get_freshness_status(age_hours),
                "recommendation": "use" if is_fresh else "refresh"
            }
            
        except Exception as e:
            logger.error(f"Error validating deal freshness: {e}")
            return {
                "is_fresh": False,
                "age_hours": 999,
                "max_age_hours": max_age_hours,
                "status": "expired",
                "recommendation": "refresh"
            }
    
    def get_optimal_ttl(self, query: str, category: str = None) -> int:
        """
        Calculate optimal TTL based on query characteristics
        
        Args:
            query: Search query
            category: Product category (optional)
            
        Returns:
            TTL in seconds
        """
        try:
            # Detect category if not provided
            if category is None:
                category = self._detect_category(query)
            
            # Get base TTL from category
            base_hours = self.CATEGORY_THRESHOLDS.get(category, self.CATEGORY_THRESHOLDS["default"])
            
            # Reduce TTL for price-sensitive queries
            if self._is_price_sensitive(query):
                base_hours = min(base_hours, 4)
            
            # Convert to seconds
            ttl_seconds = base_hours * 3600
            
            logger.info(f"📅 Optimal TTL for '{query}' (category: {category}): {base_hours}h ({ttl_seconds}s)")
            return ttl_seconds
            
        except Exception as e:
            logger.error(f"Error calculating optimal TTL: {e}")
            return 86400  # Default 24 hours
    
    def _detect_category(self, query: str) -> str:
        """Detect product category from query"""
        query_lower = query.lower()
        
        # Electronics keywords
        electronics = ["iphone", "macbook", "laptop", "computer", "tablet", "phone", "tv", "camera", "headphones"]
        if any(kw in query_lower for kw in electronics):
            return "electronics"
        
        # Gaming keywords
        gaming = ["nintendo", "playstation", "xbox", "switch", "ps5", "game", "gaming"]
        if any(kw in query_lower for kw in gaming):
            return "gaming"
        
        # Fashion keywords
        fashion = ["shoes", "clothing", "shirt", "pants", "dress", "jacket", "jeans"]
        if any(kw in query_lower for kw in fashion):
            return "fashion"
        
        # Software keywords
        software = ["software", "app", "license", "subscription", "microsoft", "adobe"]
        if any(kw in query_lower for kw in software):
            return "software"
        
        # Home keywords
        home = ["furniture", "kitchen", "appliance", "bed", "chair", "table"]
        if any(kw in query_lower for kw in home):
            return "home"
        
        # Sports keywords
        sports = ["sports", "fitness", "gym", "workout", "running", "bike"]
        if any(kw in query_lower for kw in sports):
            return "sports"
        
        return "default"
    
    def _is_price_sensitive(self, query: str) -> bool:
        """Check if query is price-sensitive (needs shorter TTL)"""
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in self.PRICE_SENSITIVE_KEYWORDS)
    
    def _get_freshness_status(self, age_hours: float) -> str:
        """Get freshness status label"""
        if age_hours < self.FRESH_THRESHOLD:
            return "fresh"
        elif age_hours < self.GOOD_THRESHOLD:
            return "good"
        elif age_hours < self.STALE_THRESHOLD:
            return "stale"
        else:
            return "expired"
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key for query"""
        query_normalized = query.lower().strip()
        return f"search:{hashlib.md5(query_normalized.encode()).hexdigest()[:16]}"
    
    def add_freshness_metadata(self, results: List[Dict], query: str) -> List[Dict]:
        """
        Add freshness metadata to search results
        
        Args:
            results: List of deal results
            query: Original search query
            
        Returns:
            Results with freshness metadata
        """
        try:
            current_time = datetime.now().timestamp()
            category = self._detect_category(query)
            is_price_sensitive = self._is_price_sensitive(query)
            
            for result in results:
                result["freshness_metadata"] = {
                    "cached_at": current_time,
                    "category": category,
                    "is_price_sensitive": is_price_sensitive,
                    "recommended_refresh_hours": self.CATEGORY_THRESHOLDS.get(category, 24),
                    "max_age_hours": self.MAX_DEAL_AGE
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error adding freshness metadata: {e}")
            return results
    
    def check_deals_validity(self, cached_data: Dict) -> Dict[str, Any]:
        """
        Check if cached deals are still valid (24-hour rule)
        
        Args:
            cached_data: Cached search results
            
        Returns:
            Validity check results
        """
        try:
            results = cached_data.get("results", [])
            timestamp = cached_data.get("timestamp", 0)
            age_hours = (datetime.now().timestamp() - timestamp) / 3600
            
            # Check if deals exceed 24-hour limit
            if age_hours >= self.MAX_DEAL_AGE:
                return {
                    "valid": False,
                    "reason": f"Deals are {age_hours:.1f} hours old (exceeds 24h limit)",
                    "action": "refresh_required",
                    "age_hours": age_hours,
                    "warning": "⚠️ These deals may no longer be available or prices may have changed"
                }
            
            # Check metadata if available
            if results and isinstance(results, list) and len(results) > 0:
                first_result = results[0]
                if "freshness_metadata" in first_result:
                    metadata = first_result["freshness_metadata"]
                    recommended_hours = metadata.get("recommended_refresh_hours", 24)
                    
                    if age_hours >= recommended_hours:
                        return {
                            "valid": True,
                            "reason": f"Deals are {age_hours:.1f}h old, approaching refresh threshold",
                            "action": "consider_refresh",
                            "age_hours": age_hours,
                            "warning": f"�� These deals are {int(age_hours)} hours old"
                        }
            
            # Deals are fresh
            return {
                "valid": True,
                "reason": f"Deals are fresh ({age_hours:.1f}h old)",
                "action": "use_cache",
                "age_hours": age_hours,
                "warning": None
            }
            
        except Exception as e:
            logger.error(f"Error checking deals validity: {e}")
            return {
                "valid": False,
                "reason": f"Error validating deals: {e}",
                "action": "refresh_required",
                "age_hours": 999,
                "warning": "⚠️ Unable to verify deal freshness"
            }


def get_deal_freshness_manager() -> DealFreshnessManager:
    """Get DealFreshnessManager instance"""
    return DealFreshnessManager()
