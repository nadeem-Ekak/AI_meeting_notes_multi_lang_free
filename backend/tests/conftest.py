"""Shared test fixtures.

Tests run entirely offline: a mock STT engine and a fake LLM are injected, and the
database is an in-memory SQLite (single shared connection via StaticPool).
"""
from __future__ import annotations

import os
import tempfile

# Set before importing app modules so config reads test-safe values.
os.environ.setdefault("UPLOAD_DIR", os.path.join(tempfile.gettempdir(), "mt_test_uploads"))
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_meeting_notes.db")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import create_app
from app.stt.engine import MockTranscriptionEngine, STTSegment


@pytest.fixture
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def fake_stt() -> MockTranscriptionEngine:
    return MockTranscriptionEngine()


@pytest.fixture
def client(test_engine, fake_stt, monkeypatch):
    session_factory = sessionmaker(bind=test_engine)
    app = create_app(engine=fake_stt, init_on_startup=False)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    from app.ai import providers

    class FakeClient:
        def __init__(self, provider):
            self.provider = provider

        def complete(self, system, user, temperature=0.3):
            return "FAKE_RESPONSE"

    monkeypatch.setattr(
        providers,
        "get_llm_client",
        lambda db: FakeClient(providers.LLMProvider("fake", "", None, "fake-model")),
    )

    with TestClient(app) as c:
        yield c


@pytest.fixture
def create_meeting(client) -> int:
    meeting = client.post("/api/meetings", json={"title": "Test meeting"}).json()
    return meeting["id"]


@pytest.fixture
def upload_and_transcribe(client, fake_stt, create_meeting):
    """Upload fake audio and run the pipeline, returning the meeting id."""

    def _run(segments: list[STTSegment]) -> int:
        fake_stt.segments = list(segments)
        meeting_id = create_meeting
        client.post(
            f"/api/meetings/{meeting_id}/upload",
            files={"file": ("audio.wav", b"fake-audio-bytes", "audio/wav")},
        )
        client.post(f"/api/meetings/{meeting_id}/transcribe", json={})
        return meeting_id

    return _run
