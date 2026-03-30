import time
from fastapi import HTTPException
from cache.redis_client import get_redis
from config import RATE_LIMIT_POSTS_PER_MINUTE


async def check_rate_limit(user_id: str, action: str = "post"):
    """Sliding window rate limiter using Redis sorted sets."""
    r = get_redis()
    key = f"rate_limit:{action}:{user_id}"
    now = time.time()
    window_start = now - 60

    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, 60)
    results = await pipe.execute()

    request_count = results[2]
    if request_count > RATE_LIMIT_POSTS_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later.",
        )
