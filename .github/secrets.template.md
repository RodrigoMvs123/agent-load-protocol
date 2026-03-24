# GitHub Secrets — ALP Server

API keys and credentials MUST never appear in `agent.alp.json`.
Store them here as GitHub Secrets and inject at runtime.

## How to add a secret in GitHub

1. Go to your repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add the secrets below

## Required secrets for the reference server

| Secret name | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key (if using GPT models) |
| `ANTHROPIC_API_KEY` | Anthropic API key (if using Claude) |
| `GOOGLE_API_KEY` | Google API key (if using Gemini) |

## Using secrets in your server

In `alp_server.py`, access them via environment variables:

```python
import os
openai_key = os.environ.get("OPENAI_API_KEY")
```

In GitHub Actions, inject them like this:

```yaml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## Rule

The `agent.alp.json` Agent Card is always public-safe.
Secrets live only in the server environment — never in the card.