"""
Fanout Worker — Kafka consumer that processes fanout messages
and updates friend news feed caches.

Run as standalone process:
    python -m queue.worker
"""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import redis.asyncio as redis
from aiokafka import AIOKafkaConsumer
from config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_FANOUT_TOPIC,
    REDIS_URL,
    NEWSFEED_CACHE_LIMIT,
)

NEWSFEED_PREFIX = "newsfeed:"


async def process_message(redis_client, message):
    data = json.loads(message.value.decode("utf-8"))
    post_id = data["post_id"]
    friend_ids = data["friend_ids"]
    timestamp = data["timestamp"]

    # Use pipeline for batch Redis writes
    pipe = redis_client.pipeline()
    for friend_id in friend_ids:
        key = f"{NEWSFEED_PREFIX}{friend_id}"
        pipe.zadd(key, {post_id: timestamp})
        pipe.zremrangebyrank(key, 0, -(NEWSFEED_CACHE_LIMIT + 1))
    await pipe.execute()
    print(f"Fanout complete: post {post_id} pushed to {len(friend_ids)} friends")


async def main():
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    consumer = AIOKafkaConsumer(
        KAFKA_FANOUT_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="fanout-workers",
        auto_offset_reset="earliest",
    )
    await consumer.start()
    print(f"Fanout worker started — consuming from '{KAFKA_FANOUT_TOPIC}'...")
    try:
        async for message in consumer:
            await process_message(redis_client, message)
    finally:
        await consumer.stop()
        await redis_client.close()


if __name__ == "__main__":
    asyncio.run(main())
