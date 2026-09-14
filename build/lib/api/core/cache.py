import redis
import os
import json
from functools import wraps

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Setup redis client
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def semantic_cache(ttl_seconds: int = 3600):
    """
    A simple decorator for caching LLM responses in Redis.
    In a real semantic caching scenario, we would compute the embedding 
    of the query and check for cosine similarity within a threshold.
    For demonstration, this caches exact prompt matches.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a deterministic cache key from arguments
            cache_key = f"llm_cache:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            cached_response = redis_client.get(cache_key)
            if cached_response:
                print(f"Cache hit for {cache_key}")
                return json.loads(cached_response)
                
            response = func(*args, **kwargs)
            
            # Cache the new response
            if response:
                redis_client.setex(cache_key, ttl_seconds, json.dumps(response))
                
            return response
        return wrapper
    return decorator
