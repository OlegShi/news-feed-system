from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from middleware.authentication import get_current_user
from services.friend_service import add_friend, get_friends, find_user_by_username

router = APIRouter()


class AddFriendRequest(BaseModel):
    friend_username: str


@router.post("/friends")
async def add_friend_route(
    body: AddFriendRequest,
    user: dict = Depends(get_current_user),
):
    friend = await find_user_by_username(body.friend_username)
    if not friend:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        await add_friend(user["user_id"], friend["user_id"])
        return {"message": f"Added {body.friend_username} as friend"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/friends")
async def get_friends_route(
    user: dict = Depends(get_current_user),
):
    friends = await get_friends(user["user_id"])
    return {"friends": friends}
