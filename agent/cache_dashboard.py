"""
Cache Management Dashboard
Provides insights and management for Redis Cloud cache
"""

import asyncio
from utils.cache_optimizer import get_cache_optimizer
from utils.redis_client import get_redis_client
from utils.session_manager import SessionManager
import json
from datetime import datetime


class CacheDashboard:
    """
    Dashboard for monitoring and managing Redis Cloud cache
    """
    
    def __init__(self):
        self.cache_optimizer = get_cache_optimizer()
        self.redis_client = get_redis_client()
        self.session_manager = SessionManager()
    
    def display_cache_overview(self):
        """Display comprehensive cache overview"""
        print("🗄️  Redis Cloud Cache Dashboard")
        print("=" * 60)
        
        # Get statistics
        stats = self.cache_optimizer.get_cache_statistics()
        
        print(f"📊 Cache Overview:")
        print(f"   Total Keys: {stats['total_keys']}")
        print(f"   Search Cache: {stats['search_cache']['count']} queries")
        print(f"   Total Deals Cached: {stats['search_cache']['total_results']}")
        print(f"   Active Sessions: {stats['session_data']['count']}")
        print(f"   LLM Responses Cached: {stats['llm_cache']['count']}")
        print(f"   Cache Hit Potential: {stats['cache_hit_potential']:.0%}")
        
        # Show memory usage
        if self.redis_client:
            info = self.redis_client.info()
            memory_used = info.get('used_memory_human', 'Unknown')
            print(f"   Memory Used: {memory_used}")
            print(f"   Connected Clients: {info.get('connected_clients', 0)}")
    
    def show_recent_searches(self, limit: int = 5):
        """Show recent cached searches"""
        print(f"\n🔍 Recent Cached Searches (Top {limit}):")
        print("-" * 40)
        
        try:
            search_keys = self.redis_client.keys("search:*")
            
            # Get search data with timestamps
            searches = []
            for key in search_keys:
                data = self.redis_client.get(key)
                if data:
                    try:
                        parsed = json.loads(data)
                        searches.append({
                            "key": key,
                            "query": parsed.get("query", "Unknown"),
                            "results_count": len(parsed.get("results", [])),
                            "timestamp": parsed.get("timestamp", "")
                        })
                    except:
                        continue
            
            # Sort by timestamp if available
            searches.sort(key=lambda x: x["timestamp"] if x["timestamp"] else "", reverse=True)
            
            for i, search in enumerate(searches[:limit], 1):
                print(f"   {i}. Query: '{search['query']}'")
                print(f"      Results: {search['results_count']} deals")
                if search["timestamp"]:
                    print(f"      Cached: {search['timestamp'][:19]}")
                print(f"      Key: {search['key']}")
                print()
                
        except Exception as e:
            print(f"   Error retrieving searches: {e}")
    
    def show_active_sessions(self, limit: int = 3):
        """Show active sessions with conversation data"""
        print(f"\n👤 Active Sessions (Top {limit}):")
        print("-" * 40)
        
        try:
            session_keys = self.redis_client.keys("session:*")
            
            for i, key in enumerate(session_keys[:limit], 1):
                data = self.redis_client.get(key)
                if data:
                    try:
                        session_info = json.loads(data)
                        session_id = session_info.get("session_id", "Unknown")
                        created = session_info.get("created_at", "")
                        
                        print(f"   {i}. Session: {session_id}")
                        print(f"      Created: {created[:19] if created else 'Unknown'}")
                        
                        # Get context data
                        context_key = f"context:{session_id}"
                        context_data = self.redis_client.get(context_key)
                        if context_data:
                            context_info = json.loads(context_data)
                            topics = context_info.get("topics", [])
                            if topics:
                                print(f"      Topics: {', '.join(topics[:3])}")
                        
                        print()
                        
                    except:
                        continue
                        
        except Exception as e:
            print(f"   Error retrieving sessions: {e}")
    
    def find_cache_opportunities(self, query: str, session_id: str = "demo"):
        """Demonstrate cache optimization for a query"""
        print(f"\n🎯 Cache Optimization for: '{query}'")
        print("-" * 50)
        
        optimization = self.cache_optimizer.optimize_query_execution(query, session_id)
        
        print(f"Strategy: {optimization['strategy']}")
        print(f"Cache Hit: {'✅' if optimization['cache_hit'] else '❌'}")
        print(f"Time Saved: {optimization['estimated_time_saved']} seconds")
        
        if optimization['cached_data']:
            if isinstance(optimization['cached_data'], list):
                print(f"Cached Results: {len(optimization['cached_data'])} deals available")
            else:
                print("Cached Results: Available")
        
        if optimization['suggestions']:
            print(f"Suggestions: {len(optimization['suggestions'])} contextual matches")
            for suggestion in optimization['suggestions']:
                print(f"  - {suggestion['type']}: {suggestion['source']}")
    
    def cleanup_expired_cache(self):
        """Clean up expired or old cache entries"""
        print(f"\n🧹 Cache Cleanup Report:")
        print("-" * 30)
        
        try:
            all_keys = self.redis_client.keys("*")
            expired_count = 0
            
            for key in all_keys:
                ttl = self.redis_client.ttl(key)
                if ttl == -1:  # No expiration set
                    # Set default expiration for keys without TTL
                    if key.startswith("search:"):
                        self.redis_client.expire(key, 3600)  # 1 hour
                        expired_count += 1
                    elif key.startswith("session:"):
                        self.redis_client.expire(key, 86400)  # 24 hours
                        expired_count += 1
            
            print(f"✅ Set expiration for {expired_count} keys")
            print(f"📊 Total keys managed: {len(all_keys)}")
            
        except Exception as e:
            print(f"❌ Cleanup error: {e}")


async def run_cache_demo():
    """Run comprehensive cache demonstration"""
    dashboard = CacheDashboard()
    
    # Show overview
    dashboard.display_cache_overview()
    
    # Show recent activity
    dashboard.show_recent_searches()
    dashboard.show_active_sessions()
    
    # Test cache optimization
    test_queries = [
        "Find iPhone 15 deals",
        "Nintendo Switch discounts", 
        "MacBook Pro 2024 best price",
        "cheap wireless headphones"
    ]
    
    print(f"\n🧪 Cache Optimization Tests:")
    print("=" * 40)
    
    for query in test_queries:
        dashboard.find_cache_opportunities(query)
        print()
    
    # Cleanup
    dashboard.cleanup_expired_cache()


if __name__ == "__main__":
    asyncio.run(run_cache_demo())
