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

### 1. Create your Agent Card

```json
{
  "alp_version": "0.1.0",
  "id": "my-agent",
  "name": "My Agent",
  "persona": "You are a helpful assistant.",
  "llm": { "provider": "any" },
  "tools": [],
  "memory": { "enabled": false },
  "server": {
    "url": "https://your-server.com",
    "transport": "http"
  }
}
```

### 2. Run the reference server

```bash
git clone https://github.com/RodrigoMvs123/agent-load-protocol
cd agent-load-protocol/reference/server/python
pip install -r requirements.txt
AGENT_CARD_PATH=../../examples/hello-agent/agent.alp.json python alp_server.py
```

### 3. Load into Claude Code

In your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "my-agent": {
      "url": "https://your-server.com/tools"
    }
  }
}
```

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
