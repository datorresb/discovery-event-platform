# Discovery Event Platform

> Real-time multi-source event aggregation with AI-powered city expansion.
> Scrapes, deduplicates, ranks, and enriches events from 3+ live sources per city.

https://github.com/datorresb/discovery-event-platform/raw/main/docs/discovery-demo.mp4

---

## Quickstart (Codespace)

The entire platform runs in **GitHub Codespaces** — zero local setup.
Three services, one Codespace, you're live.

### 1. Open your Codespace

Click **Code → Codespaces → Create codespace on main**.

### 2. Authenticate GitHub

The Copilot LLM proxy needs your GitHub credentials. Run once:

```bash
unset GITHUB_TOKEN
gh auth login -h github.com -p https -w
```

### 3. Start the 3 services

```bash
# Service 1 — Backend API (port 8000)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Service 2 — Frontend (port 5173)
cd ../frontend
npm install
npm run dev &

# Service 3 — Copilot LLM Proxy (port 8080)
cd ../backend
python copilot_proxy.py &
```

Verify all three are up:

```bash
curl -s -o /dev/null -w "Backend: %{http_code}\n" http://localhost:8000/api/cities
curl -s -o /dev/null -w "Frontend: %{http_code}\n" http://localhost:5173
curl -s -o /dev/null -w "LLM Proxy: %{http_code}\n" http://localhost:8080
```

### 4. Populate with real events

```bash
cd backend
python -m app.pipeline.runner
```

Scrapes **233+ real events** from 3 live Montreal sources.

### 5. Open the app

Go to the **Ports** tab and open port **5173**.

---

## Architecture

```
frontend/                → React 19 + TypeScript + Vite        (port 5173)
backend/                 → Python + FastAPI + SQLite            (port 8000)
  copilot_proxy.py       → Lightweight Copilot LLM proxy       (port 8080)
  app/scrapers/          → 3 real HTTP scrapers (Eventbrite, AllEvents, Montreal Open Data)
  app/scrapers/generated/→ AI-generated scrapers per city
  app/pipeline/          → Dedup + ranking pipeline
  app/services/          → LLM enrichment + scraper code generation
```

### The 3 Services

| # | Service | Port | What it does |
|---|---------|------|--------------|
| 1 | **Backend API** | 8000 | FastAPI server — events CRUD, scraping pipeline, city generation |
| 2 | **Frontend** | 5173 | React 19 SPA — event grid, filters, city selector, "Add City" form |
| 3 | **Copilot LLM Proxy** | 8080 | Forwards `/v1/chat/completions` to GitHub Copilot API using `gh auth` tokens. Zero dependencies — pure Python stdlib. Required for AI city generation and event enrichment. |

## Real Scrapers

| Source | Type | Events |
|--------|------|--------|
| **Eventbrite** | JSON-LD from search page | ~70 |
| **AllEvents.in** | JSON-LD event data | ~65 |
| **Montreal Open Data** | City CKAN API | ~100 |

## AI City Generator

Type any city name in the UI and the platform will:

1. Ask the LLM to **generate real scraper code** (httpx + BeautifulSoup)
2. **Execute** the generated scrapers to fetch live events
3. **Deduplicate & rank** events across sources
4. **Enrich** with emoji, color, and vibe via LLM
5. Display the city as "**City / Country**" format (e.g., Bogotá / Colombia)

```bash
# Or via API
curl -X POST http://localhost:8000/api/cities/generate \
  -H "Content-Type: application/json" \
  -d '{"city": "Tokyo"}'
```

Generated scrapers are saved in `backend/app/scrapers/generated/`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/events` | List events (`category`, `location`, `sort`, `date_from`, `date_to`) |
| `GET` | `/api/events/top` | Top-ranked events this week |
| `GET` | `/api/cities` | List all cities with events |
| `POST` | `/api/cities/generate` | Generate events for a new city via AI |

## Stack

- **Frontend**: React 19, TypeScript, Vite
- **Backend**: Python 3.12, FastAPI, SQLAlchemy, SQLite
- **Scraping**: httpx, BeautifulSoup4, dateutil
- **AI**: GitHub Copilot API (Claude Sonnet 4), code generation + enrichment
- **Dedup**: thefuzz (fuzzy string matching)

## License

MIT
