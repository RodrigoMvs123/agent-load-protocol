# Surface 2 — Custom UI

This example shows an ALP agent powering a custom developer dashboard.
The frontend calls `POST /tools/{name}` directly — no MCP, no chat window.

## Pattern

```
Your frontend  →  POST /tools/review_diff  →  ALP Server  →  result
```

The Agent Card is the API contract. Your UI decides how to render the results.

## Files

- `agent.alp.json` — the Agent Card for a code review agent
- `client.py` — minimal Python client showing how to call the server

## How to run

```bash
# Start the ALP Server with this card
AGENT_CARD_PATH=examples/custom-ui/agent.alp.json \
GITHUB_TOKEN=your-token \
python reference/server/python/alp_server.py

# In another terminal, run the client
pip install httpx
python examples/custom-ui/client.py
```

## Fetching the persona for your UI

```bash
curl http://localhost:8000/persona
# Live equivalent: https://agent-load-protocol.onrender.com/persona
# → {"persona": "You are an expert code reviewer...", "id": "code-reviewer", "name": "Code Reviewer"}
```

Use the persona as the system prompt when you make LLM calls from your own backend.
