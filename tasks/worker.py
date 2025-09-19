import asyncio
import json
import aioredis
from connector import process_message  # Your existing connector function
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

REDIS_URL = "redis://redis:6379"


async def handle_message_event(payload, redis):
    session_id = payload.get("session_id")
    message_text = payload.get("message", {}).get("content")
    if not message_text or not session_id:
        logger.warning(f"Invalid payload: {payload}")
        return

    logger.debug(f"Processing message for session {session_id}: {message_text}")

    try:
        events = await process_message(session_id, message_text, redis)
        if not events:
            logger.warning(f"No events returned from process_message for session {session_id}")
            return

        for e in events:
            channel = f"events:session:{session_id}:response"
            await redis.publish(channel, json.dumps(e))
            logger.debug(f"Published event to {channel}: {e}")

    except Exception as e:
        logger.error(f"Error in handle_message_event: {e}")


async def main():
    redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
    pubsub = redis.pubsub()

    await pubsub.psubscribe("messages:session:*")
    logger.info("Worker subscribed to messages:session:*")

    async for message in pubsub.listen():
        logger.debug(f"Received message: {message}")

        if message["type"] == "pmessage":
            try:
                payload = json.loads(message["data"])
                logger.debug(f"Dispatching payload to handler: {payload}")
                # Use create_task to avoid blocking listener
                asyncio.create_task(handle_message_event(payload, redis))
            except Exception as e:
                logger.error(f"Failed to handle message: {e}")

        await asyncio.sleep(0.01)


if __name__ == "__main__":
    logger.info("Starting worker...")
    asyncio.run(main())
