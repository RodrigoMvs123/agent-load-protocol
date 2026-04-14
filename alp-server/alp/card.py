"""
alp.card
--------
Agent Card loader + validator.
Supports local file (card_path) and remote URL (card_url).
Includes in-memory cache with refresh support.
"""

import json
from pathlib import Path
from typing import Optional

import httpx


_cache: dict[str, dict] = {}


def load_local(card_path: str) -> dict:
    """Load an Agent Card from a local file."""
    path = Path(card_path)
    if not path.exists():
        raise FileNotFoundError(f"Agent card not found: {card_path}")
    with open(path) as f:
        return json.load(f)


async def load_remote(url: str) -> dict:
    """Load an Agent Card from a public URL."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Failed to fetch card from '{url}': HTTP {exc.response.status_code}"
        )
    except httpx.RequestError as exc:
        raise RuntimeError(
            f"Connection error fetching card from '{url}': {str(exc)}"
        )


async def get_card(
    card_path: str = "agent.alp.json",
    card_url: Optional[str] = None,
    cache_key: str = "__primary__",
    use_cache: bool = True,
) -> dict:
    """
    Return an Agent Card.
    Priority: card_url (remote) > card_path (local file).
    Results are cached in memory; pass use_cache=False to force reload.
    """
    if use_cache and cache_key in _cache:
        return _cache[cache_key]

    if card_url:
        card = await load_remote(card_url)
    else:
        card = load_local(card_path)

    _cache[cache_key] = card
    return card


def invalidate(cache_key: str = "__primary__") -> None:
    """Remove a card from the cache so it will be reloaded on next access."""
    _cache.pop(cache_key, None)


def get_all_cached() -> dict[str, dict]:
    """Return all cached cards."""
    return dict(_cache)