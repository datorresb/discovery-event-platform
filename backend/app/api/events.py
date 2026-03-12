from __future__ import annotations

import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import EventOut, EventRow

router = APIRouter()


@router.get("/events", response_model=list[EventOut])
def list_events(
    category: Optional[str] = Query(None, description="Filter by category"),
    location: Optional[str] = Query(None, description="Filter by city/location"),
    date_from: Optional[datetime.date] = Query(None, description="Events on or after this date"),
    date_to: Optional[datetime.date] = Query(None, description="Events on or before this date"),
    sort: str = Query("score", description="Sort by: score, date"),
    db: Session = Depends(get_db),
):
    q = db.query(EventRow)

    if category:
        q = q.filter(EventRow.category == category)
    if location:
        q = q.filter(EventRow.location == location)
    if date_from:
        q = q.filter(EventRow.date >= datetime.datetime.combine(date_from, datetime.time.min))
    if date_to:
        q = q.filter(EventRow.date <= datetime.datetime.combine(date_to, datetime.time.max))

    if sort == "date":
        q = q.order_by(EventRow.date)
    else:
        q = q.order_by(desc(EventRow.score), EventRow.date)

    return q.all()


@router.get("/events/top", response_model=list[EventOut])
def top_events(
    limit: int = Query(5, ge=1, le=20),
    location: Optional[str] = Query(None, description="Filter by city/location"),
    db: Session = Depends(get_db),
):
    """Top-ranked events this week."""
    today = datetime.date.today()
    week_end = today + datetime.timedelta(days=7)

    q = (
        db.query(EventRow)
        .filter(EventRow.date >= datetime.datetime.combine(today, datetime.time.min))
        .filter(EventRow.date <= datetime.datetime.combine(week_end, datetime.time.max))
    )
    if location:
        q = q.filter(EventRow.location == location)

    return q.order_by(desc(EventRow.score), EventRow.date).limit(limit).all()
