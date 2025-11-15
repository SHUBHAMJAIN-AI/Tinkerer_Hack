"""
Session Management Utility
Handles conversation context and session persistence with Redis
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from utils.redis_client import get_redis_client
from redis_config import CACHE_TTL_SESSIONS, ENABLE_SESSION_PERSISTENCE

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages user sessions and conversation context"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        self.ttl = CACHE_TTL_SESSIONS
        
    def _get_session_key(self, session_id: str) -> str:
        """Generate Redis key for session"""
        return f"session:{session_id}"
    
    def _get_context_key(self, session_id: str) -> str:
        """Generate Redis key for conversation context"""
        return f"context:{session_id}"
    
    def save_session(self, session_id: str, state: Dict[str, Any]) -> bool:
        """
        Save session state to Redis
        
        Args:
            session_id: Unique session identifier
            state: Current agent state
            
        Returns:
            True if saved successfully
        """
        if not ENABLE_SESSION_PERSISTENCE or not self.redis_client:
            return False
            
        try:
            session_key = self._get_session_key(session_id)
            
            # Extract relevant session data
            session_data = {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "agent_status": state.get("agent_status", {}),
                "cache_hits": state.get("cached_queries", {}),
                "user_preferences": state.get("user_preferences", {}),
                "total_queries": state.get("total_queries", 0)
            }
            
            # Save session data
            self.redis_client.setex(
                session_key,
                self.ttl,
                json.dumps(session_data)
            )
            
            logger.info(f"💾 Session {session_id} saved to Redis")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save session {session_id}: {str(e)}")
            return False
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load session state from Redis
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Session data dict or None if not found
        """
        if not ENABLE_SESSION_PERSISTENCE or not self.redis_client:
            return None
            
        try:
            session_key = self._get_session_key(session_id)
            session_data = self.redis_client.get(session_key)
            
            if session_data:
                data = json.loads(session_data)
                logger.info(f"📥 Session {session_id} loaded from Redis")
                return data
                
        except Exception as e:
            logger.error(f"❌ Failed to load session {session_id}: {str(e)}")
            
        return None
    
    def save_conversation_context(self, session_id: str, messages: List[Any], 
                                context_summary: Optional[str] = None) -> bool:
        """
        Save conversation context for contextual understanding
        
        Args:
            session_id: Unique session identifier
            messages: List of conversation messages
            context_summary: Optional summary of conversation context
            
        Returns:
            True if saved successfully
        """
        if not ENABLE_SESSION_PERSISTENCE or not self.redis_client:
            return False
            
        try:
            context_key = self._get_context_key(session_id)
            
            # Extract conversation context
            context_data = {
                "session_id": session_id,
                "updated_at": datetime.now().isoformat(),
                "message_count": len(messages),
                "context_summary": context_summary,
                "recent_topics": self._extract_topics_from_messages(messages),
                "last_search_query": self._get_last_search_query(messages),
                "conversation_history": self._serialize_messages(messages[-10:])  # Keep last 10 messages
            }
            
            # Save context data
            self.redis_client.setex(
                context_key,
                self.ttl,
                json.dumps(context_data)
            )
            
            logger.info(f"💬 Conversation context saved for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save context for session {session_id}: {str(e)}")
            return False
    
    def load_conversation_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load conversation context for contextual understanding
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Context data dict or None if not found
        """
        if not ENABLE_SESSION_PERSISTENCE or not self.redis_client:
            return None
            
        try:
            context_key = self._get_context_key(session_id)
            context_data = self.redis_client.get(context_key)
            
            if context_data:
                data = json.loads(context_data)
                logger.info(f"📖 Conversation context loaded for session {session_id}")
                return data
                
        except Exception as e:
            logger.error(f"❌ Failed to load context for session {session_id}: {str(e)}")
            
        return None
    
    def get_contextual_prompt_addition(self, session_id: str) -> str:
        """
        Get contextual information to add to LLM prompts
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Contextual prompt addition string
        """
        context = self.load_conversation_context(session_id)
        if not context:
            return ""
        
        prompt_addition = "\n\n**CONVERSATION CONTEXT:**\n"
        
        # Add context summary
        if context.get("context_summary"):
            prompt_addition += f"Previous conversation: {context['context_summary']}\n"
        
        # Add recent topics
        if context.get("recent_topics"):
            topics = ", ".join(context["recent_topics"])
            prompt_addition += f"Recent topics discussed: {topics}\n"
        
        # Add last search query
        if context.get("last_search_query"):
            prompt_addition += f"Last search was for: {context['last_search_query']}\n"
        
        prompt_addition += "\nUse this context to understand references like 'cheaper', 'similar', 'that product', etc.\n"
        
        return prompt_addition
    
    def update_session_activity(self, session_id: str) -> bool:
        """
        Update last activity timestamp for session
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if updated successfully
        """
        if not ENABLE_SESSION_PERSISTENCE or not self.redis_client:
            return False
            
        try:
            session_key = self._get_session_key(session_id)
            session_data = self.redis_client.get(session_key)
            
            if session_data:
                data = json.loads(session_data)
                data["last_activity"] = datetime.now().isoformat()
                
                self.redis_client.setex(
                    session_key,
                    self.ttl,
                    json.dumps(data)
                )
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to update session activity: {str(e)}")
            
        return False
    
    def _extract_topics_from_messages(self, messages: List[Any]) -> List[str]:
        """Extract key topics from conversation messages"""
        topics = []
        
        for msg in messages[-5:]:  # Look at last 5 messages
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                content = msg.content.lower()
                
                # Extract product categories and brands
                keywords = [
                    'iphone', 'laptop', 'headphones', 'tv', 'phone', 'computer',
                    'apple', 'samsung', 'sony', 'dell', 'hp', 'nike', 'adidas',
                    'amazon', 'walmart', 'best buy', 'target', 'costco'
                ]
                
                for keyword in keywords:
                    if keyword in content and keyword not in topics:
                        topics.append(keyword)
                        
        return topics[:5]  # Return top 5 topics
    
    def _get_last_search_query(self, messages: List[Any]) -> Optional[str]:
        """Extract the last search query from messages"""
        for msg in reversed(messages):
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                content = msg.content.lower()
                
                # Look for search-related keywords
                search_indicators = ['find', 'search', 'look for', 'deals on', 'price of']
                
                for indicator in search_indicators:
                    if indicator in content:
                        return msg.content
                        
        return None
    
    def _serialize_messages(self, messages: List[Any]) -> List[Dict[str, str]]:
        """Serialize messages for storage"""
        serialized = []
        
        for msg in messages:
            if hasattr(msg, 'content') and hasattr(msg, '__class__'):
                serialized.append({
                    'type': msg.__class__.__name__,
                    'content': str(msg.content)[:500],  # Limit content length
                    'timestamp': datetime.now().isoformat()
                })
                
        return serialized
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions (Redis TTL handles this automatically)
        
        Returns:
            Number of sessions cleaned (always 0 for Redis TTL)
        """
        # Redis TTL automatically handles cleanup
        logger.info("🧹 Session cleanup handled by Redis TTL")
        return 0


# Global session manager instance
_session_manager = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
