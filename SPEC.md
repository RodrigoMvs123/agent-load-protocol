# Agent Load Protocol (ALP) Specification
Version: 0.7.0

> For the history of what changed in each version, see [releases/](releases/).

---

## 1. Overview

ALP is not an agent. ALP is the format that makes any agent portable.

The Agent Load Protocol defines how an AI agent — its identity, tools, memory, and LLM preference — is packaged, served, and loaded across any runtime or platform.

What MCP (Model Context Protocol) is to tools, ALP is to entire agents.

---

## 2. Core Concepts

| Term | Definition |
|---|---|
| Agent Card | A JSON file (`agent.alp.json`) describing a complete agent |
| ALP Server | A server that hosts and exposes an Agent Card and its tools |
| ALP Client | Any runtime that fetches and loads an Agent Card |
| Tool Endpoint | An MCP-compatible HTTP endpoint exposing a callable function |
| Proxy Tool | A tool whose endpoint is a full URL — the ALP Server forwards the call (v0.5.0) |
| Remote Card | An Agent Card loaded from a public URL at startup (v0.6.0) |
| ALP Library | `pip install alp-server` — drop-in middleware for any Python server (v0.7.0) |
| Auth Ref | A string name referencing a credential — never the actual secret |

---

## 3. The Agent Card

The Agent Card is the central artifact of ALP. It is a JSON file that fully describes an agent.

### Minimal valid card

```json
{
  "alp_version": "0.7.0",
  "id": "my-agent",
  "name": "My Agent",
  "persona": "You are a helpful assistant.",
  "llm": { "provider": "any" },
  "server": {
    "url": "https://your-alp-server.com",
    "transport": "http"
  }
}
```

### Full field reference

| Field | Required | Since | Description |
|---|---|---|---|
| `alp_version` | ✅ | 0.1.0 | Protocol version |
| `id` | ✅ | 0.1.0 | Unique agent identifier |
| `name` | ✅ | 0.1.0 | Human-readable name |
| `description` | — | 0.1.0 | Short description |
| `persona` | ✅ | 0.1.0 | System prompt / agent identity |
| `llm` | ✅ | 0.1.0 | LLM preference (`provider`, `model`) |
| `tools` | — | 0.1.0 | Array of tool definitions |
| `memory` | — | 0.1.0 | Memory config (`enabled`) |
| `server` | ✅ | 0.1.0 | Server URL and transport |
| `metadata` | — | 0.1.0 | Author, version, tags |
| `agent_type` | — | 0.2.0 | `single` / `multi-agent` / `swarm` |
| `capabilities` | — | 0.2.0 | Declared runtime features |
| `observability` | — | 0.2.0 | WebSocket stream + logs endpoints |
| `marketplace` | — | 0.2.0 | Discovery metadata (category, pricing) |
| `variables` | — | 0.2.1 | Runtime template variables |
| `triggers` | — | 0.2.1 | Event-based start conditions |
| `knowledge` | — | 0.2.1 | Attached documents / data sources |
| `platform` | — | 0.2.1 | Provenance (source platform, agent ID) |
| `workforce` | — | 0.2.2 | Multi-agent role + connections |
| `alerts` | — | 0.2.2 | Notification / escalation rules |
| `bulk_schedule` | — | 0.2.2 | Bulk run configuration |
| `toolsets` | — | 0.3.0 | Named tool groups |
| `tools_discovery` | — | 0.3.0 | Dynamic tool discovery config |
| `pagination` | — | 0.3.0 | Default pagination settings |
| `security` | — | 0.3.0 | Read-only mode, lockdown mode |

### Full schema

See [`schema/agent.alp.schema.json`](schema/agent.alp.schema.json).

---

## 4. ALP Server Contract

An ALP Server MUST expose:

