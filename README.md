# Agent Load Protocol (ALP)

> **ALP is not an agent. ALP is the format that makes your agent portable.**

What [MCP](https://modelcontextprotocol.io) is to tools, ALP is to entire agents.

---

## The Problem

AI agents are platform-locked. Build one on Relevance AI and you cannot load it into Claude Code. Build one in LangChain and you cannot drop it into another project without rewriting everything. There is no universal format for a complete, portable agent.

---

## The Solution

ALP defines a single artifact — the **Agent Card** (`agent.alp.json`) — that fully describes any agent:

- Identity and persona (system prompt)
- Tools (MCP-compatible endpoints — local or proxied)
- Memory configuration
- LLM preference (user's choice — any provider)

Any runtime that speaks ALP can load any agent that ships an Agent Card.

---

## How It Works

```
[ Your agent (anywhere) ]
        ↓  exports
  agent.alp.json        ← the Agent Card
        ↓  served by
  ALP Server            ← exposes /agent, /persona, /tools, /agents, /mcp
        ↓  loaded by
  Any runtime           ← Kiro, Claude Code, Claude Desktop, Cursor, VS Code
```

---

## Live Demo

Live reference server: **https://agent-load-protocol.onrender.com**

| Endpoint | URL |
|---|---|
| `/health` | https://agent-load-protocol.onrender.com/health |
| `/agent` | https://agent-load-protocol.onrender.com/agent |
| `/mcp` | https://agent-load-protocol.onrender.com/mcp |

Load the live agent into any MCP-compatible runtime:

```json
{
  "mcpServers": {
    "hello-agent": {
      "type": "http",
      "url": "https://agent-load-protocol.onrender.com/mcp"
    }
  }
}
```

Works with Claude Desktop, Claude Code, VS Code, Cursor, and Kiro — no setup required.

---

## Protocol Stack

```
┌─────────────────────────────────────────────────────────────┐
│  ALP  —  agent.alp.json                                     │
│  identity · persona · tools · memory · llm · auth_ref       │
└────────────┬──────────────────┬──────────────────┬──────────┘
             ↓                  ↓                  ↓
      ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐
      │     MCP     │   │     SDK     │   │   HTTP / WS     │
      │ tools only  │   │ full agent  │   │ direct calls    │
      │ chat/IDEs   │   │ platforms   │   │ custom UIs      │
      └─────────────┘   └─────────────┘   └─────────────────┘
             ↓                  ↓                  ↓
      Claude · VS Code   Relevance AI        Your frontend
      ChatGPT · Kiro     Hive · LangChain
```

- **MCP** exposes tools only — callable functions the LLM can invoke. No persona, no memory.
- **SDK** exposes the full agent but is platform-specific.
- **ALP** describes the whole agent and tells the runtime where to find the MCP-compatible tool endpoints.

---

## Repositories

| Repo | Purpose |
|---|---|
| `agent-load-protocol` (this) | The protocol spec, schema, reference server |
| [`hello-agent-alp-kiro`](https://github.com/RodrigoMvs123/hello-agent-alp-kiro) | Hello-world agent implementing ALP |

---

## Quick Start

### Option A — GitHub-native agent (automatic, recommended for new agents)

The fastest path from zero to a live agent: your agent lives in a GitHub repo, secrets stay in GitHub, deployment is automatic via GitHub Actions.

**Requirements:** GitHub account, Google Gemini API key (free at [aistudio.google.com](https://aistudio.google.com)), Render account (free tier)

1. Fork or copy `examples/github-native-agent/` into a new GitHub repo
2. Add `GEMINI_API_KEY`, `RENDER_API_KEY`, and `RENDER_SERVICE_ID` as GitHub Secrets
   (repo → Settings → Secrets and variables → Actions)
3. Edit `agent.alp.json` — update `id`, `name`, `persona`, and `server.url`
4. Push to main — the deploy workflow triggers automatically
5. Open Kiro, connect GitHub MCP (one-time OAuth)
6. Say: `"Load my agent from github.com/YOUR-USERNAME/YOUR-REPO"`
7. Agent is live in Kiro

See `examples/github-native-agent/README.md` for the full step-by-step guide.

### Option B — pip install (drop into any existing server)

```bash
pip install alp-server
```

**FastAPI — 3 lines:**

```python
from fastapi import FastAPI
from alp import ALPRouter

app = FastAPI()
alp = ALPRouter(card_path="agent.alp.json")
app.include_router(alp.router)
```

**Flask — 3 lines:**

```python
from flask import Flask
from alp.flask import ALPBlueprint

app = Flask(__name__)
alp = ALPBlueprint(card_path="agent.alp.json")
app.register_blueprint(alp.blueprint)
```

**Custom tool registration:**

```python
alp = ALPRouter(card_path="agent.alp.json")

@alp.tool("greet")
async def greet(input_data: dict) -> dict:
    return {"message": f"Hello, {input_data.get('name', 'stranger')}!"}

app.include_router(alp.router)
```

### Option C — Run the reference server locally

**macOS / Linux:**
```bash
git clone https://github.com/RodrigoMvs123/agent-load-protocol
cd agent-load-protocol/reference/server/python
pip install -r requirements.txt
AGENT_CARD_PATH=../../../examples/hello-agent/agent.alp.json python alp_server.py
```

**Windows PowerShell:**
```powershell
git clone https://github.com/RodrigoMvs123/agent-load-protocol
cd agent-load-protocol\reference\server\python
python -m pip install -r requirements.txt
$env:AGENT_CARD_PATH = "..\..\..\examples\hello-agent\agent.alp.json"; python alp_server.py
```

Server starts at `http://localhost:8000`.

### Option D — Proxy an existing agent (zero code changes)

Add an `agent.alp.json` pointing at your existing HTTP tool endpoints:

```json
{
  "alp_version": "0.9.0",
  "id": "my-agent",
  "name": "My Agent",
  "persona": "You are a helpful assistant.",
  "llm": { "provider": "any" },
  "tools": [
    {
      "name": "search",
      "description": "Search the knowledge base.",
      "endpoint": "https://your-existing-server.com/api/search"
    }
  ],
  "server": {
    "url": "http://localhost:8000",
    "transport": "http"
  }
}
```

**macOS / Linux:**
```bash
cd reference/server/python
AGENT_CARD_PATH=../../../your-agent/agent.alp.json python alp_server.py
```

**Windows PowerShell:**
```powershell
cd reference\server\python
$env:AGENT_CARD_PATH = "..\..\..\your-agent\agent.alp.json"; python alp_server.py
```

Connect to Kiro (`.kiro/settings/mcp.json`):

```json
{
  "mcpServers": {
    "my-agent": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

**Your existing agent: zero code changes.**

### Option E — Remote card from GitHub

Add `agent.alp.json` to your GitHub repo. Point the ALP Server at your raw GitHub URL:

**macOS / Linux:**
```bash
cd reference/server/python
AGENT_CARD_URL=https://raw.githubusercontent.com/YOUR-ORG/YOUR-REPO/main/agent.alp.json \
  python alp_server.py
```

**Windows PowerShell:**
```powershell
cd reference\server\python
$env:AGENT_CARD_URL = "https://raw.githubusercontent.com/YOUR-ORG/YOUR-REPO/main/agent.alp.json"
python alp_server.py
```

To refresh the card without restarting:
```
GET http://localhost:8000/agent/refresh
```

### Option F — Multi-agent manifest

Host multiple agents from one server instance. Edit `examples/remote-card/agent.manifest.json`:

```json
{
  "_comment": "Replace with each agent's raw GitHub agent.alp.json URL.",
  "agents": [
    "https://raw.githubusercontent.com/YOUR-ORG/YOUR-REPO/main/agent.alp.json"
  ]
}
```

**macOS / Linux:**
```bash
cd reference/server/python
AGENTS_MANIFEST=../../../examples/remote-card/agent.manifest.json python alp_server.py
```

**Windows PowerShell:**
```powershell
cd reference\server\python
$env:AGENTS_MANIFEST = "..\..\..\examples\remote-card\agent.manifest.json"; python alp_server.py
```

Each agent gets its own MCP endpoint automatically:

```json
{
  "mcpServers": {
    "agent-a": { "url": "http://localhost:8000/mcp/agent-a" },
    "agent-b": { "url": "http://localhost:8000/mcp/agent-b" }
  }
}
```

### Option G — Fork the starter

```bash
git clone https://github.com/YOUR-USERNAME/hello-agent-alp-kiro
cd hello-agent-alp-kiro
pip install -r requirements.txt
cp .env.example .env
python server.py
```

**Windows PowerShell:**
```powershell
git clone https://github.com/YOUR-USERNAME/hello-agent-alp-kiro
cd hello-agent-alp-kiro
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python server.py
```

---

### Connect to any MCP runtime

```json
{
  "mcpServers": {
    "my-agent": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

Works with Kiro, Claude Code, Claude Desktop, Cursor, and any MCP-compatible client.

---

## Repository Structure

```
agent-load-protocol/
├── SPEC.md                          ← The protocol specification
├── LOADING.md                       ← How to load an agent into any runtime
├── SECRETS.md                       ← API key placement guide
├── render.yaml                      ← Render deploy config (root — required by Render)
├── schema/
│   └── agent.alp.schema.json        ← Agent Card JSON schema
├── reference/
│   └── server/
│       ├── python/
│       │   ├── alp_server.py        ← Reference server (/agent /persona /tools /agents /mcp)
│       │   └── requirements.txt
│       └── node/
│           ├── alp_server.ts        ← Node.js / TypeScript reference server
│           └── package.json
├── examples/
│   ├── hello-agent/                 ← Minimal starter card
│   ├── github-native-agent/         ← GitHub-native pattern (v0.9.0)
│   ├── platform-import/             ← Exported from Relevance AI / Hive
│   ├── custom-ui/                   ← Powering a custom frontend
│   ├── chat-window/                 ← Registered as MCP server in Claude / VS Code
│   ├── hive-agent/                  ← Hive swarm agent example
│   ├── relevance-ai-agent/          ← Relevance AI coding agent example
│   └── remote-card/                 ← agent.manifest.json multi-agent example
├── releases/
│   ├── v0.9.0.md
│   ├── v0.7.0.md
│   ├── v0.6.0.md
│   ├── v0.5.0.md
│   ├── v0.4.0.md
│   └── ...
├── deploy/
│   ├── railway.json
│   ├── fly.toml
│   ├── render.yaml
│   └── README.md
└── .github/
    ├── secrets.template.md
    └── workflows/
        └── validate-schema.yml
```

---

## Releases

| Version | Highlights |
|---|---|
| [v0.9.0](releases/v0.9.0.md) | GitHub-native agent: load from repo, secrets via GitHub Actions, auto-deploy to Render, Gemini LLM |
| [v0.7.0](releases/v0.7.0.md) | `pip install alp-server` — `ALPRouter` (FastAPI) + `ALPBlueprint` (Flask) + `@alp.tool()` |
| [v0.6.0](releases/v0.6.0.md) | Remote card loading (`AGENT_CARD_URL`), multi-agent manifest, `/agent/refresh`, `/mcp/{agent_id}` |
| [v0.5.0](releases/v0.5.0.md) | Proxy tool execution, MCP SSE transport (`/mcp`), `httpx` |
| [v0.4.0](releases/v0.4.0.md) | `GET /persona`, `GET /agents`, Node.js server, `LOADING.md`, `SECRETS.md`, `deploy/` |
| [v0.3.0](releases/v0.3.0.md) | Toolsets, security/read-only, dynamic tool discovery, server manifest |
| [v0.2.2](releases/v0.2.2.md) | Workforce, tool steps, alerts, bulk schedule |
| [v0.2.1](releases/v0.2.1.md) | Variables, triggers, knowledge, platform origin |
| [v0.2.0](releases/v0.2.0.md) | Agent types, capabilities, observability, marketplace, auth_ref |
| [v0.1.0](releases/v0.1.0.md) | Initial release |

---

## Contributing

ALP is an open protocol. Open an issue or a discussion to propose changes to the spec. PRs for new reference implementations (Node.js, Go, etc.) are welcome.

## License

MIT
