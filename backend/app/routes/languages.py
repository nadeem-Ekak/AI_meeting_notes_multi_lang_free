"""Supported languages endpoint (RQ-51/64)."""
from __future__ import annotations

from fastapi import APIRouter

from ..config import settings
from ..stt.language import CODE_SWITCH_NAMES, SUPPORTED_LANGUAGES

router = APIRouter(prefix="/languages", tags=["languages"])


@router.get("")
def list_languages() -> dict:
    languages = [{"code": code, "name": name} for code, name in SUPPORTED_LANGUAGES.items()]
    # Code-switching variants (RQ-52).
    for code, name in CODE_SWITCH_NAMES.items():
        languages.append({"code": code, "name": name})
    languages.sort(key=lambda x: x["code"])
    return {
        "languages": languages,
        "default_mode": "auto",
        "code_switching_default": True,
    }
