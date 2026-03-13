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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def _guess_category(title: str, description: str = "") -> str:
    """Guess event category from title and description."""
    text = f"{title} {description}".lower()
    
    if any(word in text for word in ["concert", "música", "music", "concierto", "festival", "band", "dj"]):
        return "music"
    elif any(word in text for word in ["food", "comida", "gastronómico", "restaurante", "cocina", "chef"]):
        return "food"
    elif any(word in text for word in ["arte", "art", "cultura", "museum", "teatro", "exhibition", "exposición"]):
        return "culture"
    elif any(word in text for word in ["night", "noche", "bar", "club", "party", "fiesta", "disco"]):
        return "nightlife"
    else:
        return "community"


class EventbriteCartagenaScraper(BaseScraper):
    """Scrapes events from Eventbrite's Cartagena search page via JSON-LD."""

    def source_name(self) -> str:
        return "eventbrite_cartagena"

    def scrape(self) -> list[RawEvent]:
        search_url = "https://www.eventbrite.com/d/colombia--cartagena/events/"
        
        try:
            resp = httpx.get(
                search_url,
                headers=HEADERS,
                timeout=15,
                follow_redirects=True,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Eventbrite Cartagena fetch failed: %s", exc)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract JSON-LD structured data
        ld_scripts = soup.find_all("script", type="application/ld+json")
        events: list[RawEvent] = []
        
        for ld_script in ld_scripts:
            if not ld_script or not ld_script.string:
                continue

            try:
                ld_data = json.loads(ld_script.string)
            except json.JSONDecodeError:
                continue

            # Handle different JSON-LD structures
            items = []
            if isinstance(ld_data, dict):
                if ld_data.get("@type") == "Event":
                    items = [ld_data]
                elif "itemListElement" in ld_data:
                    items = ld_data.get("itemListElement", [])
            elif isinstance(ld_data, list):
                items = ld_data

            for entry in items:
                item = entry.get("item", entry) if isinstance(entry, dict) and "item" in entry else entry
                
                if not isinstance(item, dict) or item.get("@type") != "Event":
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
                            location="Cartagena",
                            category=category,
                            description=description[:500] if description else None,
                            source=self.source_name(),
                            source_url=url,
                        )
                    )
                except Exception as exc:
                    logger.debug("Skipping Eventbrite event: %s", exc)
                    continue

        logger.info("Eventbrite Cartagena: scraped %d events", len(events))
        return events


class AllEventsCartagenaScraper(BaseScraper):
    """Scrapes events from AllEvents.in Cartagena page."""

    def source_name(self) -> str:
        return "allevents_cartagena"

    def scrape(self) -> list[RawEvent]:
        search_url = "https://allevents.in/cartagena"
        
        try:
            resp = httpx.get(
                search_url,
                headers=HEADERS,
                timeout=15,
                follow_redirects=True,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("AllEvents Cartagena fetch failed: %s", exc)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        events: list[RawEvent] = []

        # Try JSON-LD first
        ld_scripts = soup.find_all("script", type="application/ld+json")
        for ld_script in ld_scripts:
            if not ld_script or not ld_script.string:
                continue

            try:
                ld_data = json.loads(ld_script.string)
                if isinstance(ld_data, list):
                    items = ld_data
                elif isinstance(ld_data, dict) and ld_data.get("@type") == "Event":
                    items = [ld_data]
                else:
                    continue

                for item in items:
                    if not isinstance(item, dict) or item.get("@type") != "Event":
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
                                location="Cartagena",
                                category=category,
                                description=description[:500] if description else None,
                                source=self.source_name(),
                                source_url=url,
                            )
                        )
                    except Exception as exc:
                        logger.debug("Skipping AllEvents event: %s", exc)
                        continue

            except json.JSONDecodeError:
                continue

        # Fallback to HTML parsing if no JSON-LD events found
        if not events:
            event_cards = soup.find_all("div", class_=re.compile(r"event|card"))
            for card in event_cards[:20]:  # Limit to avoid too many requests
                try:
                    title_elem = card.find(["h1", "h2", "h3", "h4", "a"], class_=re.compile(r"title|name|event"))
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue

                    # Look for date information
                    date_elem = card.find(["time", "span", "div"], class_=re.compile(r"date|time"))
                    if not date_elem:
                        continue
                    
                    date_text = date_elem.get_text(strip=True)
                    if not date_text:
                        continue
                    
                    # Try to parse the date
                    try:
                        event_date = parse_date(date_text)
                    except:
                        continue

                    # Look for venue
                    venue_elem = card.find(["span", "div"], class_=re.compile(r"venue|location"))
                    venue = venue_elem.get_text(strip=True) if venue_elem else None

                    # Look for description
                    desc_elem = card.find(["p", "div"], class_=re.compile(r"desc|summary"))
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    # Look for URL
                    url_elem = card.find("a", href=True)
                    url = url_elem["href"] if url_elem else None

                    category = _guess_category(title, description)

                    events.append(
                        RawEvent(
                            title=title,
                            date=event_date,
                            venue=venue,
                            location="Cartagena",
                            category=category,
                            description=description[:500] if description else None,
                            source=self.source_name(),
                            source_url=url,
                        )
                    )
                except Exception as exc:
                    logger.debug("Skipping AllEvents card: %s", exc)
                    continue

        logger.info("AllEvents Cartagena: scraped %d events", len(events))
        return events


