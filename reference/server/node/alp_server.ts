/**
 * ALP Reference Server — Node.js / TypeScript
 * Agent Load Protocol v0.4.0
 *
 * Serves an agent.alp.json and its tools over HTTP.
 * Mirrors the Python reference server (reference/server/python/alp_server.py).
 */

import Fastify from "fastify";
import cors from "@fastify/cors";
import { readFileSync, readdirSync, statSync } from "fs";
import { join, resolve } from "path";

const app = Fastify({ logger: false });
await app.register(cors, { origin: "*" });

const AGENT_CARD_PATH = resolve(
  process.env.AGENT_CARD_PATH ?? "agent.alp.json"
);
const AGENTS_DIR = process.env.AGENTS_DIR
  ? resolve(process.env.AGENTS_DIR)
  : null;

function loadCard(): Record<string, unknown> {
  try {
    return JSON.parse(readFileSync(AGENT_CARD_PATH, "utf8"));
  } catch {
    throw new Error(`Agent card not found: ${AGENT_CARD_PATH}`);
  }
}

function findCards(dir: string): Record<string, unknown>[] {
  const cards: Record<string, unknown>[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      cards.push(...findCards(full));
    } else if (entry === "agent.alp.json") {
      try {
        cards.push(JSON.parse(readFileSync(full, "utf8")));
      } catch {}
    }
  }
  return cards;
}

// ── Routes ────────────────────────────────────────────────────────────────────

app.get("/health", async () => ({ status: "ok", alp_version: "0.4.0" }));

app.get("/agent", async (_req, reply) => {
  try {
    return loadCard();
  } catch (e: unknown) {
    reply.status(404).send({ detail: (e as Error).message });
  }
});

app.get("/persona", async (_req, reply) => {
  const card = loadCard();
  const persona = card.persona as string | undefined;
  if (!persona) {
    return reply
      .status(404)
      .send({ detail: "No persona defined in Agent Card" });
  }
  return { persona, id: card.id, name: card.name };
});

app.get("/tools", async () => {
  const card = loadCard();
  return { tools: (card.tools as unknown[]) ?? [] };
});

app.get("/agents", async () => {
  if (AGENTS_DIR) {
    return { agents: findCards(AGENTS_DIR) };
  }
  try {
    return { agents: [loadCard()] };
  } catch (e: unknown) {
    return { agents: [], error: (e as Error).message };
  }
});

app.post<{ Params: { tool_name: string }; Body: { input?: Record<string, unknown> } }>(
  "/tools/:tool_name",
  async (req, reply) => {
    const card = loadCard();
    const tools = Object.fromEntries(
      ((card.tools as { name: string }[]) ?? []).map((t) => [t.name, t])
    );
    const { tool_name } = req.params;

    if (!tools[tool_name]) {
      return reply
        .status(404)
        .send({ detail: `Tool '${tool_name}' not found` });
    }

    // --- Add your tool implementations here ---
    // if (tool_name === "greet") {
    //   const name = req.body.input?.name ?? "world";
    //   return { result: `Hello, ${name}!`, error: null };
    // }

    return {
      result: `Tool '${tool_name}' executed with input: ${JSON.stringify(req.body.input ?? {})}`,
      error: null,
    };
  }
);

// ── Start ─────────────────────────────────────────────────────────────────────

const port = parseInt(process.env.PORT ?? "8000", 10);
await app.listen({ port, host: "0.0.0.0" });
console.log(`🚀 ALP Server (Node.js) starting on http://localhost:${port}`);
console.log(`   Agent card : ${AGENT_CARD_PATH}`);
console.log(`   Endpoints  : /agent  /persona  /tools  /agents  /health`);
