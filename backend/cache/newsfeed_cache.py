from cache.redis_client import get_redis
from config import NEWSFEED_CACHE_LIMIT

NEWSFEED_PREFIX = "newsfeed:"


async def add_post_to_feed(user_id: str, post_id: str, timestamp: float):
    r = get_redis()
    key = f"{NEWSFEED_PREFIX}{user_id}"
    await r.zadd(key, {post_id: timestamp})
    # Trim to keep only the latest entries
    await r.zremrangebyrank(key, 0, -(NEWSFEED_CACHE_LIMIT + 1))


async def get_feed_post_ids(user_id: str, offset: int = 0, limit: int = 20) -> list[str]:
    r = get_redis()
    key = f"{NEWSFEED_PREFIX}{user_id}"
    # Reverse chronological: highest score (newest) first
    post_ids = await r.zrevrange(key, offset, offset + limit - 1)
    return post_ids
