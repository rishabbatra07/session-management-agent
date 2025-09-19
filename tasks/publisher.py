import aioredis, json
from pathlib import Path
REDIS_URL = "redis://localhost:6379"

async def publish_session_event(session_id: str, event: dict):
    redis = aioredis.from_url(REDIS_URL)
    ch = f"events:session:{session_id}"
    await redis.publish(ch, json.dumps(event))
    await redis.close()
