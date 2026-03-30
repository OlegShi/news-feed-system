from fastapi import Query, Header, HTTPException
from services.auth_service import verify_token
from typing import Optional


async def get_current_user(
    auth_token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
) -> dict:
    """Extract and validate auth token from query param or Authorization header."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif auth_token:
        token = auth_token

    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        payload = verify_token(token)
        return {"user_id": payload["user_id"], "username": payload["username"]}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
