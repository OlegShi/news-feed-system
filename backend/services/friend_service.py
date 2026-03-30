from database.graph_db import get_driver
from database.mongodb import get_db
from config import MAX_FRIENDS


async def add_friend(user_id: str, friend_id: str):
    if user_id == friend_id:
        raise ValueError("Cannot add yourself as a friend")

    db = get_db()
    friend = await db.users.find_one({"user_id": friend_id})
    if not friend:
        raise ValueError("User not found")

    driver = get_driver()
    async with driver.session() as session:
        # Check current friend count
        result = await session.run(
            "MATCH (u:User {user_id: $user_id})-[:FRIENDS_WITH]-() "
            "RETURN count(*) AS cnt",
            user_id=user_id,
        )
        record = await result.single()
        if record and record["cnt"] >= MAX_FRIENDS:
            raise ValueError(f"Maximum friend limit ({MAX_FRIENDS}) reached")

        # Check if already friends
        result = await session.run(
            "MATCH (a:User {user_id: $user_id})-[:FRIENDS_WITH]-(b:User {user_id: $friend_id}) "
            "RETURN count(*) AS cnt",
            user_id=user_id,
            friend_id=friend_id,
        )
        record = await result.single()
        if record and record["cnt"] > 0:
            raise ValueError("Already friends")

        # Create friendship
        await session.run(
            "MATCH (a:User {user_id: $user_id}), (b:User {user_id: $friend_id}) "
            "CREATE (a)-[:FRIENDS_WITH]->(b)",
            user_id=user_id,
            friend_id=friend_id,
        )


async def get_friends(user_id: str) -> list[dict]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (u:User {user_id: $user_id})-[:FRIENDS_WITH]-(friend:User) "
            "RETURN friend.user_id AS user_id, friend.username AS username",
            user_id=user_id,
        )
        records = await result.data()
        return [{"user_id": r["user_id"], "username": r["username"]} for r in records]


async def find_user_by_username(username: str) -> dict | None:
    db = get_db()
    user = await db.users.find_one({"username": username}, {"_id": 0, "password_hash": 0})
    if user:
        return {"user_id": user["user_id"], "username": user["username"]}
    return None
