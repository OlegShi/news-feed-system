from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database.mongodb import connect_mongodb, close_mongodb
from database.graph_db import connect_neo4j, close_neo4j
from cache.redis_client import connect_redis, close_redis
from message_queue.producer import connect_kafka_producer, close_kafka_producer
from routes import feed, friends, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_mongodb()
    await connect_redis()
    await connect_neo4j()
    try:
        await connect_kafka_producer()
    except Exception as e:
        print(f"Warning: Kafka not available ({e}). Fanout disabled.")
    yield
    try:
        await close_kafka_producer()
    except Exception:
        pass
    await close_neo4j()
    await close_redis()
    await close_mongodb()


app = FastAPI(title="News Feed System", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/v1/auth", tags=["Auth"])
app.include_router(feed.router, prefix="/v1/me", tags=["Feed"])
app.include_router(friends.router, prefix="/v1/me", tags=["Friends"])
