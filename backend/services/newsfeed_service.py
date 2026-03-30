from cache.newsfeed_cache import get_feed_post_ids
from services.post_service import get_post_by_id
from cache.user_cache import get_user, set_user
from database.mongodb import get_db


async def get_newsfeed(user_id: str, offset: int = 0, limit: int = 20) -> list[dict]:
    """Build a fully hydrated news feed from cached post IDs."""
    post_ids = await get_feed_post_ids(user_id, offset, limit)

    feed = []
    for post_id in post_ids:
        post = await get_post_by_id(post_id)
        if not post:
            continue

        author = await _get_user_info(post["user_id"])

        feed.append({
            "post_id": post["post_id"],
            "user_id": post["user_id"],
            "username": author.get("username", "Unknown") if author else "Unknown",
            "content": post["content"],
            "created_at": post["created_at"],
        })

    return feed


async def _get_user_info(user_id: str) -> dict | None:
    cached = await get_user(user_id)
    if cached:
        return cached

    db = get_db()
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    if user:
        user_data = {
            "user_id": user["user_id"],
            "username": user["username"],
            "created_at": str(user["created_at"]),
        }
        await set_user(user_id, user_data)
        return user_data
    return None
