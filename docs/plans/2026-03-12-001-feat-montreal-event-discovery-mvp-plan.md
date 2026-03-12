---
title: "feat: Montreal Event Discovery MVP"
type: feat
status: active
date: 2026-03-12
origin: docs/prds/2026-03-12-global-events-aggregation-discovery-platform-prd.md
---

# feat: Montreal Event Discovery MVP

Single-city prototype of the Global Events Aggregation & Discovery Platform. Scrape, normalize, rank, and display events from diverse Montreal sources — mainstream and underground — in a React web app powered by a Python FastAPI backend.

**Architecture:** Modular monorepo — `backend/` (Python/FastAPI) + `frontend/` (React/TypeScript/Vite).

**Key decisions from brainstorm session:**
- 🎯 **Scope:** Single-city prototype (Montreal)
- ⚛️ **Frontend:** React + TypeScript (Vite)
- 🐍 **Backend:** Python + FastAPI
- 🔧 **Ingestion:** Hybrid — APIs where available, HTML scraping, LLM extraction for unstructured sources
- 📊 **Ranking:** Cross-source frequency (event mentioned by N sources → higher rank)
- ⏰ **Freshness:** Daily batch job
- 🏗️ **Architecture:** Modular monorepo

## Acceptance Criteria

- [x] **Monorepo structure** — `backend/` (FastAPI) and `frontend/` (React/Vite) with clear separation
- [x] **Event schema** — Normalized model: title, date/time, venue, location, genre/category, source, source_url, description
- [x] **3-5 Montreal scrapers** — At least one per source type: mainstream platform, venue website, specialized platform (e.g., RA-style), newsletter/blog
- [x] **Scraper plugin system** — Each scraper is a Python class implementing a common interface; easy to add new ones
- [x] **Cross-source deduplication** — Match same event across sources using title + date + venue fuzzy matching
- [x] **Cross-source frequency ranking** — Events mentioned by more sources rank higher
- [x] **REST API** — `GET /api/events` with filters: date range, category, sort order
- [x] **React frontend** — City view with event cards, category filter, date filter, "Top Events This Week" section
- [x] **Daily batch pipeline** — Script/task that runs all scrapers, normalizes, deduplicates, and stores results
- [x] **Ethical scraping** — Respect `robots.txt`, rate limiting, proper User-Agent headers
- [x] **SQLite storage** — Simple local DB for MVP (no external DB dependency)

## Context

- **PRD:** [docs/prds/2026-03-12-global-events-aggregation-discovery-platform-prd.md](/workspaces/ATV-StarterKit/docs/prds/2026-03-12-global-events-aggregation-discovery-platform-prd.md)
- **Out of scope (per PRD):** Ticket purchasing, social features, user-generated events, monetization
- **Future evolution:** Multi-city expansion, personalization/recommendations, source credibility weighting

## MVP

### Monorepo structure

```
discovery-event-platform/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entrypoint
│   │   ├── models.py            # SQLAlchemy/Pydantic event schema
│   │   ├── api/
│   │   │   └── events.py        # GET /api/events endpoint
│   │   ├── scrapers/
│   │   │   ├── base.py          # Abstract scraper interface
│   │   │   ├── eventbrite.py    # Mainstream platform scraper
│   │   │   ├── venue_mtl.py     # Montreal venue websites
│   │   │   ├── ra_style.py      # Specialized music platform
│   │   │   └── newsletter.py   # Newsletter/blog LLM extractor
│   │   ├── pipeline/
│   │   │   ├── runner.py        # Daily batch orchestrator
│   │   │   ├── dedup.py         # Fuzzy deduplication logic
│   │   │   └── ranker.py        # Cross-source frequency scorer
│   │   └── db.py                # SQLite setup
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── EventCard.tsx
│   │   │   ├── EventList.tsx
│   │   │   ├── FilterBar.tsx
│   │   │   └── TopEvents.tsx
│   │   ├── api/
│   │   │   └── events.ts        # API client
│   │   └── types/
│   │       └── event.ts         # TypeScript event type
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
└── README.md
```

### backend/app/scrapers/base.py

```python
from abc import ABC, abstractmethod
from app.models import RawEvent

class BaseScraper(ABC):
    @abstractmethod
    def source_name(self) -> str: ...

    @abstractmethod
    def scrape(self) -> list[RawEvent]: ...
```

### backend/app/pipeline/ranker.py

```python
def rank_events(events: list[NormalizedEvent]) -> list[RankedEvent]:
    """Score by cross-source frequency: more sources = higher rank."""
    # Group by fuzzy-matched event identity
    # Count distinct sources per event
    # Sort descending by source count
```

### frontend/src/components/EventCard.tsx

```tsx
interface EventCardProps {
  title: string;
  date: string;
  venue: string;
  category: string;
  sourceCount: number;
}
```

## Sources

- **PRD:** docs/prds/2026-03-12-global-events-aggregation-discovery-platform-prd.md
- **Brainstorm decisions:** Captured in-session (Montreal, React+TS, Python, hybrid ingestion, cross-source frequency ranking, daily batch, modular monorepo)
