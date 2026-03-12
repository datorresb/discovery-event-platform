"""Fuzzy deduplication of events across sources.

Uses title + date + venue fuzzy matching to identify the same event
mentioned by different sources.
"""

from __future__ import annotations

from thefuzz import fuzz

from app.models import RawEvent


def _normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def events_match(a: RawEvent, b: RawEvent, threshold: int = 75) -> bool:
    """Return True if two RawEvents likely refer to the same real-world event."""
    # Must be on the same date
    if a.date.date() != b.date.date():
        return False

    title_score = fuzz.token_sort_ratio(_normalize(a.title), _normalize(b.title))
    if title_score >= threshold:
        return True

    # If venues match and titles are somewhat similar, still a match
    if a.venue and b.venue:
        venue_score = fuzz.token_sort_ratio(_normalize(a.venue), _normalize(b.venue))
        if venue_score >= 80 and title_score >= 50:
            return True

    return False


def deduplicate(raw_events: list[RawEvent]) -> list[dict]:
    """Group raw events into deduplicated clusters.

    Returns a list of dicts with:
      - "canonical": the RawEvent with the longest description (used as display)
      - "sources": set of unique source names
      - "source_count": number of distinct sources
    """
    clusters: list[dict] = []

    for event in raw_events:
        matched = False
        for cluster in clusters:
            if events_match(event, cluster["canonical"]):
                cluster["sources"].add(event.source)
                cluster["source_count"] = len(cluster["sources"])
                # Keep the version with the longest description
                if event.description and (
                    not cluster["canonical"].description
                    or len(event.description) > len(cluster["canonical"].description)
                ):
                    cluster["canonical"] = event
                matched = True
                break

        if not matched:
            clusters.append(
                {
                    "canonical": event,
                    "sources": {event.source},
                    "source_count": 1,
                }
            )

    return clusters
