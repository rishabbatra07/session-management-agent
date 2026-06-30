# Author: Rishab Batra (rishabbatra07@gmail.com)
# Computer Use Demo (FastAPI + Worker + Frontend)

## Features
- FastAPI backend providing session APIs (start session, send message)
- Real-time progress streaming via WebSocket & SSE endpoints
- Redis-based worker integration
- Simple static HTML/JS frontend (in `controller/static`) to demo API usage

## Running Locally
```bash
docker compose build --no-cache
docker compose up
```

Then open [http://localhost:8000](http://localhost:8000) in your browser to try the demo frontend.

## Frontend Usage
- Click **Create Session** → starts a new agent session and shows session id
- Enter session id and click **Connect WS** → connects WebSocket to stream agent events
- Type a message and click **Send** → sends user message to backend and worker echoes

## Notes
- VNC support is a placeholder and not implemented here.
- Replace the simple agent loop with the actual Anthropic computer-use agent for production use.


# Flow Architecture

1) User creates session calls to FastAPI from where Redis/pubsub is been subscribed by Worker which do all handling with Claude AI

2) Worker sends reply to Redis and to FastAPI and from there WebSocket is listening to send response to Frontend

3) User clicks Connect VNC → noVNC frontend → VNC server → remote desktop


# Have added video demonstration here:
https://www.loom.com/share/d42131479ed44e9090e8673898ad2852?sid=4d6d3f14-ded6-4e79-8a35-a16aefdfeaec


# Search using console
curl -X POST http://localhost:8000/v1/sessions/aad4ccc2-7942-4f9d-9e4d-bb00753b4410/messages \
-H "Content-Type: application/json" \
-d '{"content":"Search the weather in Dubai"}'
{"ok":true}%


(base) rishab.batra@Rishabs-MacBook-Pro ~ % docker exec -it computer_use_demo-redis-1 redis-cli

# Subscriber
127.0.0.1:6379> PSUBSCRIBE events:session:*
1) "psubscribe"
2) "events:session:*"
3) (integer) 1
1) "pmessage"
2) "events:session:*"
3) "events:session:10e3f865-2573-492a-a993-afb842fb2da5:response"
4) "{\"session_id\": \"10e3f865-2573-492a-a993-afb842fb2da5\", \"message\": {\"role\": \"assistant\", \"content\": \"**Malaysia Weather Summary:**\\n\\nCurrently overcast with cloudy skies and a comfortable temperature of 21\\u00b0C (70\\u00b0F). The air is very humid at 97%, with light winds at 1 m/s. Expect a calm but muggy day with limited sunshine due to the cloud cover.\"}}"
   Error: Server closed the connection

# Publisher 
127.0.0.1:6379> PUBLISH messages:session:test '{"session_id":"test","message":{"content":"weather in dubai"}}'
(integer) 2
127.0.0.1:6379> PUBLISH messages:session:test '{"session_id":"test","message":{"content":"weather in india"}}'
(integer) 2


