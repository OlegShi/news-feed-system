from database.graph_db import get_driver
from cache.user_cache import get_user, set_user
from cache.redis_client import get_redis
from database.mongodb import get_db
from message_queue.producer import send_fanout_message
from config import FANOUT_THRESHOLD

PULL_USER_KEY = "pull_model_users"


async def fanout_post(post_id: str, user_id: str, timestamp: float):
    """Push post to friends' news feed caches via Kafka.

    Uses push model for users with <= FANOUT_THRESHOLD friends.
    Users with more friends are marked for pull model on read.
    """
    friend_ids = await get_friend_ids(user_id)
    if not friend_ids:
        return

    # High-follower user: mark for pull model, skip push
    if len(friend_ids) > FANOUT_THRESHOLD:
        r = get_redis()
        await r.sadd(PULL_USER_KEY, user_id)
        return

    # Ensure this user is NOT in the pull set (friend count may have dropped)
    r = get_redis()
    await r.srem(PULL_USER_KEY, user_id)

    # Warm user cache for friends
    db = get_db()
    for fid in friend_ids:
        cached = await get_user(fid)
        if not cached:
            user = await db.users.find_one({"user_id": fid}, {"_id": 0, "password_hash": 0})
            if user:
                await set_user(fid, {
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "created_at": str(user["created_at"]),
                })

    await send_fanout_message(post_id, user_id, friend_ids, timestamp)


async def is_pull_model_user(user_id: str) -> bool:
    """Check if a user is marked for pull model (high-follower)."""
    r = get_redis()
    return await r.sismember(PULL_USER_KEY, user_id)


async def get_friend_ids(user_id: str) -> list[str]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (u:User {user_id: $user_id})-[:FRIENDS_WITH]-(friend:User) "
            "RETURN friend.user_id AS friend_id",
            user_id=user_id,
        )
        records = await result.data()
        return [r["friend_id"] for r in records]
