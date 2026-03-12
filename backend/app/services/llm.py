"""LLM service — generates Python scraper code via Copilot Proxy, then executes it."""

from __future__ import annotations

import datetime
import inspect
import json
import os
import re
import textwrap
from pathlib import Path

import httpx

from app.models import RawEvent
from app.scrapers.base import BaseScraper

COPILOT_PROXY_URL = "http://localhost:8080/v1/chat/completions"
MODEL = "claude-sonnet-4"
GENERATED_DIR = Path(__file__).resolve().parent.parent / "scrapers" / "generated"

# Allowed modules for generated scraper code
_ALLOWED_MODULES = {
    "datetime", "re", "json", "typing", "abc", "dataclasses",
    "time", "math", "random", "string", "collections",
    # HTTP + parsing for real scraping
    "httpx", "bs4", "dateutil", "logging",
}


def _safe_import(name, *args, **kwargs):
    """Only allow importing safe modules in generated code."""
    if name in _ALLOWED_MODULES:
        return __import__(name, *args, **kwargs)
    raise ImportError(f"Import of '{name}' is not allowed in generated scrapers")


def _read_template_files() -> str:
    """Read the BaseScraper interface, RawEvent model, and a real scraper example to include in the prompt."""
    base_path = Path(__file__).resolve().parent.parent / "scrapers" / "base.py"
    models_path = Path(__file__).resolve().parent.parent / "models.py"
    sample_path = Path(__file__).resolve().parent.parent / "scrapers" / "eventbrite_mtl.py"

    base_code = base_path.read_text()
    # Only include the RawEvent class from models
    models_code = models_path.read_text()
    raw_event_match = re.search(r"(class RawEvent\(BaseModel\):.*?)(?=\n\nclass |\Z)", models_code, re.DOTALL)
    raw_event_code = raw_event_match.group(1) if raw_event_match else "# RawEvent not found"

    # Use the real Eventbrite scraper as the example
    sample_code = sample_path.read_text()
    # Take just the class definition
    first_class = re.search(r"(class \w+\(BaseScraper\):.*?)(?=\n\nclass |\Z)", sample_code, re.DOTALL)
    sample_snippet = first_class.group(1) if first_class else sample_code[:2000]

    return f"""## BaseScraper Interface (base.py):
```python
{base_code}
```

## RawEvent Model:
```python
{raw_event_code}
```

## Example REAL Scraper (scrapes Eventbrite Montreal via JSON-LD):
```python
{sample_snippet}
```"""


def _build_prompt(city: str) -> str:
    templates = _read_template_files()
    today = datetime.date.today().isoformat()

    return f"""You are a Python code generator. Generate a complete Python scraper module for events in **{city}**.

{templates}

## Your Task

Write a Python module with 2-3 scraper classes for {city}. Each class must:
1. Inherit from `BaseScraper`
2. Implement `source_name()` returning a unique string
3. Implement `scrape()` returning a `list[RawEvent]` with REAL scraped data

## CRITICAL — REAL SCRAPING REQUIRED

Each scraper class MUST make real HTTP requests to actual event listing websites for {city}.
You have access to these libraries:
- `httpx` — for HTTP GET requests (use `httpx.get(url, timeout=15, headers=HEADERS, follow_redirects=True)`)
- `bs4` (BeautifulSoup) — for HTML parsing (use `BeautifulSoup(resp.text, "html.parser")`)
- `json` — for parsing JSON-LD or API responses
- `dateutil.parser.parse` — for flexible date parsing (use `from dateutil.parser import parse as parse_date`)
- `re`, `datetime`, `logging`

### Scraping strategy (pick for each class):
1. **JSON-LD scraping**: Find `<script type="application/ld+json">` in HTML, parse it for Event objects
2. **Public API**: If the city has a public events API (e.g. open data portals), use it directly
3. **HTML scraping**: Parse event cards/listings from the page structure using BeautifulSoup

### Requirements:
- Use `from app.models import RawEvent` and `from app.scrapers.base import BaseScraper`
- Import `datetime`, `json`, `logging`, `httpx`, and `from bs4 import BeautifulSoup`
- Add `from dateutil.parser import parse as parse_date`
- Set `location="{city}"` on all events
- ALWAYS wrap HTTP calls in try/except and return `[]` on failure
- Use a proper User-Agent header  
- Use `timeout=15` on all HTTP requests
- Categories must be one of: music, culture, food, nightlife, community
- Truncate descriptions to 500 chars: `description[:500]`

### Target real websites for {city}:
- Eventbrite search page for that city (has JSON-LD)
- AllEvents.in page for that city (has JSON-LD)  
- The city's official events/tourism page
- Local venue websites

DO NOT return hardcoded/demo data. Every event must come from a real HTTP request.

Return ONLY the Python code. No markdown fences. No explanation. Just the code."""


