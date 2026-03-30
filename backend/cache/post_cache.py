import json
from cache.redis_client import get_redis

POST_CACHE_PREFIX = "post:"
POST_CACHE_TTL = 3600  # 1 hour


async def set_post(post_id: str, post_data: dict):
    r = get_redis()
    key = f"{POST_CACHE_PREFIX}{post_id}"
    await r.setex(key, POST_CACHE_TTL, json.dumps(post_data, default=str))


async def get_post(post_id: str) -> dict | None:
    r = get_redis()
    key = f"{POST_CACHE_PREFIX}{post_id}"
    data = await r.get(key)
    if data:
        return json.loads(data)
    return None
