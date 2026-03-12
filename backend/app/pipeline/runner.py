"""Daily batch pipeline runner.

Runs all scrapers, deduplicates, ranks, and persists results to SQLite.
Can be run as: python -m app.pipeline.runner
"""

from __future__ import annotations

import asyncio
import datetime
import sys

from app.db import SessionLocal, create_tables
from app.models import EventRow, RawEvent
from app.pipeline.dedup import deduplicate
from app.pipeline.ranker import rank_clusters
from app.scrapers.allevents_mtl import AllEventsMtlScraper
from app.scrapers.eventbrite_mtl import EventbriteMtlScraper
from app.scrapers.montreal_opendata import MontrealOpenDataScraper
from app.services.enrichment import enrich_events, _fallback_enrich

ALL_SCRAPERS = [
    # Montreal — 3 real sources
    EventbriteMtlScraper(),
    AllEventsMtlScraper(),
    MontrealOpenDataScraper(),
]


async def run_pipeline(use_llm_enrichment: bool = False):
    print(f"[{datetime.datetime.now().isoformat()}] Starting scraping pipeline...")

    # Step 1: Scrape all sources
    all_events: list[RawEvent] = []
    for scraper in ALL_SCRAPERS:
        try:
            events = scraper.scrape()
            print(f"  ✅ {scraper.source_name()}: {len(events)} events")
            all_events.extend(events)
        except Exception as e:
            print(f"  ❌ {scraper.source_name()}: {e}")

    print(f"\n  Total raw events: {len(all_events)}")

    # Step 2: Deduplicate
    clusters = deduplicate(all_events)
    print(f"  After dedup: {len(clusters)} unique events")

    # Step 3: Rank
    ranked = rank_clusters(clusters)

    # Step 4: Enrich with metadata
    enrichment_batch = [
        {
            "title": c["canonical"].title,
            "category": c["canonical"].category,
            "description": c["canonical"].description,
        }
        for c in ranked
    ]

    if use_llm_enrichment:
        print("  🧠 Enriching with LLM...")
        enriched = await enrich_events(enrichment_batch)
    else:
        # Use fast rule-based enrichment
        for ev in enrichment_batch:
            fallback = _fallback_enrich(ev.get("title", ""), ev.get("category"))
            ev.update(fallback)
        enriched = enrichment_batch

    # Step 5: Persist to DB
    create_tables()
    db = SessionLocal()
    try:
        # Clear previous data (full refresh for MVP)
        db.query(EventRow).delete()

        for i, cluster in enumerate(ranked):
            ev = cluster["canonical"]
            meta = enriched[i] if i < len(enriched) else {}
            row = EventRow(
                title=ev.title,
                date=ev.date,
                venue=ev.venue,
                location=ev.location,
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

        db.commit()
        print(f"\n  💾 Persisted {len(ranked)} events to database")
    finally:
        db.close()

    # Summary
    print("\n  📊 Top events:")
    for i, cluster in enumerate(ranked[:5], 1):
        ev = cluster["canonical"]
        meta = enriched[i - 1] if i - 1 < len(enriched) else {}
        emoji = meta.get("emoji", "")
        print(f"    {i}. {emoji} {ev.title} ({cluster['source_count']} sources, score={cluster['score']:.2f})")

    print(f"\n[{datetime.datetime.now().isoformat()}] Pipeline complete!")


if __name__ == "__main__":
    use_llm = "--enrich" in sys.argv
    asyncio.run(run_pipeline(use_llm_enrichment=use_llm))
