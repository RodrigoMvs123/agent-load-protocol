# alp-server

> Agent Load Protocol — drop-in MCP/SSE middleware for any Python server.

Add Kiro / Claude Code / MCP connectivity to any existing FastAPI or Flask app in 3 lines.

## Install

```bash
pip install alp-server
```

## FastAPI

```python
from fastapi import FastAPI
from alp import ALPRouter

app = FastAPI()

# Adds /mcp, /agent, /tools, /persona, /agents, /health, /agent/refresh
alp = ALPRouter(card_path="agent.alp.json")
app.include_router(alp.router)

# Your existing routes — untouched
@app.get("/your/existing/route")
async def your_route():
    return {"ok": True}
```

```bash
uvicorn main:app --port 8000
```

## Flask

```bash
pip install alp-server[flask]
```

```python
from flask import Flask
from alp.flask import ALPBlueprint

app = Flask(__name__)

alp = ALPBlueprint(card_path="agent.alp.json")
app.register_blueprint(alp.blueprint)
```

## Custom tool registration

Register Python functions as tool handlers instead of using proxy URLs:

```python
from fastapi import FastAPI
from alp import ALPRouter

app = FastAPI()
alp = ALPRouter(card_path="agent.alp.json")

@alp.tool("greet")
async def greet(input_data: dict) -> dict:
    name = input_data.get("name", "stranger")
    return {"message": f"Hello, {name}!"}

@alp.tool("search")
async def search(input_data: dict) -> dict:
    results = my_search_function(input_data["query"])
    return {"results": results}

app.include_router(alp.router)
```

## Remote card (v0.6.0)

Load the Agent Card from a public GitHub URL:

```python
alp = ALPRouter(
    card_url="https://raw.githubusercontent.com/YOUR-ORG/YOUR-REPO/main/agent.alp.json"
)
```

Or via environment variable:

```bash
AGENT_CARD_URL=https://raw.githubusercontent.com/YOUR-ORG/YOUR-REPO/main/agent.alp.json
```

## Connect to Kiro

Add to `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "my-agent": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

## Endpoints added

| Endpoint | Description |
|---|---|
| `GET /mcp` | MCP SSE stream — Kiro connects here |
| `POST /mcp` | MCP JSON-RPC receiver |
| `GET /agent` | Agent Card JSON |
| `GET /agent/refresh` | Re-fetch remote card |
| `GET /persona` | Agent persona for system prompt |
| `GET /tools` | Tool list |
| `POST /tools/{name}` | Execute a tool |
| `GET /agents` | All hosted cards |
| `GET /health` | Status check |

## Protocol

Part of the [Agent Load Protocol](https://github.com/RodrigoMvs123/agent-load-protocol).

## License

MIT