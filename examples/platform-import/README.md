# Surface 1 — Platform Import

This example shows an Agent Card exported from a platform (Relevance AI)
and loaded into any ALP-compatible runtime.

## What makes this a platform-import card

- The `platform` block records where the agent was built (`relevance-ai`),
  its original `agent_id`, and a link back to the source.
- The card is otherwise identical to any other ALP card — the platform block
  is informational only and does not affect loading.

## How to use it

1. Replace the placeholder values in `agent.alp.json`:
   - `platform.agent_id` — your actual Relevance AI agent ID
   - `platform.project_id` — your Relevance AI project ID
   - `server.url` — your deployed ALP Server URL

2. Deploy the ALP Server pointing at this card:
   ```bash
   AGENT_CARD_PATH=examples/platform-import/agent.alp.json python reference/server/python/alp_server.py
   ```

3. Register in any runtime — see [LOADING.md](../../LOADING.md).

## The platform block

```json
"platform": {
  "name": "relevance-ai",
  "agent_id": "bcbe5a-143fe01a-...",
  "project_id": "my-project-id",
  "export_url": "https://app.relevanceai.com/agents/..."
}
```

This lets a marketplace (e.g. HoneyComb) trace the agent back to its origin
and display provenance information without running the agent.
