"""Basic connection example.
"""

import redis

r = redis.Redis(
    host='redis-15355.c80.us-east-1-2.ec2.cloud.redislabs.com',
    port=15355,
    decode_responses=True,
    username="default",
    password="lGiExWuz4PTznA21XE3DSgfCWLhyZcNi",
)

success = r.set('foo', 'bar')
print(f"Set operation success: {success}")

result = r.get('foo')
print(f"Retrieved value: {result}")

# Test connection info
info = r.info()
print(f"Redis version: {info.get('redis_version', 'Unknown')}")
print(f"Used memory: {info.get('used_memory_human', 'Unknown')}")
