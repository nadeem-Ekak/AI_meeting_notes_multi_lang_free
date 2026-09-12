"""SQLAlchemy models.

Stores language metadata per RQ-65:
    meeting_language, segment_language, speaker_language, language_confidence.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), default="Untitled meeting")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(32), default="created")  # created|transcribed
    meeting_language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    audio_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    segments: Mapped[list["Segment"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )
    speakers: Mapped[list["Speaker"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )
    notes: Mapped[list["Note"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )


class Speaker(Base):
    __tablename__ = "speakers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id"), index=True)
    label: Mapped[str] = mapped_column(String(64))
    dominant_language: Mapped[str | None] = mapped_column(String(64), nullable=True)

    meeting: Mapped["Meeting"] = relationship(back_populates="speakers")


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id"), index=True)
    speaker_id: Mapped[int | None] = mapped_column(ForeignKey("speakers.id"), nullable=True)
    start: Mapped[float] = mapped_column(Float)
    end: Mapped[float] = mapped_column(Float)
    text: Mapped[str] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    language_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    script: Mapped[str | None] = mapped_column(String(32), nullable=True)
    avg_logprob: Mapped[float | None] = mapped_column(Float, nullable=True)
    no_speech_prob: Mapped[float | None] = mapped_column(Float, nullable=True)
    low_confidence: Mapped[bool] = mapped_column(Boolean, default=False)

    meeting: Mapped["Meeting"] = relationship(back_populates="segments")


class Vocabulary(Base):
    __tablename__ = "vocabulary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    term: Mapped[str] = mapped_column(String(255))
    language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    script: Mapped[str | None] = mapped_column(String(32), nullable=True)
    category: Mapped[str] = mapped_column(String(32), default="technical")  # technical|project|person


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32))  # summary|notes|mom|translation
    language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    meeting: Mapped["Meeting"] = relationship(back_populates="notes")


class Setting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)
