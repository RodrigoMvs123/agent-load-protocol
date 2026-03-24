"""
ALP Reference Server
Agent Load Protocol v0.1.0

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

app = FastAPI(title="ALP Server", version="0.1.0")

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
    return {"status": "ok", "alp_version": "0.1.0"}


@app.get("/agent")
def get_agent():
    """Return the Agent Card."""
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
    print(f"ALP Server starting on http://localhost:{port}")
    print(f"Agent card: {AGENT_CARD_PATH}")
    uvicorn.run(app, host="0.0.0.0", port=port)