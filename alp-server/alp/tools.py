"""
alp.tools
---------
Tool registry + proxy executor.

- Tools with a full URL endpoint are proxied via HTTP (v0.5.0)
- Tools with a relative endpoint are executed via registered Python functions
- The @alp.tool() decorator registers local Python functions as tools
"""

from typing import Any, Callable, Optional
import httpx


# Global tool function registry: tool_name -> async callable
_tool_registry: dict[str, Callable] = {}


def register(tool_name: str, fn: Callable) -> None:
    """Register a Python function as the handler for a named tool."""
    _tool_registry[tool_name] = fn


def get_registered(tool_name: str) -> Optional[Callable]:
    """Return the registered function for a tool, or None."""
    return _tool_registry.get(tool_name)


def list_mcp(card: dict) -> list[dict]:
    """Return the MCP-formatted tool list from an Agent Card."""
    return [
        {
            "name": t["name"],
            "description": t.get("description", ""),
            "inputSchema": t.get("input_schema", {"type": "object", "properties": {}}),
        }
        for t in card.get("tools", [])
    ]


async def execute(tool_name: str, input_data: dict, card: dict) -> Any:
    """
    Execute a tool.

    Resolution order:
    1. Registered Python function (@alp.tool decorator)
    2. Full URL endpoint → proxy via HTTP (v0.5.0)
    3. Relative endpoint → stub response
    """
    tools = {t["name"]: t for t in card.get("tools", [])}

    if tool_name not in tools:
        raise KeyError(f"Tool '{tool_name}' not found in Agent Card")

    # 1. Registered local function
    fn = get_registered(tool_name)
    if fn is not None:
        return await fn(input_data)

    tool = tools[tool_name]
    endpoint = tool.get("endpoint", "")

    # 2. Proxy execution (v0.5.0)
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
            raise RuntimeError(
                f"Proxy error from '{endpoint}': HTTP {exc.response.status_code}"
            )
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Proxy connection error to '{endpoint}': {str(exc)}"
            )

    # 3. Local stub — override by registering a function with @alp.tool()
    return {
        "result": f"Tool '{tool_name}' executed with input: {input_data}",
        "error": None,
    }