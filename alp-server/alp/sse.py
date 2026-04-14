"""
alp.sse
-------
SSE (Server-Sent Events) transport layer for MCP.
Manages per-session queues and the event stream generator.
"""

import asyncio
import json
import uuid
from typing import AsyncGenerator


# session_id -> asyncio.Queue
_clients: dict[str, asyncio.Queue] = {}


def create_session() -> tuple[str, asyncio.Queue]:
    """Create a new SSE session. Returns (session_id, queue)."""
    session_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()
    _clients[session_id] = queue
    return session_id, queue


def remove_session(session_id: str) -> None:
    """Remove a session from the client registry."""
    _clients.pop(session_id, None)


def get_queue(session_id: str) -> asyncio.Queue | None:
    """Return the queue for a session, or None if not found."""
    return _clients.get(session_id)


async def push(session_id: str, message: dict) -> bool:
    """Push a message to a session's SSE queue. Returns False if session not found."""
    queue = get_queue(session_id)
    if queue is None:
        return False
    await queue.put(message)
    return True


async def event_stream(
    session_id: str,
    queue: asyncio.Queue,
    post_url: str,
    ping_interval: float = 15.0,
) -> AsyncGenerator[str, None]:
    """
    Async generator that yields SSE-formatted strings.
    Sends the endpoint event first, then relays queued messages with heartbeat pings.
    """
    try:
        # MCP endpoint discovery event
        yield f"event: endpoint\ndata: {post_url}\n\n"

        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=ping_interval)
                yield f"event: message\ndata: {json.dumps(message)}\n\n"
            except asyncio.TimeoutError:
                yield ": ping\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        remove_session(session_id)