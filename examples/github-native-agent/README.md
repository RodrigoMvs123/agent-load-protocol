# GitHub-native ALP Agent

This example shows an ALP agent that:
- Lives entirely in a GitHub repository
- Deploys automatically via GitHub Actions
- Manages secrets through GitHub Secrets (never in the card)
- Loads into Kiro with a single prompt and GitHub authentication

## Setup (one time)

### Step 1 — Fork or copy this example

Fork this example or copy these files into a new GitHub repository of your own.

### Step 2 — Add your secrets

Go to your repo on GitHub:
**Settings → Secrets and variables → Actions → New repository secret**

Add the following secrets:

| Secret name | What it is |
|---|---|
| `GEMINI_API_KEY` | Your Google Gemini API key (free quota available at [aistudio.google.com](https://aistudio.google.com)) |
| `RENDER_API_KEY` | Your Render API key (Render dashboard → Account → API Keys) |
| `RENDER_SERVICE_ID` | The ID of your Render web service (visible in the Render dashboard URL) |

### Step 3 — Edit `agent.alp.json`

Open `agent.alp.json` and update:
- `id` — a unique slug for your agent (e.g. `my-research-agent`)
- `name` — human-readable name
- `description` — what your agent does
- `persona` — the system prompt / identity of your agent
- `server.url` — your Render app URL (e.g. `https://my-agent.onrender.com`)

### Step 4 — Push to main

Push your changes. The workflow triggers automatically on push to main.
You can also trigger it manually: **Actions → Deploy ALP Agent → Run workflow**

### Step 5 — Load in Kiro

Once your repo is set up:

1. Open Kiro
2. Connect GitHub MCP (one-time OAuth — Kiro will prompt you)
3. Say: `"Load my agent from github.com/YOUR-USERNAME/YOUR-REPO"`
4. Kiro reads `agent.alp.json` via GitHub MCP (`get_file_contents`)
5. Kiro triggers the deploy workflow via `workflow_dispatch`
6. GitHub Actions deploys your agent with secrets injected
7. Kiro connects to `/mcp` — you can chat with your agent

## How secrets stay safe

GitHub Secrets are designed exactly for this pattern:
- They are stored encrypted in your GitHub repo
- They are **never** returned by the GitHub API — not even to you
- They are injected **only** into the workflow runner at runtime
- They never appear in `agent.alp.json`, in logs, or in any config file

This is the same mechanism used by GitHub Actions CI/CD pipelines worldwide.

## Loading without `get_agent_card` (today)

The `get_agent_card` tool proposed in
[github/github-mcp-server#2299](https://github.com/github/github-mcp-server/issues/2299)
would return a parsed, schema-validated Agent Card in one call.

Until that tool is available, Kiro uses the existing `get_file_contents` tool:

```
get_file_contents({ owner: "user", repo: "my-agent", path: "agent.alp.json" })
```

This returns the raw file. Kiro decodes and parses it. Same result.
If `get_agent_card` is approved and shipped, the step becomes cleaner
with schema validation built in — but it is **not required** for this pattern.

## File structure of your agent repo

```
my-agent-repo/
├── agent.alp.json              ← ALP agent card (public-safe, no secrets)
├── server.py                   ← ALP server (reference or alp-server library)
├── requirements.txt            ← Python dependencies
├── render.yaml                 ← Render deploy config
└── .github/
    └── workflows/
        └── deploy.yml          ← GitHub Actions deploy workflow (copy from ALP repo)
```
