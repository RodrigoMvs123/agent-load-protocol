# API Key & Secrets Guide

## The rule

> The `agent.alp.json` Agent Card is always public-safe.
> API keys and secrets live **only** in environment variables on the ALP Server.
> They never appear in the card, in the chat window, or in any runtime config.

The card references secrets by name using `auth_ref`:

```json
{
  "name": "web_search",
  "description": "Search the web.",
  "endpoint": "/tools/web_search",
  "auth_ref": "serper_api_key"
}
```

At runtime, the ALP Server reads `os.environ["SERPER_API_KEY"]` and injects it
into the tool call. The key never leaves the server.

---

## Where keys go per runtime

| Runtime | Where the key goes |
|---|---|
| ALP Server (all cases) | `.env` file locally, or deployment env vars (Railway / Fly.io / Render dashboard) |
| Claude Desktop | ALP Server env only — Claude receives tool results, never raw keys |
| Claude Code | ALP Server env only — same principle |
| ChatGPT Plugin | ALP Server env only — GPT actions call your server, not the LLM API directly |
| VS Code / Cursor / Kiro | ALP Server env only — the IDE calls the server's endpoints |
| Gemini | ALP Server env only |
| GitHub Actions (CI/CD) | GitHub Secrets → injected as env vars into the server on deploy |

---

## Local development

```bash
cp .env.example .env
# Edit .env and fill in your keys — this file is gitignored
```

`.env.example` (safe to commit — no real values):

```bash
# LLM provider keys — injected by the ALP Server, never put in the card
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=

# Tool-specific keys — referenced via auth_ref in the card
SERPER_API_KEY=
GITHUB_TOKEN=

# Server config
PORT=8000
AGENT_CARD_PATH=examples/hello-agent/agent.alp.json
```

---

## Deployed environments

### Railway

Set in the Railway dashboard: **Project → Settings → Variables**

```
OPENAI_API_KEY=sk-...
SERPER_API_KEY=abc...
AGENT_CARD_PATH=examples/hello-agent/agent.alp.json
```

### Fly.io

```bash
fly secrets set OPENAI_API_KEY=sk-... SERPER_API_KEY=abc...
```

### Render

Set in the Render dashboard: **Service → Environment → Add Environment Variable**

---

## GitHub Actions (CI/CD)

Store secrets in **GitHub repo → Settings → Secrets and variables → Actions**.

Reference them in your workflow:

```yaml
- name: Deploy ALP Server
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    SERPER_API_KEY: ${{ secrets.SERPER_API_KEY }}
  run: fly deploy
```

---

## What the card CAN contain

| Field | Safe? | Notes |
|---|---|---|
| `id`, `name`, `description` | ✅ | Always public |
| `persona` | ✅ | Public — it's a system prompt, not a secret |
| `tools[].name`, `tools[].description` | ✅ | Public |
| `tools[].auth_ref` | ✅ | A name only — not the actual key |
| `server.url` | ✅ | Public endpoint |
| Any actual API key | ❌ | Never — use `auth_ref` instead |
| Connection strings | ❌ | Never — use `auth_ref` instead |
| Passwords | ❌ | Never |
