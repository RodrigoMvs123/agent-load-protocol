# Agent Load Protocol (ALP) Specification
Version: 0.1.0

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

## 4. The Agent Card

The Agent Card is the central artifact of ALP. It is a JSON file that fully describes an agent.

### 4.1 Minimal Example

```json
{
  "alp_version": "0.1.0",
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
