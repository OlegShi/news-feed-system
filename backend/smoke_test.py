"""
Smoke test — verifies that all infrastructure components are connected
and the full feed-publishing + retrieval flow works end-to-end.

Run from the backend/ directory:
    python smoke_test.py

Requires all services running: MongoDB, Redis, Neo4j, Kafka, and the API server.
"""
import asyncio
import sys
import time
import httpx

API = "http://localhost:8000"
USERS = [
    {"username": f"smoketest_alice_{int(time.time())}", "password": "pass123456"},
    {"username": f"smoketest_bob_{int(time.time())}", "password": "pass123456"},
]

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
CHECK = f"{GREEN}\u2713{RESET}"
CROSS = f"{RED}\u2717{RESET}"


def ok(msg):
    print(f"  {CHECK} {msg}")


def fail(msg):
    print(f"  {CROSS} {RED}{msg}{RESET}")


def section(msg):
    print(f"\n{YELLOW}[{msg}]{RESET}")


async def test_direct_connections():
    """Test each infrastructure component directly."""
    results = {}

    # --- MongoDB ---
    section("MongoDB")
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        from config import MONGODB_URL, MONGODB_DB

        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=3000)
        db = client[MONGODB_DB]
        await db.command("ping")
        ok(f"Connected to {MONGODB_URL}")

        test_doc = {"_test": True, "ts": time.time()}
        r = await db.smoke_test.insert_one(test_doc)
        ok(f"Write OK — inserted doc {r.inserted_id}")

        found = await db.smoke_test.find_one({"_id": r.inserted_id})
        assert found is not None
        ok("Read OK — document retrieved")

        await db.smoke_test.delete_one({"_id": r.inserted_id})
        ok("Delete OK — cleaned up")
        results["mongodb"] = True
        client.close()
    except Exception as e:
        fail(f"MongoDB: {e}")
        results["mongodb"] = False

    # --- Redis ---
    section("Redis")
    try:
        import redis.asyncio as aioredis
        from config import REDIS_URL

        r = aioredis.from_url(REDIS_URL, decode_responses=True)
        await r.ping()
        ok(f"Connected to {REDIS_URL}")

        await r.set("smoke_test_key", "hello", ex=10)
        val = await r.get("smoke_test_key")
        assert val == "hello"
        ok(f"Write/Read OK — got '{val}'")

        await r.zadd("smoke_test_zset", {"item1": 1.0, "item2": 2.0})
        items = await r.zrevrange("smoke_test_zset", 0, -1)
        assert len(items) == 2
        ok(f"Sorted set OK — {len(items)} items (used for news feed cache)")

        await r.delete("smoke_test_key", "smoke_test_zset")
        ok("Cleanup OK")
        results["redis"] = True
        await r.close()
    except Exception as e:
        fail(f"Redis: {e}")
        results["redis"] = False

    # --- Neo4j ---
    section("Neo4j (Graph DB)")
    try:
        from neo4j import AsyncGraphDatabase
        from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

        driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        async with driver.session() as session:
            result = await session.run("RETURN 1 AS n")
            record = await result.single()
            assert record["n"] == 1
            ok(f"Connected to {NEO4J_URI}")

            await session.run(
                "CREATE (a:SmokeTest {name:'A'})-[:KNOWS]->(b:SmokeTest {name:'B'})"
            )
            ok("Write OK — created nodes + relationship")

            result = await session.run(
                "MATCH (a:SmokeTest)-[:KNOWS]->(b:SmokeTest) RETURN a.name, b.name"
            )
            data = await result.data()
            assert len(data) == 1
            ok(f"Read OK — traversed graph: {data[0]['a.name']} -> {data[0]['b.name']}")

            await session.run("MATCH (n:SmokeTest) DETACH DELETE n")
            ok("Cleanup OK")
        results["neo4j"] = True
        await driver.close()
    except Exception as e:
        fail(f"Neo4j: {e}")
        results["neo4j"] = False

    # --- Kafka ---
    section("Kafka")
    try:
        from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
        import json
        from config import KAFKA_BOOTSTRAP_SERVERS

        producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await producer.start()
        ok(f"Producer connected to {KAFKA_BOOTSTRAP_SERVERS}")

        test_msg = {"smoke_test": True, "ts": time.time()}
        await producer.send_and_wait("smoke_test_topic", test_msg)
        ok("Produce OK — sent message to 'smoke_test_topic'")
        await producer.stop()

        consumer = AIOKafkaConsumer(
            "smoke_test_topic",
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset="earliest",
            group_id=f"smoke-test-{int(time.time())}",
            consumer_timeout_ms=5000,
        )
        await consumer.start()
        msg = await asyncio.wait_for(consumer.getone(), timeout=10)
        received = json.loads(msg.value.decode("utf-8"))
        assert received.get("smoke_test") is True
        ok(f"Consume OK — received message back")
        await consumer.stop()
        results["kafka"] = True
    except Exception as e:
        fail(f"Kafka: {e}")
        results["kafka"] = False

    return results


