import os

# MongoDB
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "newsfeed")

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Kafka
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_FANOUT_TOPIC = "fanout"

# Neo4j
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "newsfeed123")

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Rate limiting
RATE_LIMIT_POSTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_POSTS_PER_MINUTE", "10"))

# Limits
MAX_FRIENDS = 5000
NEWSFEED_CACHE_LIMIT = 500
FANOUT_THRESHOLD = 1000  # Users with more friends use pull model
