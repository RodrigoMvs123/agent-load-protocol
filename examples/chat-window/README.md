# Surface 3 — Chat Window

This example shows an ALP agent registered as an MCP server in a chat window.
The agent's tools appear as callable functions; its persona shapes every reply.

## Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "web-researcher": {
      "type": "http",
      "url": "https://your-agent.railway.app/tools"
    }
  }
}
```

## Claude Code

```bash
claude mcp add web-researcher --transport http https://your-agent.railway.app/tools
```

## VS Code

`settings.json`:

```json
{
  "mcp.servers": [
    {
      "name": "web-researcher",
      "url": "https://your-agent.railway.app/tools"
    }
  ]
}
```

## Cursor

`.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "web-researcher": {
      "type": "http",
      "url": "https://your-agent.railway.app/tools"
    }
  }
}
```

## How to run locally

```bash
AGENT_CARD_PATH=examples/chat-window/agent.alp.json \
SERPER_API_KEY=your-key \
python reference/server/python/alp_server.py
```

Then use `http://localhost:8000/tools` as the MCP server URL in any of the configs above.
The live equivalent is `https://agent-load-protocol.onrender.com/tools`.

## What happens when the agent loads

1. The runtime fetches `GET /tools` and registers each tool with the LLM.
2. The runtime fetches `GET /persona` and injects it as the system prompt.
3. The user types a question. The LLM decides which tool to call.
4. The runtime calls `POST /tools/web_search` with the query.
5. The ALP Server injects `SERPER_API_KEY` and executes the search.
6. The result is returned to the LLM, which summarises it for the user.
