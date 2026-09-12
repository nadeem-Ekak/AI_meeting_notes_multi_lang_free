"""Settings endpoints: language defaults, thresholds, LLM providers (RQ-64)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..ai.providers import get_default_provider_name, load_providers
from ..config import settings
from ..db import get_db
from ..models import Setting
from ..schemas import LLMProviderOut, SettingsOut, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


def _stored(db: Session, key: str, field: str):
    row = db.query(Setting).filter(Setting.key == key).first()
    if row and isinstance(row.value, dict) and field in row.value:
        return row.value[field]
    return None


def _upsert(db: Session, key: str, value: dict) -> None:
    row = db.query(Setting).filter(Setting.key == key).first()
    if row is None:
        db.add(Setting(key=key, value=value))
    else:
        row.value = value


def _build_settings(db: Session) -> SettingsOut:
    language_mode = _stored(db, "language_mode", "value") or settings.language_mode
    code_switching = _stored(db, "code_switching", "value")
    if code_switching is None:
        code_switching = settings.code_switching
    providers = load_providers(db)
    return SettingsOut(
        language_mode=language_mode,
        code_switching=bool(code_switching),
        lang_prob_threshold=settings.lang_prob_threshold,
        avg_logprob_threshold=settings.avg_logprob_threshold,
        no_speech_threshold=settings.no_speech_threshold,
        llm_default_provider=get_default_provider_name(db),
        llm_providers=[
            LLMProviderOut(
                name=p.name, base_url=p.base_url, api_key=p.api_key, model=p.model
            )
            for p in providers
        ],
    )


@router.get("", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db)) -> SettingsOut:
    return _build_settings(db)


@router.put("", response_model=SettingsOut)
def update_settings(
    payload: SettingsUpdate, db: Session = Depends(get_db)
) -> SettingsOut:
    if payload.language_mode is not None:
        _upsert(db, "language_mode", {"value": payload.language_mode})
    if payload.code_switching is not None:
        _upsert(db, "code_switching", {"value": payload.code_switching})
    if payload.llm_default_provider is not None:
        _upsert(db, "llm_default_provider", {"value": payload.llm_default_provider})
    if payload.llm_providers is not None:
        _upsert(
            db,
            "llm_providers",
            {"items": [p.model_dump() for p in payload.llm_providers]},
        )
    db.commit()
    return _build_settings(db)
