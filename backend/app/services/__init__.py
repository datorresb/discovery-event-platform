"""LLM service — calls the Copilot Proxy to generate events for any city."""

from __future__ import annotations

import datetime
import json
import re

import httpx

from app.models import RawEvent

COPILOT_PROXY_URL = "http://localhost:8080/v1/chat/completions"
MODEL = "claude-sonnet-4"


def _build_prompt(city: str) -> str:
    today = datetime.date.today().isoformat()
    return f"""Generate 8-12 realistic, culturally relevant events happening in {city} over the next 7 days starting from {today}.

Include a MIX of event types: music, culture, food, nightlife, community.
Make events feel authentic to {city}'s character — use real venue names, local cultural references, and local event traditions.

Return ONLY a JSON array. Each object must have exactly these fields:
- "title": string (event name)
- "date": string (ISO 8601 datetime, e.g. "{today}T19:00:00")
- "venue": string (real or realistic venue name in {city})
- "location": "{city}"
- "category": string (one of: music, culture, food, nightlife, community)
- "description": string (1-2 sentences, vivid and specific)
- "source": "ai_generated"
- "source_url": null

Return ONLY the JSON array, no markdown fences, no explanation."""


async def generate_events_for_city(city: str) -> list[RawEvent]:
    """Call the Copilot Proxy LLM to generate events for a city."""
    prompt = _build_prompt(city)

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            COPILOT_PROXY_URL,
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4096,
            },
        )
        resp.raise_for_status()

    data = resp.json()
    content = data["choices"][0]["message"]["content"]

    # Strip markdown code fences if present
    content = re.sub(r"^```(?:json)?\s*", "", content.strip())
    content = re.sub(r"\s*```$", "", content.strip())

    events_json = json.loads(content)

    events: list[RawEvent] = []
    for item in events_json:
        events.append(
            RawEvent(
                title=item["title"],
                date=datetime.datetime.fromisoformat(item["date"]),
                venue=item.get("venue"),
                location=item.get("location", city),
                category=item.get("category"),
                description=item.get("description"),
                source="ai_generated",
                source_url=None,
            )
        )

    return events
