# Loading an ALP Agent into Any Runtime

This guide shows how to register a running ALP Server in every major runtime.
All you need is the public HTTPS URL of your deployed ALP Server.

> **Prerequisite:** Your ALP Server must be running and reachable.
> See the [deploy/](deploy/) folder for one-click deploy configs.

---

## Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "my-agent": {
      "type": "http",
      "url": "https://your-agent.railway.app/tools"
    }
  }
}
```

Restart Claude Desktop. Your agent's tools appear in the tool picker.
The persona is injected automatically when the first tool is called.

---

## Claude Code (CLI)

```bash
claude mcp add my-agent --transport http https://your-agent.railway.app/tools
```

Or add it to `.claude/settings.json` in your project:

```json
{
  "mcpServers": {
    "my-agent": {
      "type": "http",
      "url": "https://your-agent.railway.app/tools"
    }
  }
}
```

---

## VS Code (with MCP extension)

Add to your VS Code `settings.json`:

```json
{
  "mcp.servers": [
    {
      "name": "my-agent",
      "url": "https://your-agent.railway.app/tools"
    }
  ]
}
```

Or use the MCP extension's UI: **Command Palette → MCP: Add Server → HTTP → paste URL**.

---

## Cursor

Add to `.cursor/mcp.json` in your project root (or global `~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "my-agent": {
      "type": "http",
      "url": "https://your-agent.railway.app/tools"
    }
  }
}
```

---

## Kiro (AWS)

Add to `.kiro/settings/mcp.json` in your project:

```json
{
  "mcpServers": {
    "my-agent": {
      "type": "http",
      "url": "https://your-agent.railway.app/tools",
      "timeout": 30000
    }
  }
}
```

---

## ChatGPT (Custom GPT / Plugin)

1. Go to **ChatGPT → Explore GPTs → Create → Configure → Add actions**
2. Import the OpenAPI schema from your ALP Server:
   ```
   https://your-agent.railway.app/openapi.json
   ```
3. Set the authentication type to **None** (the ALP Server handles auth internally).
4. Save. Your agent's tools are now available as GPT actions.

---

## Gemini (Google AI Studio / Vertex AI)

Gemini supports function calling via the API. Fetch your tool definitions and
register them as Gemini tools:

```python
import httpx, google.generativeai as genai

tools_resp = httpx.get("https://your-agent.railway.app/tools").json()
persona_resp = httpx.get("https://your-agent.railway.app/persona").json()

# Convert ALP tools to Gemini FunctionDeclarations
gemini_tools = [
    genai.protos.FunctionDeclaration(
        name=t["name"],
        description=t["description"],
        parameters=t.get("input_schema", {})
    )
    for t in tools_resp["tools"]
]

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    system_instruction=persona_resp["persona"],
    tools=gemini_tools
)
```

---

## Injecting the persona manually

Any runtime that supports a system prompt can load the persona directly:

```bash
curl https://your-agent.railway.app/persona
# → {"persona": "You are a helpful assistant...", "id": "my-agent", "name": "My Agent"}
```

Pass the `persona` value as the system prompt before the conversation starts.

---

## Verifying the connection

```bash
# Health check
curl https://your-agent.railway.app/health

# Fetch the Agent Card
curl https://your-agent.railway.app/agent

# List tools
curl https://your-agent.railway.app/tools

# Call a tool
curl -X POST https://your-agent.railway.app/tools/greet \
  -H "Content-Type: application/json" \
  -d '{"input": {"name": "world"}}'
```
