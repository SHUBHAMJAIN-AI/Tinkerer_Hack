"""Basic connection example with error handling.
"""

import redis
import sys

try:
    print("Connecting to Redis Cloud...")
    r = redis.Redis(
        host='redis-15355.c80.us-east-1-2.ec2.cloud.redislabs.com',
        port=15355,
        decode_responses=True,
        username="default",
        password="lGiExWuz4PTznA21XE3DSgfCWLhyZcNi",
        socket_timeout=10,
        socket_connect_timeout=10
    )
    
    print("Testing connection with ping...")
    ping_result = r.ping()
    print(f"Ping result: {ping_result}")
    
    print("Setting test key...")
    success = r.set('foo', 'bar')
    print(f"Set operation success: {success}")
    
    print("Getting test key...")
    result = r.get('foo')
    print(f"Retrieved value: {result}")
    
    # Test connection info
    print("Getting Redis info...")
    info = r.info()
    print(f"Redis version: {info.get('redis_version', 'Unknown')}")
    print(f"Used memory: {info.get('used_memory_human', 'Unknown')}")
    print(f"Connected clients: {info.get('connected_clients', 'Unknown')}")
    
    print("✅ Redis connection test successful!")
    
except redis.ConnectionError as e:
    print(f"❌ Connection error: {e}")
    sys.exit(1)
except redis.TimeoutError as e:
    print(f"❌ Timeout error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
