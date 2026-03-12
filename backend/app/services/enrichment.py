"""LLM enrichment service — adds emoji, color tags, and vibe metadata to events."""

from __future__ import annotations

import json
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

COPILOT_PROXY_URL = "http://localhost:8080/v1/chat/completions"
MODEL = "claude-sonnet-4"

# Category → defaults (used as fallback if LLM is unavailable)
_CATEGORY_DEFAULTS: dict[str, dict[str, str]] = {
    "music": {"emoji": "🎵", "color_tag": "purple", "vibe": "Live & loud"},
    "culture": {"emoji": "🎭", "color_tag": "pink", "vibe": "Art & soul"},
    "food": {"emoji": "🍽️", "color_tag": "amber", "vibe": "Taste & share"},
    "nightlife": {"emoji": "🌙", "color_tag": "blue", "vibe": "After dark"},
    "community": {"emoji": "🤝", "color_tag": "green", "vibe": "Together"},
}

_FALLBACK = {"emoji": "✨", "color_tag": "neutral", "vibe": "Don't miss it"}


def _fallback_enrich(title: str, category: str | None) -> dict[str, str]:
    """Quick rule-based enrichment when LLM is unavailable."""
    if category and category in _CATEGORY_DEFAULTS:
        return _CATEGORY_DEFAULTS[category]
    title_lower = title.lower()
    for cat, defaults in _CATEGORY_DEFAULTS.items():
        if cat in title_lower:
            return defaults
    return _FALLBACK


async def enrich_events(events: list[dict]) -> list[dict]:
    """Enrich a batch of events with emoji, color_tag, and vibe via LLM.

    Each event dict must have at minimum: title, category, description.
    Returns the same list with emoji/color_tag/vibe added.
    Falls back to rule-based enrichment if LLM is unavailable.
    """
    if not events:
        return events

    # Build a compact batch for the LLM (max 30 events at a time)
    batch = events[:30]
    summaries = []
    for i, ev in enumerate(batch):
        summaries.append(
            f"{i}. [{ev.get('category', '?')}] {ev.get('title', '?')}"
        )

    prompt = f"""You are a cultural event curator. For each event below, assign:
1. **emoji** — a single emoji that captures the event's essence (be creative, not generic)
2. **color_tag** — one of: purple, pink, amber, blue, green, red, indigo, teal, orange, neutral
3. **vibe** — a punchy 2-4 word mood/tagline (like "Late night grooves" or "Family fun day")

Events:
{chr(10).join(summaries)}

Return ONLY a JSON array (no markdown fences) where each object has: {{"i": <index>, "emoji": "...", "color_tag": "...", "vibe": "..."}}
Be creative! Avoid repeating the same emoji. Match the mood of each specific event."""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                COPILOT_PROXY_URL,
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2048,
                },
            )
            resp.raise_for_status()

        content = resp.json()["choices"][0]["message"]["content"].strip()
        # Strip markdown fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

        enrichments = json.loads(content)

        # Apply enrichments from LLM
        enrichment_map = {item["i"]: item for item in enrichments}
        for i, ev in enumerate(batch):
            if i in enrichment_map:
                item = enrichment_map[i]
                ev["emoji"] = item.get("emoji", "✨")
                ev["color_tag"] = item.get("color_tag", "neutral")
                ev["vibe"] = item.get("vibe", "")[:50]  # cap vibe length
            else:
                fallback = _fallback_enrich(ev.get("title", ""), ev.get("category"))
                ev.update(fallback)

        # Handle remaining events beyond the batch
        for ev in events[30:]:
            fallback = _fallback_enrich(ev.get("title", ""), ev.get("category"))
            ev.update(fallback)

        logger.info("LLM enriched %d events", len(batch))

    except Exception as exc:
        logger.warning("LLM enrichment failed, using fallback: %s", exc)
        for ev in events:
            fallback = _fallback_enrich(ev.get("title", ""), ev.get("category"))
            ev.update(fallback)

    return events
