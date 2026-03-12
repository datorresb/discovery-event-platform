"""Montreal Open Data (Données ouvertes) scraper for public events.

Fetches events from the City of Montreal's public CKAN API.
Dataset: "Événements publics" — civic, cultural, and community events
published by the city and its boroughs.

API docs: https://donnees.montreal.ca
"""

from __future__ import annotations

import datetime
import logging

import httpx
from dateutil.parser import parse as parse_date

from app.models import RawEvent
from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# CKAN datastore search endpoint for the "Événements publics" resource
API_URL = (
    "https://donnees.montreal.ca/api/3/action/datastore_search"
    "?resource_id=6decf611-6f11-4f34-bb36-324d804c9bad"
    "&limit=100"
    "&sort=date_debut desc"
)

_TYPE_MAP = {
    "spectacle": "culture",
    "concert": "music",
    "festival": "culture",
    "exposition": "culture",
    "atelier": "community",
    "conférence": "community",
    "séance d'information": "community",
    "animation": "culture",
    "activité sportive": "community",
    "marché": "food",
    "fête": "culture",
    "journée portes ouvertes": "community",
}


def _map_category(type_evenement: str | None) -> str | None:
    """Map French event type to our normalized category."""
    if not type_evenement:
        return None
    key = type_evenement.strip().lower()
    for french, cat in _TYPE_MAP.items():
        if french in key:
            return cat
    return "community"  # default for civic events


class MontrealOpenDataScraper(BaseScraper):
    """Scrapes real public events from the City of Montreal's Open Data API."""

    def source_name(self) -> str:
        return "montreal_opendata"

    def scrape(self) -> list[RawEvent]:
        try:
            resp = httpx.get(API_URL, timeout=20.0)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Montreal Open Data fetch failed: %s", exc)
            return []

        try:
            data = resp.json()
        except Exception:
            logger.warning("Montreal Open Data: invalid JSON response")
            return []

        records = data.get("result", {}).get("records", [])
        if not records:
            logger.warning("Montreal Open Data: no records returned")
            return []

        events: list[RawEvent] = []
        for rec in records:
            try:
                title = rec.get("titre", "").strip()
                if not title:
                    continue

                date_str = rec.get("date_debut")
                if not date_str:
                    continue
                event_date = parse_date(date_str)

                # Build venue from available address fields
                venue = rec.get("titre_adresse") or rec.get("emplacement")
                description = rec.get("description", "")
                url = rec.get("url_fiche")
                category = _map_category(rec.get("type_evenement"))

                events.append(
                    RawEvent(
                        title=title,
                        date=event_date,
                        venue=venue,
                        location="Montreal",
                        category=category,
                        description=description[:500] if description else None,
                        source=self.source_name(),
                        source_url=url,
                    )
                )
            except Exception as exc:
                logger.debug("Skipping Montreal Open Data event: %s", exc)
                continue

        logger.info("Montreal Open Data: scraped %d events", len(events))
        return events
