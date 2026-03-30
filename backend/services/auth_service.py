import jwt
import bcrypt
import uuid
from datetime import datetime, timedelta, timezone
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS
from database.mongodb import get_db
from database.graph_db import get_driver
from cache.user_cache import set_user


async def register_user(username: str, password: str) -> dict:
    db = get_db()
    existing = await db.users.find_one({"username": username})
    if existing:
        raise ValueError("Username already taken")

    user_id = str(uuid.uuid4())
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    now = datetime.now(timezone.utc)

    user_doc = {
        "user_id": user_id,
        "username": username,
        "password_hash": password_hash,
        "created_at": now,
    }
    await db.users.insert_one(user_doc)

    # Create user node in graph DB
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            "CREATE (u:User {user_id: $user_id, username: $username})",
            user_id=user_id,
            username=username,
        )

    # Cache user data
    await set_user(user_id, {
        "user_id": user_id,
        "username": username,
        "created_at": str(now),
    })

    return {"user_id": user_id, "username": username, "created_at": now}


async def login_user(username: str, password: str) -> str:
    db = get_db()
    user = await db.users.find_one({"username": username})
    if not user:
        raise ValueError("Invalid credentials")

    if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        raise ValueError("Invalid credentials")

    return create_token(user["user_id"], user["username"])


def create_token(user_id: str, username: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
