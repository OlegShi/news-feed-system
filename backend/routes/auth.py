from fastapi import APIRouter, HTTPException
from models.user import UserRegister, UserLogin
from services.auth_service import register_user, login_user

router = APIRouter()


@router.post("/register")
async def register(user: UserRegister):
    try:
        result = await register_user(user.username, user.password)
        return {
            "user_id": result["user_id"],
            "username": result["username"],
            "message": "User registered successfully",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(user: UserLogin):
    try:
        token = await login_user(user.username, user.password)
        return {"auth_token": token}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
