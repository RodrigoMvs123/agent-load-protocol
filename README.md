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

### v0.5.0 — Proxy mode

If your agent already has HTTP tool endpoints, the ALP Server forwards calls automatically. No MCP or SSE code needed in your agent:

```
Kiro / Claude Code
        ↓  tools/call via MCP SSE
  ALP Server
        ↓  POST https://your-existing-server.com/api/your-tool
  Your existing agent   ← zero code changes
        ↓  returns result
  Kiro / Claude Code
```

### v0.6.0 — Remote card mode

Ship an `agent.alp.json` in your GitHub repo. Point one hosted ALP Server at it. Your agent is live in Kiro — you never run a server:

```
Your GitHub repo
  └── agent.alp.json    ← you own this, one file

Hosted ALP Server
  └── reads card from GitHub URL
  └── exposes /mcp for Kiro
  └── proxies tool calls to your endpoints
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
| [`alp-agent-starter`](https://github.com/RodrigoMvs123/alp-agent-starter) | Hello-world agent implementing ALP |

---

## Quick Start

### Run locally

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

---

### Option A — Proxy an existing agent (v0.5.0, zero code changes)

Add an `agent.alp.json` pointing at your existing HTTP tool endpoints:

```json
{
  "alp_version": "0.6.0",
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

---

### Option B — Remote card from GitHub (v0.6.0, no server to run)

Add `agent.alp.json` to your GitHub repo. The ALP Server fetches it at startup —
you never need to run your own server.

Edit the URL in the start command to point at your raw GitHub card:

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

---

### Option C — Multi-agent manifest (v0.6.0)

Host multiple agents from one server instance. The manifest file is already
in the repo at `examples/remote-card/agents.json` — edit it to add your
agents' raw GitHub card URLs:

```json
{
  "_comment": "Replace the placeholder URL with each agent's raw GitHub agent.alp.json URL.",
  "agents": [
    "https://raw.githubusercontent.com/YOUR-ORG/YOUR-REPO/main/agent.alp.json"
  ]
}
```

Then start the server pointing at that manifest:

**macOS / Linux:**
```bash
cd reference/server/python
AGENTS_MANIFEST=../../../examples/remote-card/agents.json python alp_server.py
```

**Windows PowerShell:**
```powershell
cd reference\server\python
$env:AGENTS_MANIFEST = "..\..\..\examples\remote-card\agents.json"; python alp_server.py
```

Each agent gets its own MCP endpoint automatically — use its `id` field from the card:

```json
{
  "mcpServers": {
    "agent-a": { "url": "http://localhost:8000/mcp/agent-a" },
    "agent-b": { "url": "http://localhost:8000/mcp/agent-b" }
  }
}
```

---

### Option D — Fork the starter

The fastest way to build an ALP-compatible agent from scratch.

**macOS / Linux:**
```bash
git clone https://github.com/YOUR-USERNAME/alp-agent-starter
cd alp-agent-starter
pip install -r requirements.txt
cp .env.example .env
python server.py
```

**Windows PowerShell:**
```powershell
git clone https://github.com/YOUR-USERNAME/alp-agent-starter
cd alp-agent-starter
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python server.py
```

---

### Load into any MCP runtime

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
├── render.yaml                      ← Render deploy config
├── schema/
│   └── agent.alp.schema.json        ← Agent Card JSON schema
├── reference/
│   └── server/
│       └── python/
│           ├── alp_server.py        ← Reference server (v0.6.0)
│           └── requirements.txt
├── examples/
│   ├── hello-agent/                 ← Minimal starter card
│   ├── remote-card/                 ← agents.json manifest example (v0.6.0)
│   ├── platform-import/             ← Exported from Relevance AI / Hive
│   ├── custom-ui/                   ← Powering a custom frontend
│   └── chat-window/                 ← Registered as MCP server
├── releases/
│   ├── v0.6.0.md                    ← Remote card loading + multi-agent manifest
│   ├── v0.5.0.md                    ← Proxy tool execution + MCP SSE transport
│   ├── v0.4.0.md                    ← /persona, /agents, Node.js server
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