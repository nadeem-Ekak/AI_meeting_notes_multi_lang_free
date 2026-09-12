"""Unit tests for language detection, script detection, switches, confidence."""
from __future__ import annotations

from types import SimpleNamespace

from app.stt.language import (
    CODE_SWITCH_NAMES,
    detect_language_switches,
    detect_meeting_language,
    detect_script,
    detect_speaker_language,
    is_low_confidence,
    language_label,
)


def seg(language=None, speaker="SPEAKER_00", **kwargs):
    return SimpleNamespace(language=language, speaker=speaker, **kwargs)


# ---------- Script detection (RQ-55) ----------
def test_detect_script_devanagari():
    assert detect_script("हमें इसे कल तक पूरा करना है।") == "Devanagari"


def test_detect_script_latin():
    assert detect_script("We need to finish this by tomorrow.") == "Latin"


def test_detect_script_mixed_devanagari_latin():
    assert detect_script("हमें API को कल तक deploy करना है।") == "Mixed"


def test_detect_script_bengali():
    assert detect_script("আগে staging test করতে হবে") == "Mixed"


def test_detect_script_tamil():
    assert detect_script("இன்று deploy செய்யலாம்") == "Mixed"


# ---------- Language labels (RQ-52/53) ----------
def test_language_label_hinglish():
    assert language_label("hi,en") == "Hinglish"


def test_language_label_single():
    assert language_label("hi") == "Hindi"
    assert language_label("bn") == "Bengali"


# ---------- Meeting language aggregation (RQ-53) ----------
def test_detect_meeting_language_mixed():
    segments = [seg("hi"), seg("en"), seg("hi")]
    assert detect_meeting_language(segments) == "en,hi"


def test_detect_meeting_language_single():
    assert detect_meeting_language([seg("en"), seg("en")]) == "en"


def test_detect_meeting_language_empty():
    assert detect_meeting_language([]) is None


# ---------- Speaker language (RQ-53) ----------
def test_detect_speaker_language():
    segments = [
        seg("hi", speaker="A"),
        seg("hi", speaker="A"),
        seg("en", speaker="B"),
    ]
    result = detect_speaker_language(segments)
    assert result["A"] == "hi"
    assert result["B"] == "en"


# ---------- Language switches (RQ-54) ----------
def test_detect_language_switches():
    segments = [seg("hi"), seg("hi"), seg("en"), seg("en")]
    switches = detect_language_switches(segments)
    assert len(switches) == 1
    assert switches[0]["at_segment"] == 2
    assert switches[0]["from_lang"] == "hi"
    assert switches[0]["to_lang"] == "en"


def test_detect_no_switches_for_single_language():
    assert detect_language_switches([seg("hi"), seg("hi")]) == []


# ---------- Confidence (RQ-63) ----------
def test_is_low_confidence_low_language_probability():
    assert is_low_confidence(seg(language_probability=0.4))


def test_is_low_confidence_low_avg_logprob():
    assert is_low_confidence(seg(language_probability=0.9, avg_logprob=-2.0))


def test_is_low_confidence_high_no_speech():
    assert is_low_confidence(seg(language_probability=0.9, no_speech_prob=0.8))


def test_not_low_confidence():
    assert not is_low_confidence(
        seg(language_probability=0.9, avg_logprob=-0.5, no_speech_prob=0.1)
    )


def test_code_switch_names_registered():
    assert "hi,en" in CODE_SWITCH_NAMES
    assert "ta,en" in CODE_SWITCH_NAMES
