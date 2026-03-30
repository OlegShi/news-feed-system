import uuid
from datetime import datetime, timezone
from database.mongodb import get_db
from cache.post_cache import set_post, get_post


async def create_post(user_id: str, content: str) -> dict:
    db = get_db()
    post_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    post_doc = {
        "post_id": post_id,
        "user_id": user_id,
        "content": content,
        "created_at": now,
    }
    await db.posts.insert_one(post_doc)

    cache_data = {
        "post_id": post_id,
        "user_id": user_id,
        "content": content,
        "created_at": str(now),
    }
    await set_post(post_id, cache_data)

    return cache_data


async def get_post_by_id(post_id: str) -> dict | None:
    cached = await get_post(post_id)
    if cached:
        return cached

    db = get_db()
    post = await db.posts.find_one({"post_id": post_id}, {"_id": 0})
    if post:
        cache_data = {
            "post_id": post["post_id"],
            "user_id": post["user_id"],
            "content": post["content"],
            "created_at": str(post["created_at"]),
        }
        await set_post(post_id, cache_data)
        return cache_data
    return None
