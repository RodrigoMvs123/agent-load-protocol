"""
ALP Reference Server
Agent Load Protocol v0.6.0

Serves an agent.alp.json and its tools over HTTP.

Endpoints
---------
GET  /health                    → status check
GET  /agent                     → Agent Card JSON
GET  /agent/refresh             → re-fetch card from AGENT_CARD_URL (v0.6.0)
GET  /persona                   → persona for system prompt injection (v0.4.0)
GET  /agents                    → all hosted Agent Cards (v0.4.0 + v0.6.0)
GET  /tools                     → tool list (Claude Code / Claude Desktop)
POST /tools/{name}              → execute a tool (local or proxy)
GET  /mcp                       → MCP SSE stream (Kiro)
POST /mcp                       → MCP JSON-RPC messages (Kiro)
GET  /mcp/{agent_id}            → MCP SSE stream for a specific agent (v0.6.0)
POST /mcp/{agent_id}            → MCP JSON-RPC messages for a specific agent (v0.6.0)
GET  /.well-known/mcp-server-card → SEP-2127 compatible

v0.5.0 — Proxy Tool Execution
------------------------------
When a tool's endpoint in agent.alp.json is a full URL
(e.g. https://their-server.com/api/search), the ALP server
forwards the call via HTTP instead of executing locally.

Tool authors: zero code changes needed in their agent.

v0.6.0 — Remote Card Loading
------------------------------
AGENT_CARD_URL env var loads the Agent Card from any public URL at startup.
Falls back to AGENT_CARD_PATH if AGENT_CARD_URL is not set.

AGENTS_MANIFEST env var loads multiple remote cards from a JSON file.
Each agent gets its own /mcp/{agent-id} endpoint automatically.

macOS / Linux:
  AGENT_CARD_URL=https://raw.githubusercontent.com/org/repo/main/agent.alp.json python alp_server.py

Windows PowerShell:
  $env:AGENT_CARD_URL = "https://raw.githubusercontent.com/org/repo/main/agent.alp.json"; python alp_server.py

Kiro MCP config (.kiro/settings/mcp.json)
-----------------------------------------
Single agent:
{
  "mcpServers": {
    "my-agent": {
      "url": "http://localhost:8000/mcp"
    }
  }
}

Multi-agent (v0.6.0):
{
  "mcpServers": {
    "agent-a": { "url": "http://localhost:8000/mcp/agent-a" },
    "agent-b": { "url": "http://localhost:8000/mcp/agent-b" }
  }
}
"""

import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

