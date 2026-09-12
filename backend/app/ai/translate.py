"""Optional translation (RQ-60): a separate operation from transcription & summary."""
from __future__ import annotations

from ..stt.language import SUPPORTED_LANGUAGES
from .providers import LLMClient


def _language_name(code: str) -> str:
    return SUPPORTED_LANGUAGES.get(code.lower(), code)


def translate_text(
    client: LLMClient, text: str, target_language: str = "en", source_language: str | None = None
) -> str:
    system = (
        "You are a professional translator. Translate the text accurately and "
        "completely. Do not summarize. Do not translate personal names or proper nouns."
    )
    source_hint = f" (source language: {_language_name(source_language)})" if source_language else ""
    user = (
        f"Translate the following text into {_language_name(target_language)}{source_hint}.\n\n"
        f"{text}"
    )
    return client.complete(system, user)
