from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.events import router as events_router
from app.api.generate import router as generate_router, format_city
from app.db import create_tables, SessionLocal
from app.models import EventRow

app = FastAPI(title="Discovery Event Platform", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(events_router, prefix="/api")
app.include_router(generate_router, prefix="/api")


@app.on_event("startup")
def startup():
    create_tables()
    _migrate_city_names()


def _migrate_city_names():
    """One-time fix: update plain city names to 'City / Country' format."""
    db = SessionLocal()
    try:
        rows = db.query(EventRow).all()
        updated = 0
        for row in rows:
            pretty = format_city(row.location)
            if pretty != row.location:
                row.location = pretty
                updated += 1
        if updated:
            db.commit()
            print(f"[startup] Migrated {updated} event locations to City / Country format")
    finally:
        db.close()
