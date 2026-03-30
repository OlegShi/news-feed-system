import json
from cache.redis_client import get_redis

USER_CACHE_PREFIX = "user:"
USER_CACHE_TTL = 3600  # 1 hour


async def set_user(user_id: str, user_data: dict):
    r = get_redis()
    key = f"{USER_CACHE_PREFIX}{user_id}"
    await r.setex(key, USER_CACHE_TTL, json.dumps(user_data, default=str))


async def get_user(user_id: str) -> dict | None:
    r = get_redis()
    key = f"{USER_CACHE_PREFIX}{user_id}"
    data = await r.get(key)
    if data:
        return json.loads(data)
    return None
