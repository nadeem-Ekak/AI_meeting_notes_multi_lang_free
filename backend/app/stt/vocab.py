"""Custom vocabulary and names (RQ-57, RQ-58).

Terms are injected into the STT pipeline (initial prompt / hot-words) and applied as
a safe post-processing dictionary. Names are never translated.
"""
from __future__ import annotations

import re
from typing import Iterable


def _term_of(entry: object) -> str | None:
    if isinstance(entry, str):
        return entry
    term = getattr(entry, "term", None)
    return term if isinstance(term, str) and term.strip() else None


def _language_of(entry: object) -> str | None:
    if isinstance(entry, str):
        return None
    lang = getattr(entry, "language", None)
    return lang or None


def _filtered_terms(entries: Iterable[object], language: str | None) -> list[str]:
    """Terms applicable to the given language (None language = applies to all)."""
    terms: list[str] = []
    for entry in entries:
        term = _term_of(entry)
        if not term:
            continue
        lang = _language_of(entry)
        if lang is None or language is None or lang == language:
            if term not in terms:
                terms.append(term)
    return terms


def build_initial_prompt(entries: Iterable[object], language: str | None = None) -> str:
    terms = _filtered_terms(entries, language)
    if not terms:
        return ""
    return "Technical terms and names: " + ", ".join(terms) + "."


def build_hotwords(entries: Iterable[object], language: str | None = None) -> list[str]:
    return _filtered_terms(entries, language)


_LATIN_WORD_RE = re.compile(r"[A-Za-z]")


def apply_vocab(text: str, entries: Iterable[object]) -> str:
    """Safe post-processing: correct known terms; never translates or invents words."""
    result = text
    for entry in entries:
        term = _term_of(entry)
        if not term:
            continue
        if _LATIN_WORD_RE.search(term):
            # Case-insensitive whole-word replacement (preserves recognized casing).
            result = re.sub(
                rf"\b{re.escape(term)}\b", term, result, flags=re.IGNORECASE
            )
        else:
            # Native-script exact replacement.
            result = result.replace(term, term)
    return result