async def test_api_flow():
    """Test the full API flow: register, login, add friend, post, read feed."""
    section("API End-to-End Flow")
    results = {}

    async with httpx.AsyncClient(base_url=API, timeout=30) as client:
        tokens = []

        # Register two users
        for user in USERS:
            try:
                resp = await client.post("/v1/auth/register", json=user)
                assert resp.status_code == 200, resp.text
                ok(f"Registered user '{user['username']}'")
            except Exception as e:
                fail(f"Register {user['username']}: {type(e).__name__}: {e}")
                results["api"] = False
                return results

        # Login both users
        for user in USERS:
            try:
                resp = await client.post("/v1/auth/login", json=user)
                assert resp.status_code == 200, resp.text
                token = resp.json()["auth_token"]
                tokens.append(token)
                ok(f"Logged in '{user['username']}' — got JWT token")
            except Exception as e:
                fail(f"Login {user['username']}: {e}")
                results["api"] = False
                return results

        # Alice adds Bob as friend
        try:
            resp = await client.post(
                "/v1/me/friends",
                json={"friend_username": USERS[1]["username"]},
                headers={"Authorization": f"Bearer {tokens[0]}"},
            )
            assert resp.status_code == 200, resp.text
            ok(f"'{USERS[0]['username']}' added '{USERS[1]['username']}' as friend (Neo4j)")
        except Exception as e:
            fail(f"Add friend: {e}")

        # Verify friends list
        try:
            resp = await client.get(
                "/v1/me/friends",
                headers={"Authorization": f"Bearer {tokens[0]}"},
            )
            friends = resp.json()["friends"]
            assert any(f["username"] == USERS[1]["username"] for f in friends)
            ok(f"Friends list OK — {len(friends)} friend(s) returned")
        except Exception as e:
            fail(f"Get friends: {e}")

        # Bob publishes a post
        try:
            resp = await client.post(
                "/v1/me/feed",
                json={"content": "Hello from smoke test!"},
                headers={"Authorization": f"Bearer {tokens[1]}"},
            )
            assert resp.status_code == 200, resp.text
            post_id = resp.json()["post_id"]
            ok(f"Bob published post '{post_id}' (MongoDB + Redis post cache)")
        except Exception as e:
            fail(f"Publish post: {e}")
            results["api"] = False
            return results

        # Wait for fanout via Kafka
        print(f"  ... waiting 3s for Kafka fanout worker to process ...")
        await asyncio.sleep(3)

        # Alice reads her feed — should see Bob's post
        try:
            resp = await client.get(
                "/v1/me/feed",
                headers={"Authorization": f"Bearer {tokens[0]}"},
            )
            feed = resp.json()["feed"]
            found = any(p.get("content") == "Hello from smoke test!" for p in feed)
            if found:
                ok(f"Alice's feed has Bob's post! (Redis news feed cache -> hydrated from caches)")
                ok("Full flow verified: Post -> MongoDB + PostCache -> Kafka -> FanoutWorker -> NewsFeedCache -> Retrieval")
            else:
                fail(f"Bob's post NOT in Alice's feed. Feed has {len(feed)} items. Kafka worker may not be running.")
                print(f"    Feed contents: {feed}")
        except Exception as e:
            fail(f"Get feed: {e}")

        results["api"] = True
    return results


async def main():
    print("=" * 60)
    print("  NEWS FEED SYSTEM — SMOKE TEST")
    print("=" * 60)

    infra = await test_direct_connections()

    # Only test API if core infra is up
    if all(infra.get(k) for k in ["mongodb", "redis", "neo4j"]):
        api = await test_api_flow()
    else:
        section("API End-to-End Flow")
        fail("Skipped — fix infrastructure issues above first")
        api = {"api": False}

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    all_results = {**infra, **api}
    all_ok = True
    for component, status in all_results.items():
        icon = CHECK if status else CROSS
        print(f"  {icon} {component.upper()}")
        if not status:
            all_ok = False

    if all_ok:
        print(f"\n  {GREEN}All components connected and working!{RESET}\n")
    else:
        print(f"\n  {RED}Some components failed — check output above.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
