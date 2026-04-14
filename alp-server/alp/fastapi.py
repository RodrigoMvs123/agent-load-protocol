"""
alp.fastapi
-----------
Drop-in FastAPI router. Mounts all ALP + MCP endpoints on any FastAPI app.

Usage (3 lines):

    from fastapi import FastAPI
    from alp import ALPRouter

    app = FastAPI()
    alp = ALPRouter(card_path="agent.alp.json")
    app.include_router(alp.router)

Custom tool registration:

    alp = ALPRouter(card_path="agent.alp.json")

    @alp.tool("greet")
    async def greet(input_data: dict) -> dict:
        return {"message": f"Hello, {input_data.get('name', 'stranger')}!"}

    app.include_router(alp.router)
"""

import os
from typing import Any, Callable, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from . import card as card_module
from . import mcp as mcp_module
from . import sse as sse_module
from . import tools as tools_module


class ALPRouter:
    """
    ALP FastAPI router.
    Mount on any FastAPI app to add /mcp, /agent, /tools, /persona, /agents,
    /health, /agent/refresh endpoints.
    """

    def __init__(
        self,
        card_path: str = "agent.alp.json",
        card_url: Optional[str] = None,
        port: int = None,
        prefix: str = "",
    ):
        self.card_path = card_url or os.environ.get("AGENT_CARD_URL") or card_path
        self.card_url = card_url or os.environ.get("AGENT_CARD_URL")
        self.port = port or int(os.environ.get("PORT", 8000))
        self.router = APIRouter(prefix=prefix)
        self._register_routes()

    def tool(self, tool_name: str) -> Callable:
        """Decorator to register a local Python function as a tool handler."""
        def decorator(fn: Callable) -> Callable:
            tools_module.register(tool_name, fn)
            return fn
        return decorator

    async def _get_card(self) -> dict:
        return await card_module.get_card(
            card_path=self.card_path,
            card_url=self.card_url,
        )

    def _register_routes(self) -> None:

        router = self.router

        # --- Health ---

        @router.get("/health")
        async def health():
            return {"status": "ok", "alp_version": "0.7.0"}

        # --- Agent Card ---

        @router.get("/agent")
        async def get_agent():
            try:
                return await self._get_card()
            except Exception as e:
                raise HTTPException(status_code=404, detail=str(e))

        @router.get("/agent/refresh")
        async def refresh_agent():
            if not self.card_url:
                raise HTTPException(
                    status_code=400,
                    detail="card_url is not set — nothing to refresh"
                )
            card_module.invalidate()
            try:
                card = await self._get_card()
                return {
                    "refreshed": True,
                    "id": card.get("id"),
                    "name": card.get("name"),
                    "alp_version": card.get("alp_version"),
                    "source": self.card_url,
                }
            except Exception as exc:
                raise HTTPException(status_code=502, detail=str(exc))

        # --- Persona ---

        @router.get("/persona")
        async def get_persona():
            card = await self._get_card()
            persona = card.get("persona")
            if not persona:
                raise HTTPException(status_code=404, detail="No persona defined")
            return {"persona": persona, "id": card.get("id"), "name": card.get("name")}

        # --- Agents catalog ---

        @router.get("/agents")
        async def list_agents():
            card = await self._get_card()
            all_cached = card_module.get_all_cached()
            cards = [v for k, v in all_cached.items() if k != "__primary__"]
            if not cards:
                cards = [card]
            return {"agents": cards}

        # --- Tools ---

        @router.get("/tools")
        async def list_tools():
            card = await self._get_card()
            return {"tools": card.get("tools", [])}

        class ToolInput(BaseModel):
            input: dict[str, Any] = {}

        @router.post("/tools/{tool_name}")
        async def execute_tool(tool_name: str, body: ToolInput):
            card = await self._get_card()
            try:
                result = await tools_module.execute(tool_name, body.input, card)
                return result
            except KeyError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except RuntimeError as e:
                raise HTTPException(status_code=502, detail=str(e))

        # --- MCP SSE ---

        @router.get("/mcp")
        async def mcp_sse(request: Request):
            """MCP SSE transport — Kiro connects here."""
            card = await self._get_card()
            session_id, queue = sse_module.create_session()
            post_url = f"http://localhost:{self.port}/mcp?session_id={session_id}"
            stream = sse_module.event_stream(session_id, queue, post_url)
            return StreamingResponse(
                stream,
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        @router.post("/mcp")
        async def mcp_post(request: Request):
            """MCP JSON-RPC receiver — Kiro POSTs here."""
            card = await self._get_card()
            session_id = request.query_params.get("session_id")
            try:
                body = await request.json()
            except Exception:
                return JSONResponse({"error": "invalid JSON"}, status_code=400)

            messages = body if isinstance(body, list) else [body]
            last_response = None

            for msg in messages:
                response = await mcp_module.handle(msg, card)
                if response is None:
                    continue
                if session_id:
                    pushed = await sse_module.push(session_id, response)
                    if not pushed:
                        last_response = response
                else:
                    last_response = response

            if last_response:
                return JSONResponse(last_response)
            return JSONResponse({"ok": True})