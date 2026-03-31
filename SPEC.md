# Agent Load Protocol (ALP) Specification
Version: 0.2.0

## 1. Overview

ALP is not an agent. ALP is the format that makes any agent portable.

The Agent Load Protocol defines how an AI agent — its identity, tools, memory, and LLM preference — is packaged, served, and loaded across any runtime or platform.

What MCP (Model Context Protocol) is to tools, ALP is to entire agents.

## 2. Problem Statement

AI agents are platform-locked. An agent built on Relevance AI cannot be loaded into Claude Code. An agent built in LangChain cannot be dropped into an OSS project without rewriting. There is no universal format for describing a complete agent.

ALP solves this with a single portable artifact: the **Agent Card**.

## 3. Terminology

| Term | Definition |
|---|---|
| Agent Card | A JSON file (`agent.alp.json`) describing a complete agent |
| ALP Server | A server that hosts and exposes an Agent Card and its tools |
| ALP Client | Any runtime that fetches and loads an Agent Card |
| Tool Endpoint | An MCP-compatible endpoint exposing the agent's capabilities |
| LLM Router | The component that connects the agent to a user-selected LLM |
| Agent Type | The topology of the agent: `single`, `multi-agent`, or `swarm` |
| Capability | A declared runtime feature the agent supports (e.g. `self-healing`) |
| Auth Ref | A string ID referencing a credential the runtime resolves locally — never the actual secret |

## 4. The Agent Card

The Agent Card is the central artifact of ALP. It is a JSON file that fully describes an agent.

### 4.1 Minimal Example

```json
{
  "alp_version": "0.2.0",
  "id": "my-agent",
  "name": "My Agent",
  "description": "A portable AI agent.",
  "persona": "You are a helpful assistant.",
  "llm": {
    "provider": "any",
    "model": "user-defined"
  },
  "tools": [],
  "memory": {
    "enabled": false
  },
  "server": {
    "url": "https://your-alp-server.com",
    "transport": "http"
  }
}
```

### 4.2 Full Schema Reference

See `schema/agent.alp.schema.json`.

## 5. ALP Server Contract

An ALP Server MUST expose the following HTTP endpoints:

| Endpoint | Method | Description |
|---|---|---|
| `/agent` | GET | Returns the Agent Card JSON |
| `/tools` | GET | Returns list of available tools |
| `/tools/{name}` | POST | Executes a tool, returns result |
| `/health` | GET | Returns `{"status": "ok"}` |

### 5.1 Tool Execution Request

```json
{
  "input": { "key": "value" }
}
```

### 5.2 Tool Execution Response

```json
{
  "result": "...",
  "error": null
}
```

## 6. ALP Client Contract

An ALP Client MUST:

1. Fetch the Agent Card from `GET /agent`
2. Validate the card against the ALP JSON schema
3. Register the agent's tools via `/tools`
4. Route LLM calls using the user's chosen provider
5. Never store or expose secrets from the card

## 7. Security

- API keys and secrets MUST NOT appear in the Agent Card
- Secrets are stored in environment variables or GitHub Secrets
- The ALP Server is responsible for injecting secrets at runtime
- Transport MUST be HTTPS in production

## 8. LLM Agnosticism

ALP does not prescribe an LLM. The `llm` field in the Agent Card is a preference, not a requirement. The ALP Client resolves the final LLM based on:

1. User's explicit choice
2. Agent Card preference
3. Client default

## 9. Versioning

ALP follows semantic versioning. The `alp_version` field in the Agent Card must match a published ALP version.

## 10. Relation to MCP

ALP is MCP-compatible at the tool layer. Tool endpoints follow MCP conventions so that any MCP-compatible host can call ALP tools. ALP extends MCP by adding the Agent Card layer: identity, persona, memory, and LLM routing.

## 11. Agent Types (v0.2.0)

The `agent_type` field describes the topology of the agent. It is optional and defaults to `single`.

| Value | Description |
|---|---|
| `single` | A standalone agent with one identity and one tool set |
| `multi-agent` | A coordinated graph of agents with defined roles |
| `swarm` | A dynamically spawned worker pool controlled by a coordinator (e.g. Hive queen + workers) |

The Agent Card always describes the entry point of the graph — the agent a client loads and calls. Internal topology (worker agents, sub-graphs) is an implementation detail of the runtime.

