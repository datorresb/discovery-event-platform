---
date: 2026-03-12
topic: copilot-extension-scraper-generator
---

# Copilot Extension: City Scraper Generator

## What We're Building

A **GitHub Copilot Extension** (server-side GitHub App) that helps developers add new city scrapers to the Discovery Event Platform. When a developer types `@events add city Tokyo` in Copilot Chat, the extension generates a complete Python scraper file following the existing `BaseScraper` interface, with realistic event sources for that city.

This eliminates the manual work of researching event sources per city and writing boilerplate scraper code — the AI does it.

## Why This Approach

- **Scales the platform** — adding a new city goes from hours of research + coding to a single chat command
- **Stays in the developer workflow** — no context switching, works right in VS Code
- **Leverages existing patterns** — generated code follows the `BaseScraper` interface, so it's consistent and pluggable
- **GitHub App webhook model** gives full control over conversation flow and code generation
- Alternative approaches (Skillset, VS Code participant) were considered but offer less conversational control

## Key Decisions

- **Extension type:** Server-side GitHub App with webhook (hosted on existing FastAPI backend)
- **LLM for code generation:** Use an LLM to generate scraper code based on the city name + existing `BaseScraper` template
- **Output format:** Generated Python file returned in Copilot Chat, ready to save to `backend/app/scrapers/`
- **Scope:** Scraper code generation only (not live event lookup — that's a future enhancement)
- **Template-driven:** The extension reads the existing `BaseScraper` interface and a sample scraper to maintain code consistency

## Open Questions

_(All resolved — see Resolved Questions below)_

## Resolved Questions

- **LLM provider:** Use GitHub account as proxy (GitHub Models via Copilot token) — no separate API key needed
- **Output behavior:** Auto-save the generated scraper file to `backend/app/scrapers/` AND update `pipeline/runner.py` to register the new scraper — full automation
- **API key management:** Not needed — the Copilot token from the GitHub App webhook provides model access
- **Auto-register scraper:** Yes — the extension should update the pipeline runner to include the new scraper

## Next Steps

→ `/ce-plan` for implementation details
