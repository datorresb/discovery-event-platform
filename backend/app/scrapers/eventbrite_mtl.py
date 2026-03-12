"""Eventbrite scraper for Montreal events.

Fetches the Eventbrite Montreal search page and extracts event data
from the embedded JSON-LD (schema.org) structured data.
"""

from __future__ import annotations

import datetime
import json
import logging
import unicodedata

import httpx
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date

from app.models import RawEvent
from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.eventbrite.com/d/canada--montreal/events/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Map Eventbrite's free-text titles to our categories via keyword matching
_CATEGORY_KEYWORDS = {
    "music": ["concert", "music", "dj", "band", "jazz", "rock", "hip hop", "rap",
              "techno", "house", "rave", "festival", "live", "party", "fete", "fête"],
    "food": ["food", "wine", "beer", "brunch", "dinner", "tasting", "culinary",
             "cook", "restaurant", "market", "marché"],
    "culture": ["art", "museum", "gallery", "theatre", "theater", "film", "cinema",
                "exhibit", "heritage", "culture", "literary", "book", "dance"],
    "nightlife": ["club", "nightlife", "afterhours", "after-hours", "warehouse",
                  "lounge", "bar crawl"],
    "community": ["community", "meetup", "workshop", "class", "networking",
                  "volunteer", "charity", "run", "walk", "yoga", "wellness"],
}


def _normalize_location(raw: str) -> str:
    """Strip accents and normalize city names (Montréal → Montreal)."""
    nfkd = unicodedata.normalize("NFKD", raw)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _guess_category(title: str, description: str | None) -> str | None:
    """Guess event category from title and description text."""
    text = (title + " " + (description or "")).lower()
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return cat
    return None


class EventbriteMtlScraper(BaseScraper):
    """Scrapes real events from Eventbrite's Montreal search page via JSON-LD."""

    def source_name(self) -> str:
        return "eventbrite"

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
            logger.warning("Eventbrite fetch failed: %s", exc)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract JSON-LD structured data
        ld_script = soup.find("script", type="application/ld+json")
        if not ld_script or not ld_script.string:
            logger.warning("No JSON-LD found on Eventbrite page")
            return []

        try:
            ld_data = json.loads(ld_script.string)
        except json.JSONDecodeError:
            logger.warning("Failed to parse Eventbrite JSON-LD")
            return []

        items = ld_data.get("itemListElement", [])
        if not items:
            logger.warning("No events in Eventbrite JSON-LD")
            return []

        events: list[RawEvent] = []
        for entry in items:
            item = entry.get("item", entry)
            if item.get("@type") != "Event":
                continue

            try:
                title = item.get("name", "").strip()
                if not title:
                    continue

                # Parse date
                start_str = item.get("startDate")
                if not start_str:
                    continue
                start_date = parse_date(start_str)

                # Venue / location
                location_obj = item.get("location", {})
                venue = location_obj.get("name")
                address_obj = location_obj.get("address", {})
                locality = address_obj.get("addressLocality", "Montreal")
                # Normalize accented city names (Montréal → Montreal)
                location_normalized = _normalize_location(locality) if locality else "Montreal"

                description = item.get("description", "")
                url = item.get("url")
                category = _guess_category(title, description)

                events.append(
                    RawEvent(
                        title=title,
                        date=start_date,
                        venue=venue,
                        location=location_normalized,
                        category=category,
                        description=description[:500] if description else None,
                        source=self.source_name(),
                        source_url=url,
                    )
                )
            except Exception as exc:
                logger.debug("Skipping Eventbrite event: %s", exc)
                continue

        logger.info("Eventbrite: scraped %d events", len(events))
        return events
