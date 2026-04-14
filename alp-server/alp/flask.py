"""
alp.flask
---------
Drop-in Flask blueprint. Mounts all ALP + MCP endpoints on any Flask app.

Usage (3 lines):

    from flask import Flask
    from alp.flask import ALPBlueprint

    app = Flask(__name__)
    alp = ALPBlueprint(card_path="agent.alp.json")
    app.register_blueprint(alp.blueprint)

Note: SSE requires an async-capable Flask setup (Flask 2.x + asgiref or gevent).
For pure sync Flask, the /mcp SSE endpoint uses threading.
"""

import asyncio
import json
import os
import queue
import threading
from typing import Any, Callable, Optional

from . import card as card_module
from . import mcp as mcp_module
from . import tools as tools_module


def _run_async(coro):
    """Run an async coroutine from sync Flask context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


class ALPBlueprint:
    """
    ALP Flask blueprint.
    Register on any Flask app to add /mcp, /agent, /tools, /persona,
    /agents, /health, /agent/refresh endpoints.
    """

    def __init__(
        self,
        card_path: str = "agent.alp.json",
        card_url: Optional[str] = None,
        port: int = None,
        url_prefix: str = "",
    ):
        try:
            from flask import Blueprint
        except ImportError:
            raise ImportError(
                "Flask is not installed. Run: pip install flask"
            )

        self.card_path = card_path
        self.card_url = card_url or os.environ.get("AGENT_CARD_URL")
        self.port = port or int(os.environ.get("PORT", 8000))
        self.blueprint = Blueprint("alp", __name__, url_prefix=url_prefix)
        self._sse_clients: dict[str, queue.Queue] = {}
        self._register_routes()

    def tool(self, tool_name: str) -> Callable:
        """Decorator to register a local Python function as a tool handler."""
        def decorator(fn: Callable) -> Callable:
            tools_module.register(tool_name, fn)
            return fn
        return decorator

    def _get_card(self) -> dict:
        return _run_async(
            card_module.get_card(
                card_path=self.card_path,
                card_url=self.card_url,
            )
        )

    def _register_routes(self) -> None:
        from flask import request, jsonify, Response

        bp = self.blueprint

        @bp.get("/health")
        def health():
            return jsonify({"status": "ok", "alp_version": "0.7.0"})

        @bp.get("/agent")
        def get_agent():
            try:
                return jsonify(self._get_card())
            except Exception as e:
                return jsonify({"error": str(e)}), 404

        @bp.get("/agent/refresh")
        def refresh_agent():
            if not self.card_url:
                return jsonify({"error": "card_url is not set"}), 400
            card_module.invalidate()
            try:
                card = self._get_card()
                return jsonify({
                    "refreshed": True,
                    "id": card.get("id"),
                    "name": card.get("name"),
                    "alp_version": card.get("alp_version"),
                    "source": self.card_url,
                })
            except Exception as exc:
                return jsonify({"error": str(exc)}), 502

        @bp.get("/persona")
        def get_persona():
            card = self._get_card()
            persona = card.get("persona")
            if not persona:
                return jsonify({"error": "No persona defined"}), 404
            return jsonify({"persona": persona, "id": card.get("id"), "name": card.get("name")})

        @bp.get("/agents")
        def list_agents():
            card = self._get_card()
            return jsonify({"agents": [card]})

        @bp.get("/tools")
        def list_tools():
            card = self._get_card()
            return jsonify({"tools": card.get("tools", [])})

        @bp.post("/tools/<tool_name>")
        def execute_tool(tool_name):
            card = self._get_card()
            body = request.get_json(silent=True) or {}
            input_data = body.get("input", body)
            try:
                result = _run_async(tools_module.execute(tool_name, input_data, card))
                return jsonify(result)
            except KeyError as e:
                return jsonify({"error": str(e)}), 404
            except RuntimeError as e:
                return jsonify({"error": str(e)}), 502

        @bp.get("/mcp")
        def mcp_sse():
            import uuid
            session_id = str(uuid.uuid4())
            q: queue.Queue = queue.Queue()
            self._sse_clients[session_id] = q

            def stream():
                try:
                    post_url = f"http://localhost:{self.port}/mcp?session_id={session_id}"
                    yield f"event: endpoint\ndata: {post_url}\n\n"
                    while True:
                        try:
                            msg = q.get(timeout=15)
                            yield f"event: message\ndata: {json.dumps(msg)}\n\n"
                        except queue.Empty:
                            yield ": ping\n\n"
                finally:
                    self._sse_clients.pop(session_id, None)

            return Response(
                stream(),
                mimetype="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                },
            )

        @bp.post("/mcp")
        def mcp_post():
            card = self._get_card()
            session_id = request.args.get("session_id")
            body = request.get_json(silent=True)
            if body is None:
                return jsonify({"error": "invalid JSON"}), 400

            messages = body if isinstance(body, list) else [body]
            last_response = None

            for msg in messages:
                response = _run_async(mcp_module.handle(msg, card))
                if response is None:
                    continue
                if session_id and session_id in self._sse_clients:
                    self._sse_clients[session_id].put(response)
                else:
                    last_response = response

            if last_response:
                return jsonify(last_response)
            return jsonify({"ok": True})