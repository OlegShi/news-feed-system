from database.graph_db import get_driver
from cache.user_cache import get_user, set_user
from database.mongodb import get_db
from message_queue.producer import send_fanout_message
from config import FANOUT_THRESHOLD


async def fanout_post(post_id: str, user_id: str, timestamp: float):
    """Push post to friends' news feed caches via Kafka.

    Uses push model for users with <= FANOUT_THRESHOLD friends.
    Users with more friends are skipped (pull model on read).
    """
    friend_ids = await get_friend_ids(user_id)
    if not friend_ids:
        return

    # Skip push for high-follower users (pull model)
    if len(friend_ids) > FANOUT_THRESHOLD:
        return

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
