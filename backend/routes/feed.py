from fastapi import APIRouter, Depends, Query, Request, HTTPException
from datetime import datetime, timezone
from middleware.authentication import get_current_user
from middleware.rate_limiter import check_rate_limit
from services.post_service import create_post
from services.fanout_service import fanout_post
from services.newsfeed_service import get_newsfeed
from cache.newsfeed_cache import add_post_to_feed

router = APIRouter()


@router.post("/feed")
async def publish_post(
    request: Request,
    content: str | None = Query(None),
    user: dict = Depends(get_current_user),
):
    """Publish a post. Content via query param or JSON body."""
    post_content = content
    if not post_content:
        try:
            body = await request.json()
            post_content = body.get("content")
        except Exception:
            pass

    if not post_content or not post_content.strip():
        raise HTTPException(status_code=400, detail="Content is required")

    post_content = post_content.strip()
    if len(post_content) > 10000:
        raise HTTPException(status_code=400, detail="Content too long (max 10000 characters)")

    await check_rate_limit(user["user_id"])

    post = await create_post(user["user_id"], post_content)
    timestamp = datetime.now(timezone.utc).timestamp()

    # Add to the author's own feed
    await add_post_to_feed(user["user_id"], post["post_id"], timestamp)

    # Fanout to friends via Kafka
    try:
        await fanout_post(post["post_id"], user["user_id"], timestamp)
    except Exception:
        pass  # Post is persisted; fanout can be retried

    return {"post_id": post["post_id"], "message": "Post published successfully"}


@router.get("/feed")
async def get_feed(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    """Retrieve the authenticated user's news feed."""
    feed = await get_newsfeed(user["user_id"], offset, limit)
    return {"feed": feed}
