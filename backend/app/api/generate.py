"""API endpoints for generating events for new cities via LLM."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import distinct
from sqlalchemy.orm import Session

from app.db import get_db, create_tables
from app.models import EventOut, EventRow, RawEvent
from app.pipeline.dedup import deduplicate
from app.pipeline.ranker import rank_clusters
from app.services.enrichment import enrich_events
from app.services.llm import generate_events_for_city

router = APIRouter()

# ── City display formatting ─────────────────────────────────────────
# Maps a lowercase key → pretty "City / Country" display name.
# Add entries here as new cities are generated.
_CITY_DISPLAY: dict[str, str] = {
    "montreal": "Montreal / Canada",
    "bogota": "Bogotá / Colombia",
    "bogotá": "Bogotá / Colombia",
    "mexico city": "Mexico City / Mexico",
    "ciudad de mexico": "Ciudad de México / Mexico",
    "buenos aires": "Buenos Aires / Argentina",
    "lima": "Lima / Peru",
    "santiago": "Santiago / Chile",
    "sao paulo": "São Paulo / Brazil",
    "são paulo": "São Paulo / Brazil",
    "rio de janeiro": "Rio de Janeiro / Brazil",
    "medellin": "Medellín / Colombia",
    "medellín": "Medellín / Colombia",
    "toronto": "Toronto / Canada",
    "new york": "New York / USA",
    "london": "London / UK",
    "paris": "Paris / France",
    "barcelona": "Barcelona / Spain",
    "berlin": "Berlin / Germany",
    "tokyo": "Tokyo / Japan",
}


def format_city(raw: str) -> str:
    """Return a pretty 'City / Country' string, or title-case the input."""
    key = raw.strip().lower()
    if key in _CITY_DISPLAY:
        return _CITY_DISPLAY[key]
    # Fallback: title-case what the user typed
    return raw.strip().title()


class CityRequest(BaseModel):
    city: str

    @field_validator("city")
    @classmethod
    def validate_city(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) > 100:
            raise ValueError("City name must be 1-100 characters")
        return v


@router.post("/cities/generate", response_model=list[EventOut])
async def generate_city(request: CityRequest, db: Session = Depends(get_db)):
    """Generate events for a new city using the Copilot Proxy LLM."""
    display_name = format_city(request.city)

    # Check if city already has events (match both raw input and display name)
    existing = (
        db.query(EventRow)
        .filter(
            (EventRow.location == request.city)
            | (EventRow.location == display_name)
        )
        .count()
    )
    if existing > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Events for '{display_name}' already exist. Use the events API to view them.",
        )

    try:
        raw_events = await generate_events_for_city(request.city)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM generation failed: {e}")

    if not raw_events:
        raise HTTPException(status_code=502, detail="LLM returned no events")

    # Dedup and rank (within this city's events)
    clusters = deduplicate(raw_events)
    ranked = rank_clusters(clusters)

    # Enrich with emoji/color/vibe via LLM
    enrichment_batch = [
        {
            "title": c["canonical"].title,
            "category": c["canonical"].category,
            "description": c["canonical"].description,
        }
        for c in ranked
    ]
    enriched = await enrich_events(enrichment_batch)

    # Persist
    create_tables()
    new_rows = []
    for i, cluster in enumerate(ranked):
        ev = cluster["canonical"]
        meta = enriched[i] if i < len(enriched) else {}
        row = EventRow(
            title=ev.title,
            date=ev.date,
            venue=ev.venue,
            location=display_name,
            category=ev.category,
            description=ev.description,
            source=",".join(sorted(cluster["sources"])),
            source_url=ev.source_url,
            source_count=cluster["source_count"],
            score=cluster["score"],
            emoji=meta.get("emoji"),
            color_tag=meta.get("color_tag"),
            vibe=meta.get("vibe"),
        )
        db.add(row)
        new_rows.append(row)

    db.commit()
    for row in new_rows:
        db.refresh(row)

    return new_rows


@router.get("/cities", response_model=list[str])
def list_cities(db: Session = Depends(get_db)):
    """Return all cities that have events in the database."""
    rows = db.query(distinct(EventRow.location)).order_by(EventRow.location).all()
    return [row[0] for row in rows]