## 12. Capabilities (v0.2.0)

The `capabilities` array declares what the agent can do at runtime. Clients and marketplaces use this to filter and display agents without running them.

Supported values:

| Capability | Meaning |
|---|---|
| `human-in-the-loop` | Agent can pause and request human input |
| `self-healing` | Agent can detect failures and redeploy or retry |
| `parallel-execution` | Agent can run multiple workers concurrently |
| `streaming` | Agent supports real-time output streaming |
| `memory` | Agent maintains state across sessions |
| `tool-use` | Agent can invoke external tools |
| `code-execution` | Agent can write and run code |
| `web-search` | Agent can search the web |

## 13. Observability (v0.2.0)

The `observability` block describes how to stream or monitor agent execution.

```json
"observability": {
  "websocket": true,
  "endpoint": "/stream",
  "logs_endpoint": "/logs"
}
```

If `websocket` is `true`, the ALP Server SHOULD expose the `endpoint` path for real-time streaming over WebSocket. The `transport` field in `server` should be set to `"websocket"` accordingly.

## 14. Marketplace (v0.2.0)

The `marketplace` block provides metadata for agent discovery platforms (e.g. HoneyComb).

```json
"marketplace": {
  "category": "automation",
  "tags": ["business-process", "self-healing"],
  "pricing_model": "per-run",
  "icon_url": "https://example.com/icon.png"
}
```

A marketplace platform can render a full agent listing from the Agent Card alone — without running the agent.

## 15. Auth References (v0.2.0)

Tools that require credentials use `auth_ref` — a string ID the runtime resolves locally. The Agent Card never contains actual secrets.

```json
{
  "name": "search",
  "description": "Search the web.",
  "endpoint": "/tools/search",
  "auth_ref": "serper_api_key"
}
```

The runtime is responsible for mapping `auth_ref` values to actual credentials via environment variables, a secrets manager, or a bindings file. This keeps the Agent Card safe to share publicly.

## 16. Migration from v0.1.0

All v0.1.0 Agent Cards are valid v0.2.0 cards. The new fields (`agent_type`, `capabilities`, `observability`, `marketplace`) are all optional. No breaking changes.

To upgrade, change `alp_version` to `"0.2.0"` and add any new fields relevant to your agent.

---

## 17. Variables (v0.2.1)

Relevance AI agents use template variables injected into the persona and tool prompts at runtime — e.g. `{{repo_path}}`, `{{main_branch_name}}`. ALP models these in the `variables` block.

The card declares what variables exist and what they mean. The runtime is responsible for resolving their values. Variables are never hardcoded in the card.

```json
"variables": {
  "repo_path": {
    "description": "The GitHub repo path the agent is working in.",
    "required": true
  },
  "main_branch_name": {
    "description": "The name of the main branch in the repo.",
    "required": true,
    "default": "main"
  }
}
```

The persona can reference variables using `{{variable_name}}` syntax. The ALP runtime substitutes them before sending the persona to the LLM.

## 18. Triggers (v0.2.1)

Relevance AI agents can be started automatically by events — emails, schedules, webhooks. ALP models these in the `triggers` array.

```json
"triggers": [
  {
    "type": "webhook",
    "config": { "path": "/trigger/inbound" }
  },
  {
    "type": "schedule",
    "config": { "cron": "0 9 * * 1-5" }
  },
  {
    "type": "email",
    "config": {}
  }
]
```

Supported trigger types: `webhook`, `schedule`, `email`, `manual`, `event`.

The `config` object is trigger-specific and optional. The runtime is responsible for wiring the trigger to the agent's execution.

## 19. Knowledge (v0.2.1)

Relevance AI agents can have documents and data sources attached as knowledge. ALP models these in the `knowledge` array.

```json
"knowledge": [
  {
    "id": "github-api-docs",
    "type": "document",
    "description": "GitHub API reference documentation."
  },
  {
    "id": "project-database",
    "type": "database",
    "description": "Internal project database.",
    "auth_ref": "db_connection_string"
  }
]
```

Knowledge sources use `auth_ref` for credentials, following the same pattern as tools. The card never contains actual connection strings or API keys.

## 20. Platform Origin (v0.2.1)

The `platform` block records where the agent was built. This is useful for traceability — knowing a card was exported from Relevance AI, Hive, or another platform.

