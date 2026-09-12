"""Pydantic request/response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ---------- Meetings ----------
class MeetingCreate(BaseModel):
    title: str = "Untitled meeting"


class MeetingOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    status: str
    meeting_language: str | None = None

    model_config = {"from_attributes": True}


# ---------- Transcription ----------
class TranscribeRequest(BaseModel):
    language_mode: str = "auto"  # auto | manual:<code> | code-switching
    code_switching: bool = True
    use_custom_vocabulary: bool = True


class SegmentOut(BaseModel):
    id: int
    start: float
    end: float
    speaker: str | None = None
    text: str
    language: str | None = None
    language_label: str | None = None
    language_confidence: float | None = None
    script: str | None = None
    low_confidence: bool = False
    warning: str | None = None


class LanguageSwitch(BaseModel):
    at_segment: int
    from_lang: str
    to_lang: str


class TranscriptOut(BaseModel):
    meeting_id: int
    meeting_language: str | None = None
    segments: list[SegmentOut] = []
    language_switches: list[LanguageSwitch] = []


# ---------- Notes / Summary / MoM ----------
class NotesRequest(BaseModel):
    kind: Literal["summary", "notes", "mom"] = "summary"
    language: str = "same"


class NotesOut(BaseModel):
    id: int
    kind: str
    language: str | None = None
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Translation ----------
class TranslateRequest(BaseModel):
    target_language: str = "en"
    source: Literal["transcript", "summary"] = "transcript"


class TranslateOut(BaseModel):
    id: int
    target_language: str
    content: str


# ---------- Vocabulary ----------
class VocabularyCreate(BaseModel):
    term: str
    language: str | None = None
    script: str | None = None
    category: Literal["technical", "project", "person"] = "technical"


class VocabularyOut(BaseModel):
    id: int
    term: str
    language: str | None = None
    script: str | None = None
    category: str

    model_config = {"from_attributes": True}


# ---------- Settings ----------
class LLMProviderOut(BaseModel):
    name: str
    base_url: str
    api_key: str | None = None
    model: str


class SettingsOut(BaseModel):
    language_mode: str
    code_switching: bool
    lang_prob_threshold: float
    avg_logprob_threshold: float
    no_speech_threshold: float
    llm_default_provider: str
    llm_providers: list[LLMProviderOut] = []


class SettingsUpdate(BaseModel):
    language_mode: str | None = None
    code_switching: bool | None = None
    llm_default_provider: str | None = None
    llm_providers: list[LLMProviderOut] | None = None


# ---------- Evaluation ----------
class EvaluateRequest(BaseModel):
    reference: str
    hypothesis: str
    language: str | None = None


class EvaluateOut(BaseModel):
    wer: float
    cer: float
    language: str | None = None


class SegmentCreate(BaseModel):
    """Internal payload for the transcription service (also reused by fakes)."""

    start: float
    end: float
    text: str
    language: str | None = None
    language_confidence: float | None = None
    avg_logprob: float | None = None
    no_speech_prob: float | None = None
