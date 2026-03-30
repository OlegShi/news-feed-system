from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGODB_URL, MONGODB_DB

client: AsyncIOMotorClient = None
db = None


async def connect_mongodb():
    global client, db
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB]
    await db.users.create_index("username", unique=True)
    await db.users.create_index("user_id", unique=True)
    await db.posts.create_index("post_id", unique=True)
    await db.posts.create_index([("user_id", 1), ("created_at", -1)])


async def close_mongodb():
    global client
    if client:
        client.close()


def get_db():
    return db
