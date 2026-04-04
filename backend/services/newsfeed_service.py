from cache.newsfeed_cache import get_feed_post_ids
from services.post_service import get_post_by_id
from services.fanout_service import get_friend_ids, is_pull_model_user
from cache.user_cache import get_user, set_user
from cache.post_cache import set_post
from database.mongodb import get_db


async def get_newsfeed(user_id: str, offset: int = 0, limit: int = 20) -> list[dict]:
    """Build a fully hydrated news feed.

    Merges:
    - Pushed posts from the news feed cache (fanout-on-write)
    - Pulled posts from high-follower friends queried on-demand (fanout-on-read)
    """
    # 1. Get pushed posts from cache
    post_ids = await get_feed_post_ids(user_id, offset=0, limit=offset + limit)
    pushed_posts = []
    for post_id in post_ids:
        post = await get_post_by_id(post_id)
        if post:
            pushed_posts.append(post)

    # 2. Pull posts from high-follower friends (on-demand)
    pulled_posts = await _pull_from_high_follower_friends(user_id, limit)

    # 3. Merge, deduplicate, sort reverse-chronological
    seen = set()
    all_posts = []
    for post in pushed_posts + pulled_posts:
        if post["post_id"] not in seen:
            seen.add(post["post_id"])
            all_posts.append(post)

    all_posts.sort(key=lambda p: p["created_at"], reverse=True)

    # 4. Apply pagination
    page = all_posts[offset : offset + limit]

    # 5. Hydrate with author info
    feed = []
    for post in page:
        author = await _get_user_info(post["user_id"])
        feed.append({
            "post_id": post["post_id"],
            "user_id": post["user_id"],
            "username": author.get("username", "Unknown") if author else "Unknown",
            "content": post["content"],
            "created_at": post["created_at"],
        })

    return feed


async def _pull_from_high_follower_friends(user_id: str, limit: int) -> list[dict]:
    """Fetch recent posts from friends who use the pull model (high-follower users)."""
    friend_ids = await get_friend_ids(user_id)
    if not friend_ids:
        return []

    # Filter to only high-follower friends
    pull_friend_ids = []
    for fid in friend_ids:
        if await is_pull_model_user(fid):
            pull_friend_ids.append(fid)

    if not pull_friend_ids:
        return []

    # Query their recent posts directly from MongoDB
    db = get_db()
    cursor = db.posts.find(
        {"user_id": {"$in": pull_friend_ids}},
        {"_id": 0},
    ).sort("created_at", -1).limit(limit)

    posts = []
    async for doc in cursor:
        post_data = {
            "post_id": doc["post_id"],
            "user_id": doc["user_id"],
            "content": doc["content"],
            "created_at": str(doc["created_at"]),
        }
        # Warm the post cache for subsequent requests
        await set_post(doc["post_id"], post_data)
        posts.append(post_data)

    return posts


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