```json
"platform": {
  "name": "relevance-ai",
  "agent_id": "bcbe5a-143fe01a-...",
  "project_id": "my-project-id",
  "export_url": "https://app.relevanceai.com/agents/bcbe5a/..."
}
```

This field is informational. It does not affect how the card is loaded or validated.

## 21. Migration from v0.2.0

All v0.2.0 Agent Cards are valid v0.2.1 cards. The new fields (`variables`, `triggers`, `knowledge`, `platform`) are all optional. No breaking changes.

New capabilities added: `github-integration`, `knowledge-retrieval`, `triggered-execution`.

To upgrade, change `alp_version` to `"0.2.1"` and add any new fields relevant to your agent.

---

## 22. Workforce (v0.2.2)

Relevance AI agents connect into multi-agent teams on a visual canvas. ALP models this with the `workforce` block on each agent card.

The card describes the agent's role and its outbound connections. Two connection types mirror Relevance AI's model exactly:

- `ai` — the agent decides when to hand off based on context
- `next-step` — mandatory sequential transition, fires automatically when the agent finishes

```json
"workforce": {
  "role": "manager",
  "connections": [
    {
      "target_agent_id": "writer-agent",
      "connection_type": "next-step",
      "label": "Send draft to writer"
    },
    {
      "target_agent_id": "reviewer-agent",
      "connection_type": "ai",
      "condition": "draft_ready == true",
      "label": "Route to reviewer when draft is ready"
    }
  ]
}
```

Roles: `standalone` (default), `manager`, `worker`, `reviewer`.

The workforce graph is reconstructed by reading the `workforce.connections` of all agents in a deployment. No separate graph file is needed.

## 23. Tool Steps (v0.2.2)

Relevance AI tools follow an `inputs → steps → outputs` pipeline. Each step can use the output of previous steps. ALP models this with the `steps` array on each tool, alongside the existing `input_schema` and new `output_schema`.

```json
{
  "name": "research_company",
  "description": "Researches a company before a sales call.",
  "endpoint": "/tools/research_company",
  "input_schema": {
    "type": "object",
    "required": ["company_name"],
    "properties": {
      "company_name": { "type": "string" }
    }
  },
  "steps": [
    {
      "type": "knowledge_search",
      "name": "search_internal_docs",
      "description": "Search internal knowledge base for existing company info."
    },
    {
      "type": "api_call",
      "name": "web_search",
      "description": "Search the web for recent news and funding.",
      "uses_output_of": "search_internal_docs"
    },
    {
      "type": "llm_prompt",
      "name": "compile_brief",
      "description": "Compile a one-page brief from search results.",
      "uses_output_of": "web_search"
    }
  ],
  "output_schema": {
    "type": "object",
    "properties": {
      "brief": { "type": "string" }
    }
  }
}
```

Step types: `llm_prompt`, `api_call`, `code`, `integration`, `knowledge_search`.

The `steps` array is optional. A tool without steps is treated as a single-step black box — the existing ALP v0.1.0 model.

## 24. Knowledge Retrieval Mode (v0.2.2)

When attaching knowledge to an agent, Relevance AI offers two retrieval modes. ALP models this with `retrieval_mode` on each knowledge item.

```json
"knowledge": [
  {
    "id": "product-docs",
    "type": "document",
    "description": "Product documentation and FAQs.",
    "retrieval_mode": "allow_agent_to_search"
  },
  {
    "id": "quick-reference",
    "type": "document",
    "description": "Small reference card always included in context.",
    "retrieval_mode": "add_all_to_prompt"
  }
]
```

- `add_all_to_prompt` — entire knowledge set included every run. Best for small datasets.
- `allow_agent_to_search` — agent uses RAG to pull only relevant content. Best for large datasets.

Default is `allow_agent_to_search`.

## 25. Alerts (v0.2.2)

Relevance AI agents can notify humans or escalate when something needs attention. ALP models this with the `alerts` array.

```json
"alerts": [
  {
    "trigger": "human_approval_required",
    "action": "pause",
    "channel": "slack",
    "auth_ref": "slack_webhook_url"
  },
  {
    "trigger": "tool_failure",
    "action": "notify",
    "channel": "email",
    "auth_ref": "alert_email_address"
  }
]
```

