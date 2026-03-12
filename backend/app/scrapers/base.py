from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import RawEvent


class BaseScraper(ABC):
    """Interface that all event scrapers must implement."""

    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier for this source (e.g. 'eventbrite')."""
        ...

    @abstractmethod
    def scrape(self) -> list[RawEvent]:
        """Scrape events and return normalized RawEvent list."""
        ...