class TurismoCartagenaScraper(BaseScraper):
    """Scrapes events from Cartagena tourism/official websites."""

    def source_name(self) -> str:
        return "turismo_cartagena"

    def scrape(self) -> list[RawEvent]:
        urls = [
            "https://www.cartagenadeindias.travel/eventos",
            "https://www.cartagena.gov.co/eventos",
        ]
        
        events: list[RawEvent] = []
        
        for url in urls:
            try:
                resp = httpx.get(
                    url,
                    headers=HEADERS,
                    timeout=15,
                    follow_redirects=True,
                )
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                logger.warning("Tourism site fetch failed for %s: %s", url, exc)
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            # Look for event containers
            event_selectors = [
                "div[class*='event']",
                "article[class*='event']",
                "div[class*='evento']",
                "article[class*='evento']",
                ".event-item",
                ".evento-item",
                "[class*='calendar-event']",
            ]

            found_events = []
            for selector in event_selectors:
                found_events.extend(soup.select(selector))

            for event_elem in found_events[:15]:  # Limit results
                try:
                    # Find title
                    title_elem = event_elem.find(["h1", "h2", "h3", "h4", "h5"], class_=re.compile(r"title|name|evento"))
                    if not title_elem:
                        title_elem = event_elem.find(["h1", "h2", "h3", "h4", "h5"])
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue

                    # Find date
                    date_elem = event_elem.find(["time", "span", "div"], class_=re.compile(r"date|fecha|time"))
                    if not date_elem:
                        date_elem = event_elem.find("time")
                    if not date_elem:
                        continue

                    date_text = date_elem.get("datetime") or date_elem.get_text(strip=True)
                    if not date_text:
                        continue

                    try:
                        event_date = parse_date(date_text)
                    except:
                        continue

                    # Find venue
                    venue_elem = event_elem.find(["span", "div"], class_=re.compile(r"venue|lugar|location"))
                    venue = venue_elem.get_text(strip=True) if venue_elem else None

                    # Find description
                    desc_elem = event_elem.find(["p", "div"], class_=re.compile(r"desc|summary|content"))
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    # Find URL
                    url_elem = event_elem.find("a", href=True)
                    event_url = None
                    if url_elem:
                        href = url_elem["href"]
                        if href.startswith("http"):
                            event_url = href
                        elif href.startswith("/"):
                            event_url = f"{url.split('/')[0]}//{url.split('/')[2]}{href}"

                    category = _guess_category(title, description)

                    events.append(
                        RawEvent(
                            title=title,
                            date=event_date,
                            venue=venue,
                            location="Cartagena",
                            category=category,
                            description=description[:500] if description else None,
                            source=self.source_name(),
                            source_url=event_url,
                        )
                    )
                except Exception as exc:
                    logger.debug("Skipping tourism event: %s", exc)
                    continue

        logger.info("Tourism Cartagena: scraped %d events", len(events))
        return events