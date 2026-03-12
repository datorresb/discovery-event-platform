"""AllEvents.in scraper for Montreal events.

Fetches the AllEvents.in Montreal page and extracts event data
from embedded JSON-LD (schema.org) structured data.
This is an independent aggregator source, providing cross-source diversity.
"""

from __future__ import annotations

import datetime
import json
import logging

import httpx
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date

from app.models import RawEvent
from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

SEARCH_URL = "https://allevents.in/montreal/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

_CATEGORY_KEYWORDS = {
    "music": ["concert", "music", "dj", "band", "jazz", "rock", "hip hop",
              "techno", "house", "rave", "festival", "live", "sing", "opera",
              "orchestra", "symphony"],
    "food": ["food", "wine", "beer", "brunch", "dinner", "tasting", "culinary",
             "cook", "restaurant", "market", "marché", "gastro"],
    "culture": ["art", "museum", "gallery", "theatre", "theater", "film", "cinema",
                "exhibit", "heritage", "culture", "literary", "book", "dance",
                "ballet", "cirque"],
    "nightlife": ["club", "nightlife", "afterhours", "warehouse", "lounge",
                  "bar crawl", "drag", "cabaret", "burlesque"],
    "community": ["community", "meetup", "workshop", "class", "networking",
                  "volunteer", "charity", "run", "walk", "yoga", "wellness",
                  "conference", "summit", "expo"],
}


def _guess_category(title: str, description: str | None) -> str | None:
    text = (title + " " + (description or "")).lower()
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return cat
    return None


class AllEventsMtlScraper(BaseScraper):
    """Scrapes real events from AllEvents.in Montreal via JSON-LD."""

    def source_name(self) -> str:
        return "allevents"

    def scrape(self) -> list[RawEvent]:
        try:
            resp = httpx.get(
                SEARCH_URL,
                headers=HEADERS,
                timeout=20.0,
                follow_redirects=True,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("AllEvents.in fetch failed: %s", exc)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        # AllEvents.in embeds multiple JSON-LD scripts — the first is usually
        # a flat list of Event objects.
        events: list[RawEvent] = []
        for ld_script in soup.find_all("script", type="application/ld+json"):
            if not ld_script.string:
                continue
            try:
                ld_data = json.loads(ld_script.string)
            except json.JSONDecodeError:
                continue

            # Handle both flat list and ItemList formats
            items: list[dict] = []
            if isinstance(ld_data, list):
                items = ld_data
            elif isinstance(ld_data, dict):
                if ld_data.get("@type") == "ItemList":
                    for entry in ld_data.get("itemListElement", []):
                        item = entry.get("item", entry)
                        items.append(item)
                elif ld_data.get("@type") == "Event":
                    items = [ld_data]

            for item in items:
                if item.get("@type") != "Event":
                    continue
                try:
                    title = item.get("name", "").strip()
                    if not title:
                        continue

                    start_str = item.get("startDate")
                    if not start_str:
                        continue
                    start_date = parse_date(start_str)

                    location_obj = item.get("location", {})
                    venue = None
                    if isinstance(location_obj, dict):
                        venue = location_obj.get("name")
                    elif isinstance(location_obj, str):
                        venue = location_obj

                    description = item.get("description", "")
                    url = item.get("url")
                    category = _guess_category(title, description)

                    events.append(
                        RawEvent(
                            title=title,
                            date=start_date,
                            venue=venue,
                            location="Montreal",
                            category=category,
                            description=description[:500] if description else None,
                            source=self.source_name(),
                            source_url=url,
                        )
                    )
                except Exception as exc:
                    logger.debug("Skipping AllEvents event: %s", exc)
                    continue

        logger.info("AllEvents.in: scraped %d events", len(events))
        return events
