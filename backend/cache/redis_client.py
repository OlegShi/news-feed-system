import redis.asyncio as redis
from config import REDIS_URL

redis_client: redis.Redis = None


async def connect_redis():
    global redis_client
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()


def get_redis():
    return redis_client