def _extract_python_code(content: str) -> str:
    """Extract Python code from LLM response, stripping markdown fences if present."""
    content = content.strip()
    # Try to extract from code fences
    match = re.search(r"```(?:python)?\s*\n(.*?)```", content, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Strip bare "python" word if it's the first line (LLM artifact)
    lines = content.split("\n")
    if lines and lines[0].strip().lower() == "python":
        content = "\n".join(lines[1:])
    return content.strip()


def _execute_scraper_code(code: str, city: str) -> list[RawEvent]:
    """Execute generated scraper code and run all BaseScraper subclasses found."""
    # Strip `from __future__ import annotations` — not compatible with exec()
    code = re.sub(r"^from __future__ import annotations\s*\n?", "", code, flags=re.MULTILINE)
    # Strip import lines for modules we provide in the namespace
    code = re.sub(r"^from app\.models import.*\n?", "", code, flags=re.MULTILINE)
    code = re.sub(r"^from app\.scrapers\.base import.*\n?", "", code, flags=re.MULTILINE)
    code = re.sub(r"^import datetime\s*\n?", "", code, flags=re.MULTILINE)
    code = re.sub(r"^import httpx\s*\n?", "", code, flags=re.MULTILINE)
    code = re.sub(r"^import json\s*\n?", "", code, flags=re.MULTILINE)
    code = re.sub(r"^import logging\s*\n?", "", code, flags=re.MULTILINE)
    code = re.sub(r"^import re\s*\n?", "", code, flags=re.MULTILINE)
    code = re.sub(r"^from bs4 import.*\n?", "", code, flags=re.MULTILINE)
    code = re.sub(r"^from dateutil\.parser import.*\n?", "", code, flags=re.MULTILINE)

    # Create a namespace with available imports
    # We provide safe builtins — removing only file/system access
    import builtins
    import logging as logging_mod

    from bs4 import BeautifulSoup
    from dateutil.parser import parse as parse_date

    safe_builtins = {k: v for k, v in vars(builtins).items()
                     if k not in ("open", "exec", "eval", "compile", "input", "__import__")}
    safe_builtins["__import__"] = _safe_import

    namespace: dict = {
        "__builtins__": safe_builtins,
        "datetime": datetime,
        "json": json,
        "re": re,
        "logging": logging_mod,
        "httpx": httpx,
        "BeautifulSoup": BeautifulSoup,
        "parse_date": parse_date,
        "RawEvent": RawEvent,
        "BaseScraper": BaseScraper,
    }

    # Execute the generated code
    exec(code, namespace)

    # Find all BaseScraper subclasses in the namespace
    scrapers = []
    for name, obj in namespace.items():
        if (
            inspect.isclass(obj)
            and issubclass(obj, BaseScraper)
            and obj is not BaseScraper
        ):
            scrapers.append(obj())

    if not scrapers:
        raise ValueError("No BaseScraper subclasses found in generated code")

    # Run all scrapers and collect events
    all_events: list[RawEvent] = []
    for scraper in scrapers:
        events = scraper.scrape()
        all_events.extend(events)

    return all_events


async def generate_scraper_for_city(city: str) -> tuple[list[RawEvent], str]:
    """Generate scraper code for a city, execute it, and return events + code.

    Returns:
        Tuple of (list of RawEvent, generated Python code string)
    """
    prompt = _build_prompt(city)

    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(
            COPILOT_PROXY_URL,
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4096,
            },
        )
        resp.raise_for_status()

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    code = _extract_python_code(content)

    # Save the generated code for inspection
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^a-z0-9_]", "_", city.lower().strip())
    code_path = GENERATED_DIR / f"{safe_name}.py"
    code_path.write_text(code)

    # Execute the generated code
    events = _execute_scraper_code(code, city)

    return events, code


# Keep the old function name as alias for backwards compatibility
async def generate_events_for_city(city: str) -> list[RawEvent]:
    """Backward-compatible wrapper — generates scraper code and returns events."""
    events, _code = await generate_scraper_for_city(city)
    return events
