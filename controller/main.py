from fastapi import FastAPI, WebSocket, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import aioredis, json, uuid, os
import os
import os
from fastapi.staticfiles import StaticFiles

app = FastAPI()
REDIS_URL = "redis://redis:6379"

novnc_dir = os.path.join(os.path.dirname(__file__), "noVNC")
app.mount("/vnc", StaticFiles(directory=novnc_dir), name="vnc")# Enable CORS for frontend access

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict to ["http://localhost:8000"] if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

sessions = {}


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the minimal UI at root"""
    index_path = os.path.join(static_dir, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.post("/v1/sessions")
async def create_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = {"id": session_id, "messages": []}
    return {"id": session_id}


@app.get("/v1/sessions")
async def list_sessions():
    return list(sessions.values())


@app.post("/v1/sessions/{session_id}/messages")
async def post_message(session_id: str, payload: dict):
    if session_id not in sessions:
        return {"error": "session not found"}

    message = {"role": "user", "type": "text", "content": payload.get("content")}
    sessions[session_id]["messages"].append(message)

    redis = aioredis.from_url(REDIS_URL)
    await redis.publish(f"messages:session:{session_id}", json.dumps({"session_id": session_id, "message": message}))
    await redis.close()
    return {"ok": True}


@app.websocket("/v1/realtime/ws/{session_id}")
async def realtime_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
    pubsub = redis.pubsub()

    # FIX: subscribe to the same channel your worker publishes to
    channel = f"events:session:{session_id}:response"
    await pubsub.subscribe(channel)

    try:
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg:
                try:
                    event = json.loads(msg["data"])
                except Exception:
                    event = {"raw": msg["data"]}
                await websocket.send_json(event)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await pubsub.close()
        await redis.close()


@app.get("/v1/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Returns chat history for a session from Redis"""
    redis = aioredis.from_url(REDIS_URL)
    history_key = f"session:{session_id}:history"
    data = await redis.hgetall(history_key)
    await redis.close()

    if not data:
        raise HTTPException(status_code=404, detail="No history found for this session")

    messages = []
    for msg_id, raw in sorted(data.items(), key=lambda x: int(x[0])):
        messages.append(json.loads(raw))

    return {"session_id": session_id, "history": messages}