"""
alp.mcp
-------
MCP JSON-RPC 2.0 message handler.
Supports: initialize, tools/list, tools/call, notifications/*.
"""

import json
from typing import Optional

from . import tools as tool_registry


async def handle(msg: dict, card: dict) -> Optional[dict]:
    """
    Handle a single MCP JSON-RPC 2.0 message.
    Returns the response dict, or None for notifications.
    """
    method = msg.get("method", "")
    msg_id = msg.get("id")
    params = msg.get("params", {})

    # initialize
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": card.get("name", "ALP Agent"),
                    "version": card.get("alp_version", "0.7.0"),
                },
            },
        }

    # tools/list
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": tool_registry.list_mcp(card)},
        }

    # tools/call
    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_input = params.get("arguments", params.get("input", {}))
        try:
            result = await tool_registry.execute(tool_name, tool_input, card)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result)}],
                    "isError": False,
                },
            }
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": str(exc)}],
                    "isError": True,
                },
            }

    # notifications — no response
    if method.startswith("notifications/"):
        return None

    # unknown method
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }