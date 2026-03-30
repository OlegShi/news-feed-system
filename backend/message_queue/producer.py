import json
from aiokafka import AIOKafkaProducer
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_FANOUT_TOPIC

producer: AIOKafkaProducer = None


async def connect_kafka_producer():
    global producer
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
    )
    await producer.start()


async def close_kafka_producer():
    global producer
    if producer:
        await producer.stop()


async def send_fanout_message(post_id: str, user_id: str, friend_ids: list[str], timestamp: float):
    global producer
    if not producer:
        return
    message = {
        "post_id": post_id,
        "user_id": user_id,
        "friend_ids": friend_ids,
        "timestamp": timestamp,
    }
    await producer.send_and_wait(KAFKA_FANOUT_TOPIC, message)
