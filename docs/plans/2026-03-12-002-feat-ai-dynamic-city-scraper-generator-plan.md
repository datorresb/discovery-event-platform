---
title: "feat: AI-Powered Dynamic City Scraper Generator"
type: feat
status: completed
date: 2026-03-12
origin: docs/brainstorms/2026-03-12-copilot-extension-scraper-generator-brainstorm.md
---

# feat: AI-Powered Dynamic City Scraper Generator

## Overview

Add an "Add City" feature to the Discovery Event Platform UI. Users type any city name, the backend calls the **Copilot Proxy LLM** (running at `localhost:8080`) to generate realistic event data for that city, persists it to the database, and immediately displays results in the frontend — all on the fly, no pre-built scrapers needed.

This evolves the brainstorm's original Copilot Extension concept into a **user-facing web feature** powered by the same LLM proxy. (see brainstorm: docs/brainstorms/2026-03-12-copilot-extension-scraper-generator-brainstorm.md)

## Proposed Solution

### Backend: New `/api/cities/generate` endpoint

1. Accepts a city name via POST
2. Calls the Copilot Proxy LLM (`http://localhost:8080/v1/chat/completions`) with a prompt that includes the `RawEvent` schema and instructions to generate 8-12 realistic events for that city
3. Parses the LLM JSON response into `RawEvent` objects
4. Runs dedup + ranking against existing events
5. Persists to SQLite
6. Returns the generated events
7. Adds the city to a `cities` list for the frontend dropdown

### Frontend: "Add City" UI

1. Replace hardcoded `CITIES` array with a dynamic list fetched from the API
2. Add an "Add City" input + button in the header or filter bar
3. Show loading state while the LLM generates events
4. Auto-select the new city after generation
5. Refresh events list

## Acceptance Criteria

- [x] `POST /api/cities/generate` endpoint accepts `{"city": "Tokyo"}` and returns generated events
- [x] LLM prompt produces structured JSON with 8-12 realistic events per city
- [x] Generated events follow the `RawEvent` schema (title, date, venue, location, category, description, source, source_url)
- [x] Events are deduplicated and ranked before persisting
- [x] `GET /api/cities` endpoint returns all available cities from the DB
- [x] Frontend "Add City" input with submit button
- [x] Frontend city dropdown dynamically populated from `/api/cities`
- [x] Loading spinner/state while LLM generates events
- [x] New city auto-selected after generation
- [x] Error handling for LLM failures (timeout, malformed response)

## MVP

### backend/app/api/generate.py

```python
@router.post("/cities/generate")
async def generate_city_events(request: CityRequest):
    # 1. Call Copilot Proxy LLM with city name + RawEvent schema
    # 2. Parse JSON response into RawEvent list
    # 3. Run dedup + rank pipeline on new + existing events
    # 4. Persist to DB
    # 5. Return generated events
```

### backend/app/services/llm.py

```python
async def generate_events_for_city(city: str) -> list[RawEvent]:
    # Call http://localhost:8080/v1/chat/completions
    # Model: claude-sonnet-4
    # Prompt: generate realistic events for {city}
    # Parse structured JSON response
```

### frontend/src/components/AddCityForm.tsx

```tsx
// Text input + "🌍 Discover" button
// POST /api/cities/generate with city name
// Show loading state, then refresh
```

### frontend/src/api/events.ts

```typescript
export async function generateCity(city: string): Promise<Event[]>
export async function fetchCities(): Promise<string[]>
```

## Sources

- **Origin brainstorm:** docs/brainstorms/2026-03-12-copilot-extension-scraper-generator-brainstorm.md
- **Copilot Proxy:** ClaudeCode-Copilot-Proxy at localhost:8080 (OpenAI-compatible API)
- **Available models:** claude-sonnet-4, claude-sonnet-4.6, claude-opus-4.5, gpt-4o
