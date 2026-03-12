from __future__ import annotations

import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


class EventRow(Base):
    """SQLAlchemy model for persisted events."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    venue = Column(String, nullable=True)
    location = Column(String, default="Montreal")
    category = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    source = Column(String, nullable=False)
    source_url = Column(String, nullable=True)
    source_count = Column(Integer, default=1)
    score = Column(Float, default=0.0)
    emoji = Column(String, nullable=True)
    color_tag = Column(String, nullable=True)
    vibe = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# --- Pydantic schemas ---


class RawEvent(BaseModel):
    """Event as scraped from a single source (before dedup)."""

    title: str
    date: datetime.datetime
    venue: Optional[str] = None
    location: str = "Montreal"
    category: Optional[str] = None
    description: Optional[str] = None
    source: str
    source_url: Optional[str] = None


class EventOut(BaseModel):
    """Event returned by the API."""

    id: int
    title: str
    date: datetime.datetime
    venue: Optional[str]
    location: str
    category: Optional[str]
    description: Optional[str]
    source: str
    source_url: Optional[str]
    source_count: int
    score: float
    emoji: Optional[str] = None
    color_tag: Optional[str] = None
    vibe: Optional[str] = None

    model_config = {"from_attributes": True}
