"""
ALP Reference Server
Agent Load Protocol v0.4.0

Serves an agent.alp.json and its tools over HTTP.
"""

import os
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="ALP Server", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

AGENT_CARD_PATH = os.environ.get("AGENT_CARD_PATH", "agent.alp.json")

def load_card() -> dict:
    path = Path(AGENT_CARD_PATH)
    if not path.exists():
        raise FileNotFoundError(f"Agent card not found: {AGENT_CARD_PATH}")
    with open(path) as f:
        return json.load(f)


class ToolInput(BaseModel):
    input: dict[str, Any] = {}


@app.get("/health")
def health():
    return {"status": "ok", "alp_version": "0.4.0"}


@app.get("/agent")
def get_agent():
    """Return the Agent Card."""
    try:
        return load_card()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/persona")
def get_persona():
    """Return the agent's persona text for system prompt injection."""
    card = load_card()
    persona = card.get("persona")
    if not persona:
        raise HTTPException(status_code=404, detail="No persona defined in Agent Card")
    return {"persona": persona, "id": card.get("id"), "name": card.get("name")}


@app.get("/agents")
def list_agents():
    """
    List all Agent Cards hosted by this server.
    When AGENTS_DIR is set, scans that directory for agent.alp.json files.
    Falls back to the single card at AGENT_CARD_PATH.
    """
    agents_dir = os.environ.get("AGENTS_DIR")
    if agents_dir:
        cards = []
        for p in Path(agents_dir).rglob("agent.alp.json"):
            try:
                with open(p) as f:
                    cards.append(json.load(f))
            except Exception:
                pass
        return {"agents": cards}
    # single-agent fallback
    try:
        return {"agents": [load_card()]}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/.well-known/mcp-server-card")
def well_known_server_card():
    """SEP-2127 compatible MCP Server Card endpoint."""
    try:
        return load_card()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/tools")
def list_tools():
    """Return all tools defined in the Agent Card."""
    card = load_card()
    return {"tools": card.get("tools", [])}


@app.post("/tools/{tool_name}")
def execute_tool(tool_name: str, body: ToolInput):
    """
    Execute a named tool.
    Replace the logic inside each tool block with your real implementation.
    """
    card = load_card()
    tools = {t["name"]: t for t in card.get("tools", [])}

    if tool_name not in tools:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    # --- Add your tool implementations here ---
    # Example:
    # if tool_name == "search":
    #     query = body.input.get("query", "")
    #     result = my_search_function(query)
    #     return {"result": result, "error": None}

    return {
        "result": f"Tool '{tool_name}' executed with input: {body.input}",
        "error": None
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 ALP Server starting on http://localhost:{port}")
    print(f"   Agent card : {AGENT_CARD_PATH}")
    print(f"   Endpoints  : /agent  /persona  /tools  /agents  /health  /.well-known/mcp-server-card")
    uvicorn.run(app, host="0.0.0.0", port=port)