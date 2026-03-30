from neo4j import AsyncGraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

driver = None


async def connect_neo4j():
    global driver
    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    async with driver.session() as session:
        await session.run(
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS "
            "FOR (u:User) REQUIRE u.user_id IS UNIQUE"
        )


async def close_neo4j():
    global driver
    if driver:
        await driver.close()


def get_driver():
    return driver
