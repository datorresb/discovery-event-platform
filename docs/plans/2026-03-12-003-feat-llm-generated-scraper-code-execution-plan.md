---
title: "feat: LLM-Generated Scraper Code Execution"
type: feat
status: completed
date: 2026-03-12
origin: docs/brainstorms/2026-03-12-copilot-extension-scraper-generator-brainstorm.md
---

# feat: LLM-Generated Scraper Code Execution

## Overview

Replace the current "LLM generates fake events" approach with "LLM generates real scraper Python code".

When a user types a city name:
1. The LLM generates a **Python scraper class** (like `dc.py`) that implements `BaseScraper`
2. The system **dynamically executes** the generated scraper code
3. The scraper produces `RawEvent` objects from its `scrape()` method
4. Events go through the existing dedup → rank → persist pipeline

This is fundamentally different from the current approach: the LLM writes **code**, not data. The code contains structured event data that follows real patterns (real venue names, dates, categories) — just like the handwritten Montreal and DC scrapers.

(see brainstorm: docs/brainstorms/2026-03-12-copilot-extension-scraper-generator-brainstorm.md — key decision: "Template-driven: The extension reads the existing BaseScraper interface and a sample scraper to maintain code consistency")

## Proposed Solution

### `app/services/llm.py` — Replace current approach

**Current:** Prompt asks for JSON event data → parse JSON → create RawEvents
**New:** Prompt asks for Python scraper code → dynamic exec → run `scrape()` → get RawEvents

The prompt will include:
- The `BaseScraper` abstract class code
- The `RawEvent` model definition
- A sample scraper (`dc.py`) as a template
- The city name

The LLM returns Python code. We:
1. Extract the Python code from the response
2. Execute it in a sandboxed namespace with only the required imports
3. Find the scraper class(es) in the namespace
4. Call `scrape()` on each
5. Collect the `RawEvent` list

### `app/api/generate.py` — Update endpoint

Same API contract (`POST /api/cities/generate`), but internally calls the new code-generation flow.

### Frontend — No changes needed

The frontend already works — same input, same output (events).

## Acceptance Criteria

- [x] LLM prompt includes BaseScraper interface + RawEvent model + sample scraper as template
- [x] LLM generates valid Python code that implements BaseScraper for the requested city
- [x] Generated code is dynamically executed in a restricted namespace
- [x] Generated scraper's `scrape()` method returns `RawEvent` objects
- [x] Events flow through existing dedup → rank → persist pipeline
- [x] Existing frontend works without changes
- [x] Error handling: malformed code, execution errors, timeout
- [x] Generated scraper code is saved to `backend/app/scrapers/generated/` for inspection

## MVP Files

### backend/app/services/llm.py (rewrite)

```python
async def generate_scraper_for_city(city: str) -> list[RawEvent]:
    # 1. Build prompt with BaseScraper + RawEvent + sample scraper
    # 2. Call Copilot Proxy LLM
    # 3. Extract Python code from response
    # 4. exec() in restricted namespace
    # 5. Find BaseScraper subclass, instantiate, call scrape()
    # 6. Return list[RawEvent]
```

### backend/app/scrapers/generated/ (new directory)

Stores generated scraper .py files for debugging/inspection.

## Sources

- **Origin brainstorm:** docs/brainstorms/2026-03-12-copilot-extension-scraper-generator-brainstorm.md
- **Copilot Proxy:** localhost:8080 (model: claude-sonnet-4)
- **Template scrapers:** backend/app/scrapers/dc.py, backend/app/scrapers/base.py
