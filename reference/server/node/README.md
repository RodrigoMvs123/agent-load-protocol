# ALP Reference Server — Node.js / TypeScript

A TypeScript port of the Python reference server. Feature-identical:
`/agent`, `/persona`, `/tools`, `/tools/{name}`, `/agents`, `/health`.

## Requirements

- Node.js 18+

## Quick start

```bash
cd reference/server/node
npm install

# Point at an Agent Card and run
AGENT_CARD_PATH=../../../examples/hello-agent/agent.alp.json npm start
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `AGENT_CARD_PATH` | `agent.alp.json` | Path to the Agent Card |
| `AGENTS_DIR` | — | Directory to scan for multiple Agent Cards (`GET /agents`) |
| `PORT` | `8000` | Port to listen on |

## Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | `{"status": "ok", "alp_version": "0.3.0"}` |
| `/agent` | GET | Returns the Agent Card JSON |
| `/persona` | GET | Returns `{"persona": "...", "id": "...", "name": "..."}` |
| `/tools` | GET | Returns `{"tools": [...]}` |
| `/tools/{name}` | POST | Executes a tool |
| `/agents` | GET | Returns all Agent Cards hosted by this server |

## Adding tool implementations

Edit `alp_server.ts` and add your logic inside the `/tools/:tool_name` handler:

```typescript
if (tool_name === "greet") {
  const name = req.body.input?.name ?? "world";
  return { result: `Hello, ${name}!`, error: null };
}
```