Actions: `notify`, `escalate`, `pause`, `stop`.

Credentials for notification channels use `auth_ref` — never the actual webhook URL or email address in the card.

## 26. Bulk Schedule (v0.2.2)

Relevance AI supports running an agent across a list of inputs in bulk. ALP models this with the `bulk_schedule` block.

```json
"bulk_schedule": {
  "enabled": true,
  "input_source": "knowledge_table",
  "input_source_ref": "leads_table_id",
  "concurrency": 5
}
```

The `input_source_ref` is a reference ID resolved by the runtime — not the actual data. Supported sources: `knowledge_table`, `csv`, `api_endpoint`.

## 27. API Region (v0.2.2)

Relevance AI API endpoints are region-scoped. The region ID resolves to a base URL:

```
api-<region>.stack.tryrelevance.com/latest/...
```

ALP models this with the `region` field in the `server` block:

```json
"server": {
  "url": "https://api-f1db6c.stack.tryrelevance.com/latest/agents/my-agent-id",
  "transport": "http",
  "region": "f1db6c"
}
```

## 28. Secrets Template Syntax (v0.2.2)

Relevance AI tool steps access custom API keys via template variable syntax:

```
{{secrets.chains_your_api_key}}
```

In ALP, tool-level credentials always use `auth_ref`. The `variables` block documents any secrets that are injected as template variables into tool steps, following the same pattern:

```json
"variables": {
  "secrets.chains_github_token": {
    "description": "GitHub bearer token injected into tool steps.",
    "required": true
  }
}
```

The runtime resolves `{{secrets.chains_github_token}}` at execution time. The value never appears in the card.

## 29. Migration from v0.2.1

All v0.2.1 Agent Cards are valid v0.2.2 cards. All new fields are optional. No breaking changes.

New fields: `workforce`, `alerts`, `bulk_schedule`, `server.region`, `tools[].steps`, `tools[].output_schema`, `knowledge[].retrieval_mode`.

New capabilities: `workforce-member`, `bulk-execution`, `alerting`, `rag`.

To upgrade, change `alp_version` to `"0.2.2"` and add any new fields relevant to your agent.

---

## 30. Toolsets (v0.3.0)

Inspired by MCP's `--toolsets` flag. Tools can be grouped into named sets that a client enables or disables as a unit. This reduces LLM context size and helps the model make better tool choices.

```json
"toolsets": {
  "groups": {
    "default": ["github_api_call", "create_branch", "create_pull_request"],
    "code": ["draft_code", "create_or_update_file"],
    "readonly": ["github_api_call"]
  },
  "active": "default"
}
```

An ALP client MAY allow the user or runtime to select a toolset via env var or flag. Only tools in the active toolset are registered with the LLM.

## 31. Read-Only Mode (v0.3.0)

Inspired by MCP's `--read-only` flag. A safety primitive that strips all mutating tools automatically.

Declared at the card level in `security.read_only` and at the tool level with `tools[].readonly`:

```json
"security": {
  "read_only": false
}
```

```json
{
  "name": "create_pull_request",
  "readonly": false
}
```

When an ALP client loads in read-only mode, it MUST skip all tools where `readonly` is `false`. Read-only tools (e.g. `get_process_status`) remain available.

## 32. OAuth Scopes Per Tool (v0.3.0)

Inspired by MCP's per-tool scope declarations. Each tool can declare exactly which OAuth scopes it requires and which broader scopes are accepted.

```json
{
  "name": "create_pull_request",
  "auth": {
    "type": "oauth",
    "required_scopes": ["repo"],
    "accepted_scopes": ["repo", "public_repo"]
  }
}
```

This is required for marketplace trust — a user loading an agent needs to know upfront what permissions it will request before any tool is called.

Auth types: `bearer_token`, `oauth`, `api_key`, `none`.

## 33. Dynamic Tool Discovery (v0.3.0)

Inspired by MCP's `--dynamic-toolsets` beta. When enabled, the ALP server exposes three meta-endpoints the LLM can call at runtime to discover and enable tools based on what the task needs.

```json
"tools_discovery": {
  "enabled": true,
  "mode": "dynamic"
}
```

When `mode` is `dynamic`, the ALP Server SHOULD expose:

