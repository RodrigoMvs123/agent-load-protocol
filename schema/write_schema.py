import json

schema = {
  "title": "Agent Load Protocol - Agent Card",
  "description": "Schema for a portable ALP Agent Card (agent.alp.json)",
  "type": "object",
  "required": ["alp_version", "id", "name", "persona", "llm", "server"],
  "properties": {
    "alp_version": {"type": "string", "description": "ALP spec version this card targets.", "example": "0.4.0"},
    "id": {"type": "string", "description": "Unique slug identifier for this agent.", "pattern": "^[a-z0-9-]+$"},
    "name": {"type": "string", "description": "Human-readable agent name."},
    "description": {"type": "string", "description": "Short description of what this agent does."},
    "agent_type": {
      "type": "string",
      "enum": ["single", "multi-agent", "swarm"],
      "default": "single",
      "description": "Topology of the agent."
    },
    "capabilities": {
      "type": "array",
      "description": "Declared runtime capabilities.",
      "items": {
        "type": "string",
        "enum": [
          "human-in-the-loop", "self-healing", "parallel-execution", "streaming",
          "memory", "tool-use", "code-execution", "web-search", "github-integration",
          "knowledge-retrieval", "triggered-execution", "workforce-member",
          "bulk-execution", "alerting", "rag"
        ]
      }
    },
    "persona": {"type": "string", "description": "System prompt / identity."},
    "llm": {
      "type": "object",
      "required": ["provider"],
      "properties": {
        "provider": {"type": "string", "enum": ["any", "openai", "anthropic", "google", "mistral", "ollama"]},
        "model": {"type": "string"}
      }
    },
    "toolsets": {
      "type": "object",
      "description": "Named groups of tools that can be enabled or disabled as a unit. New in v0.3.0.",
      "properties": {
        "groups": {
          "type": "object",
          "description": "Map of toolset name to list of tool names.",
          "additionalProperties": {"type": "array", "items": {"type": "string"}}
        },
        "active": {
          "type": "string",
          "description": "The toolset active by default. Must match a key in groups.",
          "default": "default"
        }
      }
    },
    "tools_discovery": {
      "type": "object",
      "description": "Dynamic tool discovery configuration. New in v0.3.0.",
      "properties": {
        "enabled": {"type": "boolean", "default": False},
        "mode": {
          "type": "string",
          "enum": ["static", "dynamic"],
          "default": "static",
          "description": "static: tools fixed at load time. dynamic: server exposes /tools/discover, /tools/enable, /tools/list at runtime."
        }
      }
    },
    "pagination": {
      "type": "object",
      "description": "Default pagination settings for list tools. New in v0.3.0.",
      "properties": {
        "style": {
          "type": "string",
          "enum": ["offset", "cursor"],
          "default": "offset",
          "description": "offset: page/per_page. cursor: after field for GraphQL-style pagination."
        },
        "default_page_size": {"type": "integer", "default": 30},
        "max_page_size": {"type": "integer", "default": 100}
      }
    },
    "security": {
      "type": "object",
      "description": "Runtime security configuration. New in v0.3.0.",
      "properties": {
        "read_only": {
          "type": "boolean",
          "default": False,
          "description": "When true, the ALP client MUST skip all tools where readonly is false."
        },
        "lockdown_mode": {
          "type": "boolean",
          "default": False,
          "description": "When true, tool outputs from untrusted sources are filtered before reaching the LLM context."
        },
        "max_tool_retries": {
          "type": "integer",
          "default": 5,
          "description": "Maximum number of times a tool call may be retried before the agent stops."
        }
      }
    },
    "tools": {
      "type": "array",
      "description": "List of tools this agent exposes.",
      "items": {
        "type": "object",
        "required": ["name", "description", "endpoint"],
        "properties": {
          "name": {"type": "string"},
          "description": {"type": "string"},
          "endpoint": {"type": "string"},
          "readonly": {
            "type": "boolean",
            "default": False,
            "description": "When true, this tool performs no mutations. Clients in read_only mode MUST skip tools where readonly is false."
          },
          "deprecated": {
            "type": "boolean",
            "default": False,
            "description": "When true, this tool is deprecated. Clients SHOULD warn users."
          },
          "aliases": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Previous names for this tool preserved for backward compatibility."
          },
          "replaces": {
            "type": "string",
            "description": "Name of the tool this one replaces, if any."
          },
          "auth": {
            "type": "object",
            "description": "Auth requirements for this tool. New in v0.3.0.",
            "properties": {
              "type": {"type": "string", "enum": ["bearer_token", "oauth", "api_key", "none"], "default": "none"},
              "required_scopes": {"type": "array", "items": {"type": "string"}, "description": "OAuth scopes required for this tool to function."},
              "accepted_scopes": {"type": "array", "items": {"type": "string"}, "description": "Broader set of OAuth scopes that satisfy this tool."}
            }
          },
          "auth_ref": {"type": "string", "description": "Credential reference ID. Never the actual secret."},
          "input_schema": {"type": "object"},
          "output_schema": {"type": "object"},
          "steps": {
            "type": "array",
            "description": "Ordered pipeline of steps the tool executes internally.",
            "items": {
              "type": "object",
              "required": ["type"],
              "properties": {
                "type": {"type": "string", "enum": ["llm_prompt", "api_call", "code", "integration", "knowledge_search"]},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "uses_output_of": {"type": "string"}
              }
            }
          },
          "description_override_key": {
            "type": "string",
            "description": "Env var key the runtime checks to override this tool description at load time. e.g. TOOL_GITHUB_API_CALL_DESCRIPTION."
          }
        }
      }
    },
    "memory": {
      "type": "object",
      "properties": {
        "enabled": {"type": "boolean", "default": False},
        "backend": {"type": "string"}
      }
    },
    "observability": {
      "type": "object",
      "description": "Observability and streaming config.",
      "properties": {
        "websocket": {"type": "boolean", "default": False},
        "endpoint": {"type": "string"},
        "logs_endpoint": {"type": "string"}
      }
    },
    "marketplace": {
      "type": "object",
      "description": "Marketplace listing metadata.",
      "properties": {
        "category": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "pricing_model": {"type": "string", "enum": ["free", "per-run", "subscription", "custom"]},
        "icon_url": {"type": "string", "format": "uri"}
      }
    },
    "variables": {
      "type": "object",
      "description": "Runtime template variables injected into persona and tool prompts.",
      "additionalProperties": {
        "type": "object",
        "required": ["description"],
        "properties": {
          "description": {"type": "string"},
          "required": {"type": "boolean", "default": False},
          "default": {"type": "string"}
        }
      }
    },
    "triggers": {
      "type": "array",
      "description": "Events that automatically start the agent.",
      "items": {
        "type": "object",
        "required": ["type"],
        "properties": {
          "type": {"type": "string", "enum": ["webhook", "schedule", "email", "manual", "event"]},
          "config": {"type": "object"}
        }
      }
    },
    "knowledge": {
      "type": "array",
      "description": "Knowledge sources attached to the agent.",
      "items": {
        "type": "object",
        "required": ["id", "type"],
        "properties": {
          "id": {"type": "string"},
          "type": {"type": "string", "enum": ["document", "url", "database", "api"]},
          "description": {"type": "string"},
          "auth_ref": {"type": "string"},
          "retrieval_mode": {
            "type": "string",
            "enum": ["add_all_to_prompt", "allow_agent_to_search"],
            "default": "allow_agent_to_search"
          }
        }
      }
    },
    "platform": {
      "type": "object",
      "description": "Origin platform metadata.",
      "properties": {
        "name": {"type": "string"},
        "agent_id": {"type": "string"},
        "project_id": {"type": "string"},
        "export_url": {"type": "string", "format": "uri"}
      }
    },
    "workforce": {
      "type": "object",
      "description": "Workforce role and connections for multi-agent teams.",
      "properties": {
        "role": {"type": "string", "enum": ["standalone", "manager", "worker", "reviewer"], "default": "standalone"},
        "connections": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["target_agent_id", "connection_type"],
            "properties": {
              "target_agent_id": {"type": "string"},
              "connection_type": {"type": "string", "enum": ["ai", "next-step"]},
              "condition": {"type": "string"},
              "label": {"type": "string"}
            }
          }
        }
      }
    },
    "alerts": {
      "type": "array",
      "description": "Alert and escalation rules.",
      "items": {
        "type": "object",
        "required": ["trigger", "action"],
        "properties": {
          "trigger": {"type": "string"},
          "action": {"type": "string", "enum": ["notify", "escalate", "pause", "stop"]},
          "channel": {"type": "string"},
          "auth_ref": {"type": "string"}
        }
      }
    },
    "bulk_schedule": {
      "type": "object",
      "description": "Bulk execution configuration.",
      "properties": {
        "enabled": {"type": "boolean", "default": False},
        "input_source": {"type": "string"},
        "input_source_ref": {"type": "string"},
        "concurrency": {"type": "integer", "minimum": 1, "default": 1}
      }
    },
    "server": {
      "type": "object",
      "required": ["url", "transport"],
      "properties": {
        "url": {"type": "string", "format": "uri"},
        "transport": {"type": "string", "enum": ["http", "sse", "websocket"]},
        "region": {"type": "string", "description": "Region ID for region-scoped API endpoints."},
        "channel": {
          "type": "string",
          "enum": ["stable", "beta", "insiders"],
          "default": "stable",
          "description": "Release channel. insiders gives access to experimental tools."
        },
        "insiders_url": {"type": "string", "format": "uri", "description": "Alternate URL for the insiders channel."},
        "modes": {
          "type": "object",
          "description": "Server-level mode flags.",
          "properties": {
            "read_only": {"type": "boolean", "default": False},
            "lockdown": {"type": "boolean", "default": False}
          }
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "author": {"type": "string"},
        "version": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "repository": {"type": "string", "format": "uri"}
      }
    }
  }
}

with open("agent-load-protocol/schema/agent.alp.schema.json", "w", encoding="utf-8") as f:
    json.dump(schema, f, indent=2)

print("done - fields:", list(schema["properties"].keys()))
