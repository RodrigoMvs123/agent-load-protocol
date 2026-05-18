# GitHub Secrets — ALP Server

API keys and credentials MUST never appear in `agent.alp.json`.
Store them here as GitHub Secrets and inject at runtime.

## How to add a secret in GitHub

1. Go to your repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add the secrets below

## Required secrets for the GitHub-native agent pattern (v0.9.0)

| Secret name | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key — free quota at [aistudio.google.com](https://aistudio.google.com) |
| `RENDER_API_KEY` | Render deploy API key — found in Render dashboard → Account Settings |
| `RENDER_SERVICE_ID` | Render service ID for this agent — found in the service URL (`srv-...`) |

## Using secrets in your server

In `server.py`, access them via environment variables:

```python
import os
gemini_key = os.environ.get("GEMINI_API_KEY")
```

In GitHub Actions, inject them like this:

```yaml
env:
  GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
  RENDER_SERVICE_ID: ${{ secrets.RENDER_SERVICE_ID }}
```

## Rule

The `agent.alp.json` Agent Card is always public-safe.
Secrets live only in the server environment — never in the card.

The `runtime.deploy.credentials` block in the card lists secret **names** only — never values.