app = FastAPI(title="ALP Server", version="0.6.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

AGENT_CARD_PATH = os.environ.get("AGENT_CARD_PATH", "agent.alp.json")
AGENT_CARD_URL  = os.environ.get("AGENT_CARD_URL", "")
AGENTS_MANIFEST = os.environ.get("AGENTS_MANIFEST", "")
PORT = int(os.environ.get("PORT", 8000))

# SSE client queues: session_id -> asyncio.Queue
_sse_clients: dict[str, asyncio.Queue] = {}

# v0.6.0 — in-memory card cache
# Primary card: _card_cache["__primary__"]
# Multi-agent:  _card_cache[agent_id]
_card_cache: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# v0.6.0 — Card loader (local + remote)
# ---------------------------------------------------------------------------

def load_card() -> dict:
    """Load card from local file (AGENT_CARD_PATH)."""
    path = Path(AGENT_CARD_PATH)
    if not path.exists():
        raise FileNotFoundError(f"Agent card not found: {AGENT_CARD_PATH}")
    with open(path) as f:
        return json.load(f)


async def load_card_remote(url: str) -> dict:
    """v0.6.0 — Fetch an Agent Card from any public URL."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Failed to fetch card from '{url}': HTTP {exc.response.status_code}"
        )
    except httpx.RequestError as exc:
        raise RuntimeError(
            f"Connection error fetching card from '{url}': {str(exc)}"
        )


async def get_primary_card() -> dict:
    """
    v0.6.0 — Return the primary Agent Card.
    Priority: AGENT_CARD_URL (remote) > AGENT_CARD_PATH (local file)
    Uses in-memory cache; refreshed by GET /agent/refresh.
    """
    if "__primary__" in _card_cache:
        return _card_cache["__primary__"]

    if AGENT_CARD_URL:
        card = await load_card_remote(AGENT_CARD_URL)
    else:
        card = load_card()

    _card_cache["__primary__"] = card
    return card


async def get_card_by_id(agent_id: str) -> dict:
    """v0.6.0 — Return a specific agent card by its id (multi-agent mode)."""
    if agent_id in _card_cache:
        return _card_cache[agent_id]
    raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")


async def load_agents_manifest() -> None:
    """
    v0.6.0 — Load multiple remote Agent Cards from AGENTS_MANIFEST file.
    Each card is cached by its 'id' field and served at /mcp/{agent-id}.
    """
    if not AGENTS_MANIFEST:
        return

    manifest_path = Path(AGENTS_MANIFEST)
    if not manifest_path.exists():
        print(f"⚠️  AGENTS_MANIFEST file not found: {AGENTS_MANIFEST}")
        return

    with open(manifest_path) as f:
        manifest = json.load(f)

    urls = manifest.get("agents", [])
    print(f"📋 Loading {len(urls)} agents from manifest...")

    for url in urls:
        try:
            card = await load_card_remote(url)
            agent_id = card.get("id")
            if agent_id:
                _card_cache[agent_id] = card
                print(f"   ✅ Loaded: {card.get('name', agent_id)} ({agent_id})")
            else:
                print(f"   ⚠️  Card at {url} has no 'id' field — skipped")
        except Exception as exc:
            print(f"   ❌ Failed to load {url}: {exc}")


# ---------------------------------------------------------------------------
# Startup — load cards
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    """Load all cards on server startup."""
    # Load primary card
    try:
        card = await get_primary_card()
        source = AGENT_CARD_URL if AGENT_CARD_URL else AGENT_CARD_PATH
        print(f"✅ Primary card loaded: {card.get('name')} (ALP {card.get('alp_version')}) from {source}")
    except Exception as exc:
        print(f"⚠️  Could not load primary card: {exc}")

    # Load manifest agents (multi-agent mode)
    await load_agents_manifest()


# ---------------------------------------------------------------------------
# v0.5.0 — Proxy tool executor
# ---------------------------------------------------------------------------

async def execute_tool(tool_name: str, input_data: dict, card: dict = None) -> dict:
    """
    Execute a tool defined in the Agent Card.

    - If the tool endpoint is a full URL (http/https) → proxy the call
    - If the tool endpoint is a relative path (/tools/...) → execute locally
    """
    if card is None:
        card = await get_primary_card()

    tools = {t["name"]: t for t in card.get("tools", [])}

    if tool_name not in tools:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    tool = tools[tool_name]
    endpoint = tool.get("endpoint", "")

    # --- Proxy execution (v0.5.0) ---
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json={"input": input_data},
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Proxy error from '{endpoint}': {exc.response.status_code}",
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Proxy connection error to '{endpoint}': {str(exc)}",
            )

    # --- Local execution (stub — replace with your implementations) ---
    # if tool_name == "greet":
    #     name = input_data.get("name", "stranger")
    #     return {"result": f"Hello, {name}!", "error": None}

    return {
        "result": f"Tool '{tool_name}' executed with input: {input_data}",
        "error": None,
    }


# ---------------------------------------------------------------------------
# MCP JSON-RPC helpers
# ---------------------------------------------------------------------------

def _mcp_tools_list(card: dict) -> list[dict]:
    return [
        {
            "name": t["name"],
            "description": t.get("description", ""),
            "inputSchema": t.get("input_schema", {"type": "object", "properties": {}}),
        }
        for t in card.get("tools", [])
    ]


async def _handle_mcp_message(msg: dict, card: dict) -> dict | None:
    method = msg.get("method", "")
    msg_id = msg.get("id")
    params = msg.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": card.get("name", "ALP Agent"),
                    "version": card.get("alp_version", "0.6.0"),
                },
            },
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": _mcp_tools_list(card)},
        }

    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_input = params.get("arguments", params.get("input", {}))
        try:
            result = await execute_tool(tool_name, tool_input, card)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result)}],
                    "isError": False,
                },
            }
        except HTTPException as exc:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": exc.detail}],
                    "isError": True,
                },
            }

    if method.startswith("notifications/"):
        return None

    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


# ---------------------------------------------------------------------------
# MCP SSE helpers (shared)
# ---------------------------------------------------------------------------

def _make_sse_stream(session_id: str, card_getter, base_url: str):
    """Returns an async SSE event stream generator for a given card."""
    queue: asyncio.Queue = asyncio.Queue()
    _sse_clients[session_id] = queue

    async def event_stream():
        try:
            endpoint_url = f"{base_url}?session_id={session_id}"
            yield f"event: endpoint\ndata: {endpoint_url}\n\n"
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"event: message\ndata: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            _sse_clients.pop(session_id, None)

    return event_stream()


async def _handle_mcp_post(request: Request, card: dict) -> JSONResponse:
    """Shared handler for MCP JSON-RPC POST messages."""
    session_id = request.query_params.get("session_id")
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON"}, status_code=400)

    messages = body if isinstance(body, list) else [body]
    last_response = None

    for msg in messages:
        response = await _handle_mcp_message(msg, card)
        if response is None:
            continue
        if session_id and session_id in _sse_clients:
            await _sse_clients[session_id].put(response)
        else:
            last_response = response

    if last_response:
        return JSONResponse(last_response)
    return JSONResponse({"ok": True})


# ---------------------------------------------------------------------------
# MCP SSE — primary agent (v0.5.0)
# ---------------------------------------------------------------------------

@app.get("/mcp")
async def mcp_sse(request: Request):
    """MCP SSE transport — primary agent. Kiro connects here."""
    session_id = str(uuid.uuid4())
    base_url = f"http://localhost:{PORT}/mcp"
    card = await get_primary_card()
    stream = _make_sse_stream(session_id, card, base_url)
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/mcp")
async def mcp_post(request: Request):
    """MCP JSON-RPC message receiver — primary agent."""
    card = await get_primary_card()
    return await _handle_mcp_post(request, card)


# ---------------------------------------------------------------------------
# v0.6.0 — MCP SSE per agent (multi-agent)
# ---------------------------------------------------------------------------

@app.get("/mcp/{agent_id}")
async def mcp_sse_agent(agent_id: str, request: Request):
    """v0.6.0 — MCP SSE transport for a specific agent by id."""
    card = await get_card_by_id(agent_id)
    session_id = str(uuid.uuid4())
    base_url = f"http://localhost:{PORT}/mcp/{agent_id}"
    stream = _make_sse_stream(session_id, card, base_url)
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/mcp/{agent_id}")
async def mcp_post_agent(agent_id: str, request: Request):
    """v0.6.0 — MCP JSON-RPC message receiver for a specific agent by id."""
    card = await get_card_by_id(agent_id)
    return await _handle_mcp_post(request, card)


# ---------------------------------------------------------------------------
# Standard REST endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "alp_version": "0.6.0"}


@app.get("/agent")
async def get_agent():
    """Return the primary Agent Card."""
    try:
        return await get_primary_card()
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/agent/refresh")
async def refresh_agent_card():
    """
    v0.6.0 — Re-fetch the primary Agent Card from AGENT_CARD_URL.
    Useful when the card is updated without restarting the server.
    """
    if not AGENT_CARD_URL:
        raise HTTPException(
            status_code=400,
            detail="AGENT_CARD_URL is not set — nothing to refresh"
        )
    try:
        card = await load_card_remote(AGENT_CARD_URL)
        _card_cache["__primary__"] = card
        return {
            "refreshed": True,
            "id": card.get("id"),
            "name": card.get("name"),
            "alp_version": card.get("alp_version"),
            "source": AGENT_CARD_URL,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/persona")
async def get_persona():
    """v0.4.0 — Return the agent persona for system prompt injection."""
    card = await get_primary_card()
    persona = card.get("persona")
    if not persona:
        raise HTTPException(status_code=404, detail="No persona defined in Agent Card")
    return {"persona": persona, "id": card.get("id"), "name": card.get("name")}


@app.get("/agents")
async def list_agents():
    """
    v0.4.0 + v0.6.0 — List all Agent Cards hosted by this server.
    Includes: primary card + all cards loaded from AGENTS_MANIFEST.
    """
    all_cards = []

    # Cards loaded from manifest (multi-agent mode)
    manifest_cards = {k: v for k, v in _card_cache.items() if k != "__primary__"}
    if manifest_cards:
        all_cards.extend(manifest_cards.values())
    else:
        # Fallback: AGENTS_DIR local scan (v0.4.0 behaviour)
        agents_dir = os.environ.get("AGENTS_DIR")
        if agents_dir:
            for p in Path(agents_dir).rglob("agent.alp.json"):
                try:
                    with open(p) as f:
                        all_cards.append(json.load(f))
                except Exception:
                    pass

    # Always include primary card if not already in list
    try:
        primary = await get_primary_card()
        primary_id = primary.get("id")
        if not any(c.get("id") == primary_id for c in all_cards):
            all_cards.insert(0, primary)
    except Exception:
        pass

    return {"agents": all_cards}


@app.get("/.well-known/mcp-server-card")
async def well_known_server_card():
    """SEP-2127 compatible MCP Server Card endpoint."""
    try:
        return await get_primary_card()
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/tools")
async def list_tools():
    """Return all tools defined in the Agent Card."""
    card = await get_primary_card()
    return {"tools": card.get("tools", [])}


class ToolInput(BaseModel):
    input: dict[str, Any] = {}


@app.post("/tools/{tool_name}")
async def execute_tool_endpoint(tool_name: str, body: ToolInput):
    """
    Execute a named tool.
    v0.5.0: if the tool endpoint is a full URL, proxies the call automatically.
    """
    result = await execute_tool(tool_name, body.input)
    return result


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"🚀 ALP Server v0.6.0 starting on http://localhost:{PORT}")
    print(f"   Agent card : {AGENT_CARD_URL or AGENT_CARD_PATH}")
    print(f"   Endpoints  : /agent  /agent/refresh  /persona  /tools  /agents  /health  /mcp  /.well-known/mcp-server-card")
    print(f"   Kiro MCP   : http://localhost:{PORT}/mcp")
    if AGENTS_MANIFEST:
        print(f"   Manifest   : {AGENTS_MANIFEST}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)