| Endpoint | Method | Description |
|---|---|---|
| `/tools/discover` | GET | Returns all available toolsets and their tools |
| `/tools/enable` | POST | Enables a toolset for the current session |
| `/tools/list` | GET | Returns currently enabled tools |

Default is `static` — tools are fixed at load time.

## 34. Lockdown Mode (v0.3.0)

Inspired by MCP's `--lockdown-mode`. Defends against prompt injection from untrusted content sources (e.g. public repository content, external web pages).

```json
"security": {
  "lockdown_mode": true
}
```

When lockdown is active, the ALP Server MUST filter tool outputs from untrusted sources before passing them to the LLM context. What counts as "untrusted" is runtime-defined — typically any content not authored by a verified workspace member.

## 35. Pagination Standard (v0.3.0)

Inspired by MCP's standardized pagination across all list tools. ALP defines default pagination settings at the card level, and tools that return lists SHOULD include `page`/`per_page` (offset) or `after` (cursor) in their `input_schema`.

```json
"pagination": {
  "style": "offset",
  "default_page_size": 30,
  "max_page_size": 100
}
```

Offset pattern in tool input_schema:
```json
"page": { "type": "integer", "minimum": 1, "default": 1 },
"per_page": { "type": "integer", "minimum": 1, "maximum": 100, "default": 30 }
```

Cursor pattern:
```json
"after": { "type": "string", "description": "Cursor for next page." }
```

## 36. Deprecated Tool Aliases (v0.3.0)

Inspired by MCP's backward-compatible tool aliasing. When a tool is renamed, the old name is preserved as an alias so existing integrations don't break.

```json
{
  "name": "github_api_call",
  "aliases": ["github_call", "gh_api"],
  "deprecated": false,
  "replaces": null
}
```

Rules:
- When a tool is renamed, the old name MUST be listed in `aliases` for at least one major version
- Deprecated tools MUST be flagged with `"deprecated": true`
- ALP clients SHOULD warn users when a deprecated tool is invoked

## 37. Tool Description Overrides (v0.3.0)

Inspired by MCP's env-var-based description overrides. Useful for localization and for tuning tool descriptions to specific LLM behaviors without changing the card.

```json
{
  "name": "github_api_call",
  "description": "Makes an authorized request to the GitHub API.",
  "description_override_key": "TOOL_GITHUB_API_CALL_DESCRIPTION"
}
```

At load time, the ALP server checks for the env var named in `description_override_key`. If set, that value replaces the card's `description` before the tool is registered with the LLM.

## 38. Insiders / Preview Channel (v0.3.0)

Inspired by MCP's insiders mode for early access to experimental tools.

```json
"server": {
  "url": "https://your-alp-server.com",
  "transport": "http",
  "channel": "stable",
  "insiders_url": "https://your-alp-server.com/insiders"
}
```

Channel options: `stable` (default), `beta`, `insiders`.

Clients MAY connect to `insiders_url` when the user opts into experimental features. The insiders channel MAY expose tools not yet in the stable card.

## 39. server.alp.json — Server Manifest (v0.3.0)

Inspired by MCP's `server.json`. A machine-readable server manifest separate from the agent card. Clients read this before connecting to understand what the server supports.

Place `server.alp.json` at the server root alongside `agent.alp.json`:

```json
{
  "name": "my-alp-server",
  "version": "0.3.0",
  "alp_version": "0.3.0",
  "transport": ["http", "websocket"],
  "endpoints": {
    "agent": "/agent",
    "tools": "/tools",
    "health": "/health",
    "discover": "/tools/discover",
    "stream": "/stream"
  },
  "auth": ["bearer_token", "oauth"],
  "channels": ["stable", "insiders"]
}
```

The ALP Server SHOULD expose `GET /server` returning this manifest. Clients MAY use it to negotiate capabilities before loading the full agent card.

## 40. Migration from v0.2.2

All v0.2.2 Agent Cards are valid v0.3.0 cards. All new fields are optional. No breaking changes.

New top-level fields: `toolsets`, `tools_discovery`, `pagination`, `security`.

New tool-level fields: `readonly`, `deprecated`, `aliases`, `replaces`, `auth`, `description_override_key`.

New server fields: `channel`, `insiders_url`, `modes`.

New artifact: `server.alp.json` server manifest.

To upgrade, change `alp_version` to `"0.3.0"` and add any new fields relevant to your agent.
