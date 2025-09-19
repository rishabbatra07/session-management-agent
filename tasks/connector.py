import asyncio
import os
import json
import re
import aiohttp
import logging
import aioredis
from anthropic import Anthropic

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


REDIS_URL = "redis://redis:6379"

ANTHROPIC_API_KEY =  os.getenv("ANTHROPIC_API_KEY")
client = Anthropic(api_key=ANTHROPIC_API_KEY)

API_KEY = os.getenv("OPENWEATHER_API_KEY")

async def fetch_weather(location: str) -> str:
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&units=metric&appid={API_KEY}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return f"Could not fetch weather for {location}."
            data = await resp.json()
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            humidity = data["main"]["humidity"]
            wind = data["wind"]["speed"]
            return (
                f"Weather in {location.title()}:\n"
                f"- Temperature: {temp}°C\n"
                f"- Condition: {desc}\n"
                f"- Humidity: {humidity}%\n"
                f"- Wind speed: {wind} m/s"
            )


async def process_message(session_id, message_text, redis):
    loop = asyncio.get_running_loop()

    # Redis keys
    history_key = f"session:{session_id}:history"
    counter_key = f"session:{session_id}:msg_counter"

    # Save user message in Redis
    msg_id = await redis.incr(counter_key)
    await redis.hset(history_key, msg_id, json.dumps({"role": "user", "content": message_text}))

    # Detect weather intent
    match = re.search(r"weather in ([a-zA-Z\s]+)", message_text, re.IGNORECASE)
    if match:
        location = match.group(1).strip()
        weather_info = await fetch_weather(location)
        prompt = f"Summarize this weather info for {location}:\n{weather_info}"
    else:
        prompt = message_text  # default: just echo/Claude response

    # Call Claude
    def call_claude():
        resp = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.content[0].text

    reply = await loop.run_in_executor(None, call_claude)

    msg_id = await redis.incr(counter_key)
    await redis.hset(history_key, msg_id, json.dumps({"role": "assistant", "content": reply}))

    await redis.publish(f"events:session:{session_id}:response", json.dumps({
           "session_id": session_id,
           "message": {"role": "assistant", "content": reply}
       }))

async def redis_listener():
    redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
    pubsub = redis.pubsub()
    await pubsub.psubscribe("messages:session:*")
    logger.info("[DEBUG] Worker subscribed to messages:session:*")

    async for message in pubsub.listen():
        if message["type"] == "pmessage":
            try:
                data = json.loads(message["data"])
                session_id = data.get("session_id")
                user_text = data["message"]["content"]
                asyncio.create_task(process_message(session_id, user_text, redis))
            except Exception as e:
                logger.error(f"[ERROR] Failed to handle message: {e}")


if __name__ == "__main__":
    asyncio.run(redis_listener())