| Endpoint | Method | Required | Description |
|---|---|---|---|
| `/agent` | GET | ✅ | Returns the Agent Card JSON |
| `/agent/refresh` | GET | — | Re-fetches card from `AGENT_CARD_URL` (v0.6.0) |
| `/persona` | GET | ✅ | Returns `{"persona": "...", "id": "...", "name": "..."}` |
| `/tools` | GET | ✅ | Returns `{"tools": [...]}` |
| `/tools/{name}` | POST | ✅ | Executes a tool — local or proxied (v0.5.0) |
| `/health` | GET | ✅ | Returns `{"status": "ok", "alp_version": "0.7.0"}` |
| `/agents` | GET | — | Returns all cards hosted by this server (v0.4.0 + v0.6.0) |
| `/mcp` | GET | — | MCP SSE stream — primary agent (v0.5.0) |
| `/mcp` | POST | — | MCP JSON-RPC receiver — primary agent (v0.5.0) |
| `/mcp/{agent_id}` | GET | — | MCP SSE stream — specific agent (v0.6.0) |
| `/mcp/{agent_id}` | POST | — | MCP JSON-RPC receiver — specific agent (v0.6.0) |

### Tool execution

Request:
```json
{ "input": { "key": "value" } }
```

Response:
```json
{ "result": "...", "error": null }
```

### Persona response

```json
{ "persona": "You are a helpful assistant...", "id": "my-agent", "name": "My Agent" }
```

### Proxy Tool Execution (v0.5.0)

When a tool's `endpoint` in the Agent Card is a full URL, the ALP Server
forwards the call via HTTP instead of executing locally.

```json
{
  "name": "search",
  "description": "Search the knowledge base.",
  "endpoint": "https://their-server.com/api/search"
}
```

The ALP Server POSTs `{"input": {...}}` to that URL and returns the result
to the caller. The remote agent needs zero MCP or SSE code.

- Relative endpoint (`/tools/search`) → executes locally on the ALP Server
- Full URL endpoint (`https://...`) → proxied to the remote agent

---

## 5. MCP SSE Transport (v0.5.0)

The ALP Server exposes a full MCP SSE transport layer for runtimes that
require it (Kiro, Claude Desktop, VS Code extensions).

| Endpoint | Method | Description |
|---|---|---|
| `/mcp` | GET | SSE stream — runtime connects here (`text/event-stream`) |
| `/mcp` | POST | MCP JSON-RPC message receiver |

Supported MCP methods: `initialize`, `tools/list`, `tools/call`, `notifications/*`.

### Kiro config (`.kiro/settings/mcp.json`)

```json
{
  "mcpServers": {
    "my-agent": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Claude Code / Claude Desktop config

```json
{
  "mcpServers": {
    "my-agent": {
      "url": "http://localhost:8000/tools"
    }
  }
}
```

---

## 6. Remote Card Loading (v0.6.0)

The ALP Server can load an `agent.alp.json` from any public URL at startup
via the `AGENT_CARD_URL` environment variable.

**Priority order:**
1. `AGENT_CARD_URL` (remote URL) — fetched at startup, cached in memory
2. `AGENT_CARD_PATH` (local file) — fallback if URL not set

**macOS / Linux:**
```bash
AGENT_CARD_URL=https://raw.githubusercontent.com/org/repo/main/agent.alp.json \
  python alp_server.py
