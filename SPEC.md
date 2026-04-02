# Agent Load Protocol (ALP) Specification
Version: 0.4.0

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
| Auth Ref | A string name referencing a credential — never the actual secret |

---

## 3. The Agent Card

The Agent Card is the central artifact of ALP. It is a JSON file that fully describes an agent.

### Minimal valid card

```json
{
  "alp_version": "0.4.0",
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
| `/persona` | GET | ✅ | Returns `{"persona": "...", "id": "...", "name": "..."}` |
| `/tools` | GET | ✅ | Returns `{"tools": [...]}` |
| `/tools/{name}` | POST | ✅ | Executes a tool, returns `{"result": ..., "error": null}` |
| `/health` | GET | ✅ | Returns `{"status": "ok", "alp_version": "0.4.0"}` |
| `/agents` | GET | — | Returns `{"agents": [...]}` — all cards on this server |

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

---

## 5. ALP Client Contract

An ALP Client MUST:

1. Fetch the Agent Card from `GET /agent`
2. Validate the card against the ALP JSON schema
3. Fetch `GET /persona` and inject it as the LLM system prompt
4. Register the agent's tools via `GET /tools`
5. Route LLM calls using the user's chosen provider
6. Never store or expose secrets from the card

---

## 6. Security

- API keys and secrets MUST NOT appear in the Agent Card
- Secrets live in environment variables on the ALP Server only
- The `auth_ref` field on tools is a name — never the actual value
- Transport MUST be HTTPS in production
- See [SECRETS.md](SECRETS.md) for the full guide

---

## 7. LLM Agnosticism

ALP does not prescribe an LLM. The `llm` field is a preference, not a requirement. The ALP Client resolves the final LLM based on:

1. User's explicit choice
2. Agent Card preference
3. Client default

---

## 8. Relation to MCP

ALP is MCP-compatible at the tool layer. Tool endpoints follow MCP conventions so any MCP-compatible host can call ALP tools. ALP extends MCP by adding the Agent Card layer: identity, persona, memory, and LLM routing.

```
ALP  —  agent.alp.json  (identity · persona · tools · memory · llm)
         ↓                    ↓                    ↓
        MCP              SDK transport          HTTP / WS
   tools · chat/IDEs     platform clients     custom frontends
```

---

## 9. Versioning

ALP follows semantic versioning. The `alp_version` field in the Agent Card must match a published ALP version. All releases are backward-compatible — a v0.1.0 card is valid in any v0.4.0 runtime.

See [releases/](releases/) for the full changelog.

---

## 10. Reference Implementations

| Language | Path |
|---|---|
| Python | `reference/server/python/alp_server.py` |
| Node.js / TypeScript | `reference/server/node/alp_server.ts` |
