"""
alp-server
----------
Agent Load Protocol — drop-in MCP/SSE middleware for any Python server.

Quick start (FastAPI):

    from fastapi import FastAPI
    from alp import ALPRouter

    app = FastAPI()
    alp = ALPRouter(card_path="agent.alp.json")
    app.include_router(alp.router)

Quick start (Flask):

    from flask import Flask
    from alp.flask import ALPBlueprint

    app = Flask(__name__)
    alp = ALPBlueprint(card_path="agent.alp.json")
    app.register_blueprint(alp.blueprint)
"""

from .fastapi import ALPRouter

__all__ = ["ALPRouter"]
__version__ = "0.7.0"