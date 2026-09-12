"""Unit tests for request/response schemas."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas import NotesRequest, TranscribeRequest


def test_transcribe_defaults():
    r = TranscribeRequest()
    assert r.language_mode == "auto"
    assert r.code_switching is True
    assert r.use_custom_vocabulary is True


def test_transcribe_manual_language():
    r = TranscribeRequest(language_mode="manual:hi")
    assert r.language_mode == "manual:hi"


def test_notes_request_valid_kinds():
    for kind in ("summary", "notes", "mom"):
        assert NotesRequest(kind=kind).kind == kind


def test_notes_request_invalid_kind():
    with pytest.raises(ValidationError):
        NotesRequest(kind="bad")
