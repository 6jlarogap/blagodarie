#!./ENV/bin/python3

# Websockets server

import asyncio
import json

from redis import asyncio as aioredis
from websockets.asyncio.server import broadcast, serve
from websockets.frames import CloseCode

from settings import *

CONNECTIONS = {}

async def handler(websocket):
    try:
        data = await websocket.recv()
        print(data)
        CONNECTIONS[websocket] = {"user_id": None}
    except:
        pass
    try:
        await websocket.wait_closed()
    finally:
        if websocket in CONNECTIONS:
            del CONNECTIONS[websocket]

async def process_events():
    """Listen to events in Redis and process them."""
    redis = aioredis.from_url("redis://127.0.0.1:6379/1")
    pubsub = redis.pubsub()
    await pubsub.subscribe("events")
    async for message in pubsub.listen():
        print(message)
        if message.get("type") != "message":
            continue
        payload = message["data"]
        # Broadcast event to all users who have permissions to see it.
        event = payload
        recipients = [
            websocket for websocket in CONNECTIONS.keys()
        ]
        broadcast(recipients, payload)


async def main():
    async with serve(handler, "localhost", SERVER_PORT):
        await process_events()

if __name__ == "__main__":
    asyncio.run(main())
