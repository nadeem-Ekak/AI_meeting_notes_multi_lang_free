"""Language detection, script detection, switch detection, confidence.

Pure functions over transcript segments — no external dependencies, fully unit-testable.

Key rule (RQ-56): language is taken from the acoustic LID signal; `script` is computed
from the text. Latin-script text may therefore be labeled Hindi/Hinglish.
"""
from __future__ import annotations

import re

SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "ur": "Urdu",
    "bn": "Bengali",
    "gu": "Gujarati",
    "mr": "Marathi",
    "pa": "Punjabi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "or": "Odia",
    "as": "Assamese",
    "ne": "Nepali",
}

CODE_SWITCH_NAMES: dict[str, str] = {
    "hi,en": "Hinglish",
    "gu,en": "Gujarati+English",
    "ta,en": "Tamil+English",
    "te,en": "Telugu+English",
    "bn,en": "Bengali+English",
    "mr,en": "Marathi+English",
    "pa,en": "Punjabi+English",
}

# Unicode blocks for Indic scripts + Arabic (Urdu) + Latin.
_SCRIPT_RANGES: dict[str, tuple[int, int]] = {
    "Devanagari": (0x0900, 0x097F),
    "Bengali": (0x0980, 0x09FF),
    "Gurmukhi": (0x0A00, 0x0A7F),   # Punjabi
    "Gujarati": (0x0A80, 0x0AFF),
    "Odia": (0x0B00, 0x0B7F),
    "Tamil": (0x0B80, 0x0BFF),
    "Telugu": (0x0C00, 0x0C7F),
    "Kannada": (0x0C80, 0x0CFF),
    "Malayalam": (0x0D00, 0x0D7F),
    "Arabic": (0x0600, 0x06FF),
    "ArabicExt": (0x0750, 0x077F),
}

_LATIN_RE = re.compile(r"[A-Za-z]")


def detect_script(text: str) -> str:
    """Return the script(s) used by the text (e.g. 'Devanagari', 'Latin', 'Mixed')."""
    scripts: set[str] = set()
    if _LATIN_RE.search(text):
        scripts.add("Latin")
    for name, (lo, hi) in _SCRIPT_RANGES.items():
        if any(lo <= ord(ch) <= hi for ch in text):
            scripts.add("Arabic" if name == "ArabicExt" else name)
    if not scripts:
        return "Unknown"
    if len(scripts) == 1:
        return next(iter(scripts))
    return "Mixed"


def _normalize_code(code: str | None) -> str | None:
    if not code:
        return None
    code = code.strip().lower()
    return code or None


def split_codes(code: str | None) -> list[str]:
    """Split a possibly-comma-joined language code into individual codes."""
    code = _normalize_code(code)
    if not code:
        return []
    return [c.strip() for c in code.split(",") if c.strip()]


def language_label(code: str | None) -> str | None:
    """Human-readable label. 'hi,en' -> 'Hinglish'; 'hi' -> 'Hindi'."""
    code = _normalize_code(code)
    if not code:
        return None
    if code in CODE_SWITCH_NAMES:
        return CODE_SWITCH_NAMES[code]
    parts = split_codes(code)
    if len(parts) > 1:
        return "+".join(SUPPORTED_LANGUAGES.get(p, p) for p in parts)
    return SUPPORTED_LANGUAGES.get(parts[0], parts[0])


def _seg_language(segment: object) -> str | None:
    return _normalize_code(getattr(segment, "language", None))


def detect_meeting_language(segments: list[object]) -> str | None:
    """Aggregate distinct segment languages into a sorted comma-joined code."""
    codes: list[str] = []
    for seg in segments:
        for code in split_codes(_seg_language(seg)):
            if code not in codes:
                codes.append(code)
    if not codes:
        return None
    return ",".join(sorted(codes))


def detect_speaker_language(segments: list[object]) -> dict[str, str]:
    """Dominant (most frequent) language code per speaker label."""
    counts: dict[str, dict[str, int]] = {}
    for seg in segments:
        speaker = getattr(seg, "speaker", None) or getattr(seg, "speaker_label", None)
        code = _seg_language(seg)
        if speaker is None or code is None:
            continue
        counts.setdefault(speaker, {})
        counts[speaker][code] = counts[speaker].get(code, 0) + 1
    result: dict[str, str] = {}
    for speaker, lang_counts in counts.items():
        result[speaker] = max(lang_counts, key=lang_counts.get)  # type: ignore[arg-type]
    return result


def detect_language_switches(segments: list[object]) -> list[dict]:
    """Detect adjacent language-set changes. Never labels the whole meeting one code."""
    switches: list[dict] = []
    prev: set[str] | None = None
    prev_index: int = 0
    for idx, seg in enumerate(segments):
        current = set(split_codes(_seg_language(seg)))
        if not current:
            continue
        if prev is not None and current != prev:
            switches.append(
                {
                    "at_segment": idx,
                    "from_lang": ",".join(sorted(prev)),
                    "to_lang": ",".join(sorted(current)),
                }
            )
        prev = current
        prev_index = idx
    return switches


def is_low_confidence(
    segment: object,
    lang_prob_threshold: float = 0.60,
    avg_logprob_threshold: float = -1.0,
    no_speech_threshold: float = 0.60,
) -> bool:
    """RQ-63: flag low-confidence segments without inventing content."""
    lang_prob = getattr(segment, "language_probability", None)
    if lang_prob is None:
        lang_prob = getattr(segment, "language_confidence", None)
    avg_logprob = getattr(segment, "avg_logprob", None)
    no_speech_prob = getattr(segment, "no_speech_prob", None)

    if lang_prob is not None and float(lang_prob) < lang_prob_threshold:
        return True
    if avg_logprob is not None and float(avg_logprob) < avg_logprob_threshold:
        return True
    if no_speech_prob is not None and float(no_speech_prob) > no_speech_threshold:
        return True
    return False
