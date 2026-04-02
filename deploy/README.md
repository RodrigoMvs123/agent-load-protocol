# Deploy your ALP Agent

Three one-click options. Pick the one you already have an account on.

---

## Railway (recommended — fastest)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

1. Push your repo to GitHub
2. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**
3. Select your repo — Railway detects Python automatically via `requirements.txt`
4. Add environment variables in the Railway dashboard (Settings → Variables):
   ```
   AGENT_CARD_PATH=examples/hello-agent/agent.alp.json
   OPENAI_API_KEY=sk-...
   ```
5. Railway assigns a public URL: `https://your-app.railway.app`

The `deploy/railway.json` in this repo is picked up automatically.

---

## Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# From the repo root
fly launch --config deploy/fly.toml

# Set secrets (never commit these)
fly secrets set OPENAI_API_KEY=sk-... AGENT_CARD_PATH=examples/hello-agent/agent.alp.json

fly deploy
```

Your agent is live at `https://your-alp-agent.fly.dev`.

---

## Render

1. Push your repo to GitHub
2. Go to [render.com](https://render.com) → **New → Web Service → Connect repo**
3. Render reads `deploy/render.yaml` automatically
4. Add secret env vars in the Render dashboard (Environment tab):
   ```
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   ```
5. Click **Deploy**. Your agent is live at `https://alp-agent.onrender.com`.

---

## Verify the deployment

```bash
curl https://your-agent.railway.app/health
# → {"status": "ok", "alp_version": "0.3.0"}

curl https://your-agent.railway.app/agent
# → the full Agent Card JSON
```

Then follow [LOADING.md](../LOADING.md) to register the URL in Claude, VS Code, or any other runtime.
