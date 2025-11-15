"""Test Redis Cloud connection.
"""

import redis
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test basic connection
def test_basic_connection():
    print("Testing basic Redis connection...")
    
    r = redis.Redis(
        host='redis-15355.c80.us-east-1-2.ec2.cloud.redislabs.com',
        port=15355,
        decode_responses=True,
        username="default",
        password="lGiExWuz4PTznA21XE3DSgfCWLhyZcNi",
    )
    
    try:
        # Test set/get
        success = r.set('test_foo', 'test_bar')
        print(f"Set operation success: {success}")
        
        result = r.get('test_foo')
        print(f"Get result: {result}")
        
        # Test ping
        ping_result = r.ping()
        print(f"Ping result: {ping_result}")
        
        # Clean up
        r.delete('test_foo')
        print("Basic connection test: ✅ SUCCESS")
        
        return True
        
    except Exception as e:
        print(f"Basic connection test: ❌ FAILED - {e}")
        return False

# Test URL-based connection (as used in our session manager)
def test_url_connection():
    print("\nTesting URL-based Redis connection...")
    
    redis_url = os.getenv('REDIS_URL', 'rediss://default:lGiExWuz4PTznA21XE3DSgfCWLhyZcNi@redis-15355.c80.us-east-1-2.ec2.cloud.redislabs.com:15355')
    
    try:
        r = redis.from_url(redis_url, decode_responses=True)
        
        # Test set/get
        success = r.set('test_session', '{"user_id": "test", "conversation": []}')
        print(f"Set session success: {success}")
        
        result = r.get('test_session')
        print(f"Get session result: {result}")
        
        # Test with TTL
        r.setex('test_ttl', 10, 'expires_in_10_seconds')
        ttl = r.ttl('test_ttl')
        print(f"TTL test: {ttl} seconds remaining")
        
        # Clean up
        r.delete('test_session', 'test_ttl')
        print("URL connection test: ✅ SUCCESS")
        
        return True
        
    except Exception as e:
        print(f"URL connection test: ❌ FAILED - {e}")
        return False

# Test our session manager
def test_session_manager():
    print("\nTesting SessionManager...")
    
    try:
        from utils.session_manager import SessionManager
        
        session_manager = SessionManager()
        
        # Create a test session
        test_session_id = "test_session_123"
        test_conversation = [
            {"role": "user", "content": "find iPhone deals"},
            {"role": "assistant", "content": "Here are some iPhone deals..."}
        ]
        
        # Save session
        session_manager.save_session(test_session_id, {
            "conversation": test_conversation,
            "last_query": "find iPhone deals",
            "user_preferences": {"budget": "$500"}
        })
        print("Session saved successfully")
        
        # Load session
        loaded_session = session_manager.load_session(test_session_id)
        print(f"Session loaded: {loaded_session is not None}")
        print(f"Conversation length: {len(loaded_session.get('conversation', []))}")
        
        # Test context generation
        context = session_manager.get_conversation_context(test_session_id)
        print(f"Context generated: {len(context)} characters")
        
        # Clean up
        session_manager.delete_session(test_session_id)
        print("SessionManager test: ✅ SUCCESS")
        
        return True
        
    except Exception as e:
        print(f"SessionManager test: ❌ FAILED - {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Redis Cloud Connection\n")
    
    basic_ok = test_basic_connection()
    url_ok = test_url_connection()
    session_ok = test_session_manager()
    
    print(f"\n📊 Test Results:")
    print(f"Basic Connection: {'✅' if basic_ok else '❌'}")
    print(f"URL Connection: {'✅' if url_ok else '❌'}")
    print(f"Session Manager: {'✅' if session_ok else '❌'}")
    
    if all([basic_ok, url_ok, session_ok]):
        print("\n🎉 All Redis tests passed! System is ready.")
    else:
        print("\n⚠️  Some tests failed. Check configuration.")
