import datetime
import json
import logging
import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date

from app.models import RawEvent
from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def _normalize_location(loc: str) -> str:
    """Normalize location string to 'bogota'."""
    if loc and "bogot" in loc.lower():
        return "bogota"
    return loc


def _guess_category(title: str, description: str = "") -> str:
    """Guess event category from title and description."""
    text = f"{title} {description}".lower()
    
    if any(word in text for word in ["concert", "music", "band", "dj", "festival", "show"]):
        return "music"
    if any(word in text for word in ["bar", "club", "night", "party", "drinks"]):
        return "nightlife"
    if any(word in text for word in ["food", "restaurant", "cooking", "dinner", "culinary", "gastro"]):
        return "food"
    if any(word in text for word in ["community", "workshop", "meetup", "networking", "volunteer"]):
        return "community"
    if any(word in text for word in ["art", "museum", "gallery", "theater", "theatre", "culture", "exhibition"]):
        return "culture"
    
    return "culture"


class EventbriteBogotaScraper(BaseScraper):
    """Scrapes real events from Eventbrite's Bogota search page via JSON-LD."""

    def source_name(self) -> str:
        return "eventbrite_bogota"

    def scrape(self) -> list[RawEvent]:
        url = "https://www.eventbrite.com/d/colombia--bogota/events/"
        
        try:
            resp = httpx.get(
                url,
                headers=HEADERS,
                timeout=15.0,
                follow_redirects=True,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Eventbrite Bogota fetch failed: %s", exc)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        ld_script = soup.find("script", type="application/ld+json")
        if not ld_script or not ld_script.string:
            logger.warning("No JSON-LD found on Eventbrite Bogota page")
            return []

        try:
            ld_data = json.loads(ld_script.string)
        except json.JSONDecodeError:
            logger.warning("Failed to parse Eventbrite Bogota JSON-LD")
            return []

        items = ld_data.get("itemListElement", [])
        if not items:
            logger.warning("No events in Eventbrite Bogota JSON-LD")
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

                start_str = item.get("startDate")
                if not start_str:
                    continue
                start_date = parse_date(start_str)

                location_obj = item.get("location", {})
                venue = location_obj.get("name")
                
                description = item.get("description", "")
                url = item.get("url")
                category = _guess_category(title, description)

                events.append(
                    RawEvent(
                        title=title,
                        date=start_date,
                        venue=venue,
                        location="bogota",
                        category=category,
                        description=description[:500] if description else None,
                        source=self.source_name(),
                        source_url=url,
                    )
                )
            except Exception as exc:
                logger.debug("Skipping Eventbrite Bogota event: %s", exc)
                continue

        logger.info("Eventbrite Bogota: scraped %d events", len(events))
        return events


class AllEventsBogotaScraper(BaseScraper):
    """Scrapes real events from AllEvents.in Bogota page via JSON-LD."""

    def source_name(self) -> str:
        return "allevents_bogota"

    def scrape(self) -> list[RawEvent]:
        url = "https://allevents.in/bogota"
        
        try:
            resp = httpx.get(
                url,
                headers=HEADERS,
                timeout=15.0,
                follow_redirects=True,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("AllEvents Bogota fetch failed: %s", exc)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        ld_scripts = soup.find_all("script", type="application/ld+json")
        
        events: list[RawEvent] = []
        
        for ld_script in ld_scripts:
            if not ld_script.string:
                continue
                
            try:
                ld_data = json.loads(ld_script.string)
            except json.JSONDecodeError:
                continue

            if isinstance(ld_data, dict):
                ld_data = [ld_data]
            
            if not isinstance(ld_data, list):
                continue

            for item in ld_data:
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

                    description = item.get("description", "")
                    url = item.get("url")
                    category = _guess_category(title, description)

                    events.append(
                        RawEvent(
                            title=title,
                            date=start_date,
                            venue=venue,
                            location="bogota",
                            category=category,
                            description=description[:500] if description else None,
                            source=self.source_name(),
                            source_url=url,
                        )
                    )
                except Exception as exc:
                    logger.debug("Skipping AllEvents Bogota event: %s", exc)
                    continue

        logger.info("AllEvents Bogota: scraped %d events", len(events))
        return events


class TuBoletaBogotaScraper(BaseScraper):
    """Scrapes real events from TuBoleta (Colombian ticketing platform) for Bogota."""

    def source_name(self) -> str:
        return "tuboleta_bogota"

    def scrape(self) -> list[RawEvent]:
        url = "https://www.tuboleta.com/eventos/en/colombia/bogota/"
        
        try:
            resp = httpx.get(
                url,
                headers=HEADERS,
                timeout=15.0,
                follow_redirects=True,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("TuBoleta Bogota fetch failed: %s", exc)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        
        events: list[RawEvent] = []
        
        event_cards = soup.find_all("div", class_=re.compile(r"event|item|card"))
        
        if not event_cards:
            event_cards = soup.find_all("article")
        
        if not event_cards:
            event_cards = soup.find_all("a", href=re.compile(r"/evento/|/event/"))

        for card in event_cards[:50]:
            try:
                title_elem = card.find(["h2", "h3", "h4", "h5"])
                if not title_elem:
                    title_elem = card.find("a", class_=re.compile(r"title|name"))
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                if not title or len(title) < 3:
                    continue

                date_elem = card.find(class_=re.compile(r"date|time|fecha"))
                if not date_elem:
                    date_elem = card.find("time")
                
                if not date_elem:
                    continue
                
                date_str = date_elem.get("datetime") or date_elem.get_text(strip=True)
                if not date_str:
                    continue
                
                try:
                    event_date = parse_date(date_str)
                except Exception:
                    continue

                venue_elem = card.find(class_=re.compile(r"venue|location|lugar"))
                venue = venue_elem.get_text(strip=True) if venue_elem else None

                desc_elem = card.find(class_=re.compile(r"description|desc"))
                description = desc_elem.get_text(strip=True) if desc_elem else ""

                link_elem = card if card.name == "a" else card.find("a")
                source_url = None
                if link_elem and link_elem.get("href"):
                    href = link_elem.get("href")
                    if href.startswith("/"):
                        source_url = f"https://www.tuboleta.com{href}"
                    elif href.startswith("http"):
                        source_url = href

                category = _guess_category(title, description)

                events.append(
                    RawEvent(
                        title=title,
                        date=event_date,
                        venue=venue,
                        location="bogota",
                        category=category,
                        description=description[:500] if description else None,
                        source=self.source_name(),
                        source_url=source_url,
                    )
                )
            except Exception as exc:
                logger.debug("Skipping TuBoleta event: %s", exc)
                continue

        logger.info("TuBoleta Bogota: scraped %d events", len(events))
        return events