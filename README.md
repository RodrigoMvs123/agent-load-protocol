# Agent Load Protocol (ALP)

> **ALP is not an agent. ALP is the format that makes your agent portable.**

What [MCP](https://modelcontextprotocol.io) is to tools, ALP is to entire agents.

## The Problem

AI agents are platform-locked. Build one on Relevance AI and you cannot load it into Claude Code. Build one in LangChain and you cannot drop it into another project without rewriting everything. There is no universal format for a complete, portable agent.

## The Solution

ALP defines a single artifact — the **Agent Card** (`agent.alp.json`) — that fully describes any agent:

- Identity and persona (system prompt)
- Tools (MCP-compatible endpoints)
- Memory configuration
- LLM preference (user's choice — any provider)

Any runtime that speaks ALP can load any agent that ships an Agent Card.

## How It Works

```
[ Your agent (anywhere) ]
        ↓  exports
  agent.alp.json        ← the Agent Card
        ↓  served by
  ALP Server            ← exposes /agent, /tools
        ↓  loaded by
  Any runtime           ← Claude Code, Claude UI, OSS projects, Codex
```

## Repositories

| Repo | Purpose |
|---|---|
| `agent-load-protocol` (this) | The protocol spec, schema, reference server |
| [`alp-agent-starter`](https://github.com/RodrigoMvs123/alp-agent-starter) | Hello-world agent implementing ALP |

## Quick Start

### Option A — Fork the starter (recommended)

The fastest way to build an ALP-compatible agent. Fork [alp-agent-starter](https://github.com/RodrigoMvs123/alp-agent-starter), edit `agent.alp.json` with your agent's identity and tools, and run it. The server validates your card against this repo's schema on every startup — if it's invalid, it won't start.

```bash
git clone https://github.com/YOUR-USERNAME/alp-agent-starter
cd alp-agent-starter
pip install -r requirements.txt
cp .env.example .env   # add your API keys
python server.py
```

You'll see:
```
🔍 Validating agent.alp.json against ALP schema...
✅ agent.alp.json is valid ALP v0.1.0
```

Then connect to any MCP-compatible runtime by pointing it to `http://localhost:8000/mcp`.

### Option B — Build from scratch

1. Create an `agent.alp.json` that validates against the schema:

```bash
curl https://raw.githubusercontent.com/RodrigoMvs123/agent-load-protocol/main/schema/agent.alp.schema.json
```

Minimal valid card:

```json
{
  "alp_version": "0.1.0",
  "id": "my-agent",
  "name": "My Agent",
  "persona": "You are a helpful assistant.",
  "llm": { "provider": "any" },
  "server": {
    "url": "https://your-server.com",
    "transport": "http"
  }
}
```

2. Build a server that exposes `/agent`, `/tools`, `/tools/{name}`, and `/mcp`

3. At startup, fetch and validate against the ALP schema — that's what makes it ALP-compliant:

```python
import httpx, jsonschema

SCHEMA_URL = "https://raw.githubusercontent.com/RodrigoMvs123/agent-load-protocol/main/schema/agent.alp.schema.json"

async def validate():
    async with httpx.AsyncClient() as client:
        schema = (await client.get(SCHEMA_URL)).json()
    jsonschema.validate(your_agent_card, schema)
```

### 3. Load into any MCP runtime

```json
{
  "mcpServers": {
    "my-agent": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

Works with Kiro, Claude Code, Claude Desktop, Cursor, and any MCP-compatible client.

## Repository Structure

```
agent-load-protocol/
├── SPEC.md                          ← The protocol specification
├── schema/
│   └── agent.alp.schema.json        ← Agent Card JSON schema
├── reference/
│   └── server/
│       └── python/
│           ├── alp_server.py
│           └── requirements.txt
├── examples/
│   └── hello-agent/
│       └── agent.alp.json
└── .github/
    ├── secrets.template.md
    └── workflows/
        └── validate-schema.yml
```

## Contributing

ALP is an open protocol. Open an issue or a discussion to propose changes to the spec. PRs for new reference implementations (Node.js, Go, etc.) are welcome.

## License

MIT
