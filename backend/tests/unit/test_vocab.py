"""Unit tests for custom vocabulary & names (RQ-57/58)."""
from __future__ import annotations

from types import SimpleNamespace

from app.stt.vocab import apply_vocab, build_hotwords, build_initial_prompt


def entry(term, language=None):
    return SimpleNamespace(term=term, language=language)


def test_build_initial_prompt_includes_terms():
    prompt = build_initial_prompt([entry("Argus"), entry("Pika")])
    assert "Argus" in prompt
    assert "Pika" in prompt


def test_build_initial_prompt_empty():
    assert build_initial_prompt([]) == ""


def test_build_hotwords_language_filter():
    entries = [entry("Argus", "en"), entry("कर्मचारी", "hi")]
    assert build_hotwords(entries, "hi") == ["कर्मचारी"]
    assert build_hotwords(entries, "en") == ["Argus"]


def test_build_hotwords_global_terms_always_included():
    entries = [entry("SCRFD"), entry("Argus", "en")]
    assert build_hotwords(entries, "hi") == ["SCRFD"]


def test_apply_vocab_latin_case_insensitive():
    entries = [entry("Argus"), entry("Pika")]
    assert apply_vocab("we use argus and pika here", entries) == "we use Argus and Pika here"


def test_apply_vocab_native_script_exact():
    entries = [entry("कर्मचारी", "hi")]
    assert apply_vocab("हम कर्मचारी को बुलाएं", entries) == "हम कर्मचारी को बुलाएं"


def test_apply_vocab_does_not_translate():
    entries = [entry("Nadeem")]
    text = "Nadeem will present"
    assert apply_vocab(text, entries) == text
