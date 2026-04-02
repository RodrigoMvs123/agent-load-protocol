"""
Surface 2 — Custom UI example
Calls the ALP Server directly from a Python script (or backend).
Replace with your own frontend framework as needed.
"""

import httpx

ALP_SERVER = "https://your-agent.railway.app"


def load_agent():
    r = httpx.get(f"{ALP_SERVER}/agent")
    r.raise_for_status()
    return r.json()


def get_persona():
    r = httpx.get(f"{ALP_SERVER}/persona")
    r.raise_for_status()
    return r.json()["persona"]


def call_tool(tool_name: str, inputs: dict):
    r = httpx.post(f"{ALP_SERVER}/tools/{tool_name}", json={"input": inputs})
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    card = load_agent()
    print(f"Loaded agent: {card['name']}")
    print(f"Persona: {get_persona()[:80]}...")

    result = call_tool("review_diff", {
        "diff": "+ def foo():\n+     return 1",
        "language": "python"
    })
    print(f"Review result: {result['result']}")