```

**Windows PowerShell:**
```powershell
$env:AGENT_CARD_URL = "https://raw.githubusercontent.com/org/repo/main/agent.alp.json"
python alp_server.py
```

### `GET /agent/refresh`

Re-fetches the card from `AGENT_CARD_URL` without restarting the server:

```json
{
  "refreshed": true,
  "id": "my-agent",
  "name": "My Agent",
  "alp_version": "0.7.0",
  "source": "https://raw.githubusercontent.com/..."
}
```

---

## 7. Multi-Agent Manifest (v0.6.0)

A single ALP Server instance can host multiple agents via `AGENTS_MANIFEST` —
a JSON file listing public card URLs. See `examples/remote-card/agent.manifest.json`.

```json
{
  "_comment": "Replace with each agent's raw GitHub agent.alp.json URL.",
  "agents": [
    "https://raw.githubusercontent.com/YOUR-ORG/YOUR-REPO/main/agent.alp.json"
  ]
}
```

Each agent is loaded at startup, cached by its `id` field, and served at:

```
GET  /mcp/{agent_id}   → MCP SSE stream for that agent
POST /mcp/{agent_id}   → MCP JSON-RPC receiver for that agent
```

Kiro multi-agent config:

```json
{
  "mcpServers": {
    "agent-a": { "url": "http://localhost:8000/mcp/agent-a" },
    "agent-b": { "url": "http://localhost:8000/mcp/agent-b" }
  }
}
```

---

## 8. ALP as a Middleware Library (v0.7.0)

The ALP SSE + MCP transport layer is available as an installable Python library.
Any existing FastAPI or Flask server adds full MCP/Kiro connectivity in 3 lines.

```bash
pip install alp-server
```

### FastAPI

```python
from fastapi import FastAPI
from alp import ALPRouter

app = FastAPI()
alp = ALPRouter(card_path="agent.alp.json")
app.include_router(alp.router)
```

### Flask

```python
from flask import Flask
from alp.flask import ALPBlueprint

app = Flask(__name__)
alp = ALPBlueprint(card_path="agent.alp.json")
app.register_blueprint(alp.blueprint)
```

### `@alp.tool()` decorator

Register local Python functions as tool handlers:

```python
@alp.tool("search")
async def search(input_data: dict) -> dict:
    return {"results": my_search(input_data["query"])}
```

**Tool resolution order:**
1. Registered Python function (`@alp.tool()`)
2. Full URL endpoint → proxied via HTTP (v0.5.0)
3. Relative endpoint → stub response

See `alp-server/` in this repo for the full library source.

---

## 9. ALP Client Contract

An ALP Client MUST:

1. Fetch the Agent Card from `GET /agent`
2. Validate the card against the ALP JSON schema
3. Fetch `GET /persona` and inject it as the LLM system prompt
4. Register the agent's tools via `GET /tools`
5. Route LLM calls using the user's chosen provider
6. Never store or expose secrets from the card

---

## 10. Security

- API keys and secrets MUST NOT appear in the Agent Card
- Secrets live in environment variables on the ALP Server only
- The `auth_ref` field on tools is a name — never the actual value
- Transport MUST be HTTPS in production
- See [SECRETS.md](SECRETS.md) for the full guide

---

## 11. LLM Agnosticism

ALP does not prescribe an LLM. The `llm` field is a preference, not a requirement. The ALP Client resolves the final LLM based on:

1. User's explicit choice
2. Agent Card preference
3. Client default

---

## 12. Relation to MCP

ALP is MCP-compatible at the tool layer. Tool endpoints follow MCP conventions so any MCP-compatible host can call ALP tools. ALP extends MCP by adding the Agent Card layer: identity, persona, memory, and LLM routing.

```
ALP  —  agent.alp.json  (identity · persona · tools · memory · llm)
         ↓                    ↓                    ↓
        MCP              SDK transport          HTTP / WS
   tools · chat/IDEs     platform clients     custom frontends
```

---

## 13. Versioning

ALP follows semantic versioning. The `alp_version` field in the Agent Card must match a published ALP version. All releases are backward-compatible — a v0.1.0 card is valid in any v0.7.0 runtime.

See [releases/](releases/) for the full changelog.

---

## 14. Reference Implementations

| Path | Description |
|---|---|
| `reference/server/python/alp_server.py` | Standalone reference server (Python) |
| `reference/server/node/alp_server.ts` | Standalone reference server (Node.js / TypeScript) |
| `alp-server/` | `pip install alp-server` — drop-in middleware library (v0.7.0) |